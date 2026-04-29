"""
==============================================================================
  SmartAgri · Mitra Unified Ledger (SQLite)
  ─────────────────────────────────────────
  The SINGLE SOURCE OF TRUTH for the entire SmartAgri platform.

  Every interaction is a timestamped row containing:
    ┌──────────────────────────────────────────────────────────┐
    │  1. Raw ESP32 sensor readings  (N, P, K, temp, hum …)   │
    │  2. Crop Detection model  I/O                            │
    │  3. Fertilizer Optimization model  I/O  (9 targets)      │
    │  4. Vision API output  (disease + soil)                   │
    │  5. LLM conversation  (user query + mitra response)      │
    │  6. User-specific metadata  (land_size, irrigated, etc.) │
    └──────────────────────────────────────────────────────────┘

  The AI (Mitra) has TWO database privileges:
    • ALWAYS:  append_new_row()  — every interaction writes a full row
    • RARELY:  update_user_meta() — ONLY when the user explicitly reveals
               a new fact (e.g. land size, soil type, irrigation method).
               This is gated by the LLM's JSON extraction.

  The store is designed for hourly auto-appends from background model runs,
  AND on-demand appends from chat interactions.
==============================================================================
"""

import os
import sqlite3
import json
import logging
from datetime import datetime, timezone
from typing import Optional

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

DB_PATH = os.path.join("data", "mitra_ledger.db")


class FarmDataStore:
    """
    Manages a local SQLite database that acts as the single source of truth
    for the SmartAgri platform.  Every model output, sensor reading,
    and user note gets persisted here.
    """

    # ── Full Schema ───────────────────────────────────────────────────────
    CREATE_LEDGER_SQL = """
    CREATE TABLE IF NOT EXISTS farm_ledger (
        id                      INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp               TEXT    NOT NULL,

        -- ═══ RAW ESP32 SENSOR READINGS ═══
        sensor_N                REAL,
        sensor_P                REAL,
        sensor_K                REAL,
        sensor_temperature      REAL,
        sensor_humidity         REAL,
        sensor_ph               REAL,
        sensor_rainfall         REAL,
        sensor_moisture         REAL,

        -- ═══ DERIVED FEATURES (model inputs) ═══
        feat_N_P_ratio          REAL,
        feat_N_K_ratio          REAL,
        feat_P_K_ratio          REAL,
        feat_THI                REAL,
        feat_water_availability REAL,
        feat_pH_stress          REAL,

        -- ═══ CROP DETECTION MODEL OUTPUT ═══
        recommended_crop        TEXT,
        crop_confidence         REAL,

        -- ═══ FERTILIZER OPTIMIZATION MODEL OUTPUT (up to 9 targets) ═══
        current_crop            TEXT,
        soil_type               TEXT,
        days_since_planting     INTEGER,
        deficit_N               REAL,
        deficit_P               REAL,
        deficit_K               REAL,
        soil_health_score       REAL,
        water_requirement_idx   REAL,
        ph_adjustment           REAL,
        temp_stress_score       REAL,
        fertilizer_urgency      REAL,
        planting_readiness      REAL,

        -- ═══ VISION API OUTPUT ═══
        disease_detected        TEXT,
        disease_confidence      REAL,
        soil_type_vision        TEXT,
        soil_type_confidence    REAL,
        image_analyzed          INTEGER DEFAULT 0,

        -- ═══ LLM / USER INTERACTION ═══
        user_query              TEXT,
        mitra_response          TEXT,
        user_notes              TEXT,

        -- ═══ USER METADATA (AI-writable only when user reveals) ═══
        land_size_acres         REAL,
        irrigation_type         TEXT,
        region                  TEXT,
        user_custom_notes       TEXT,

        -- ═══ ROW METADATA ═══
        interaction_source      TEXT DEFAULT 'mitra_chat',
        row_trigger             TEXT DEFAULT 'user_chat'
    );
    """

    # Separate table for persistent user profile that the AI updates
    # only when the user reveals NEW facts
    CREATE_PROFILE_SQL = """
    CREATE TABLE IF NOT EXISTS user_profile (
        key                     TEXT PRIMARY KEY,
        value                   TEXT,
        updated_at              TEXT,
        source                  TEXT DEFAULT 'ai_extracted'
    );
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        self._init_db()
        log.info("FarmDataStore ready  (db=%s)", self.db_path)

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(self.CREATE_LEDGER_SQL)
            conn.execute(self.CREATE_PROFILE_SQL)
            conn.commit()

    # ─────────────────────────────────────────────────────────────────────
    # READ — get the latest state for LLM context
    # ─────────────────────────────────────────────────────────────────────
    def get_latest_state(self, n: int = 1) -> list[dict]:
        """Returns the most recent `n` rows from the ledger as dicts."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM farm_ledger ORDER BY id DESC LIMIT ?", (n,)
            )
            rows = cursor.fetchall()
        if not rows:
            return []
        return [dict(row) for row in reversed(rows)]

    def get_column_values(self, column: str, n: int = 10) -> list:
        """Get last N values for a specific column — used for trend analysis."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                f"SELECT {column} FROM farm_ledger WHERE {column} IS NOT NULL "
                f"ORDER BY id DESC LIMIT ?", (n,)
            )
            return [row[0] for row in reversed(cursor.fetchall())]

    def get_user_profile(self) -> dict:
        """Returns all user profile key-value pairs."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM user_profile")
            rows = cursor.fetchall()
        return {row["key"]: row["value"] for row in rows}

    # ─────────────────────────────────────────────────────────────────────
    # WRITE — append a new timestamped row (EVERY interaction)
    # ─────────────────────────────────────────────────────────────────────
    def append_new_row(self, data: dict) -> int:
        """
        Appends a full row to the ledger. Called on EVERY interaction
        (user chat, hourly auto-update, or manual sensor push).
        """
        if "timestamp" not in data:
            data["timestamp"] = datetime.now(timezone.utc).isoformat(
                timespec="seconds"
            )

        columns, values = [], []
        for key, val in data.items():
            if key == "id":
                continue
            columns.append(key)
            if isinstance(val, (dict, list)):
                values.append(json.dumps(val))
            else:
                values.append(val)

        placeholders = ", ".join(["?"] * len(columns))
        col_str = ", ".join(columns)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                f"INSERT INTO farm_ledger ({col_str}) VALUES ({placeholders})",
                values,
            )
            conn.commit()
            row_id = cursor.lastrowid

        log.info("Ledger row #%d written  (ts=%s, trigger=%s)",
                 row_id, data["timestamp"], data.get("row_trigger", "?"))
        return row_id

    # ─────────────────────────────────────────────────────────────────────
    # WRITE — update user profile (AI-gated, ONLY for new user facts)
    # ─────────────────────────────────────────────────────────────────────
    def update_user_meta(self, key: str, value: str, source: str = "ai_extracted"):
        """
        Updates a single key in the user_profile table.
        This is the ONLY write path the AI uses to persist user-specific
        facts (land size, irrigation type, region, etc.).

        The AI is instructed to call this VERY RARELY — only when the user
        explicitly mentions a new fact not already stored.
        """
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO user_profile (key, value, updated_at, source)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(key) DO UPDATE SET
                       value=excluded.value,
                       updated_at=excluded.updated_at,
                       source=excluded.source""",
                (key, str(value), now, source),
            )
            conn.commit()
        log.info("User profile updated: %s = %s  (source=%s)", key, value, source)

    # ─────────────────────────────────────────────────────────────────────
    # UTILITY — format history for LLM prompt injection
    # ─────────────────────────────────────────────────────────────────────
    def format_history_for_llm(self, n: int = 5) -> str:
        """Compact text summary of the last n ledger entries for the LLM."""
        rows = self.get_latest_state(n)
        if not rows:
            return "No historical data available yet. This is the first interaction."

        lines = []
        for row in rows:
            ts = row.get("timestamp", "?")
            parts = [f"[{ts}]"]

            # Sensors
            sensors = {k: row.get(f"sensor_{k}") for k in
                       ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]}
            active = {k: v for k, v in sensors.items() if v is not None}
            if active:
                sensor_str = ", ".join(f"{k}={v}" for k, v in active.items())
                parts.append(f"  Sensors: {sensor_str}")

            # Crops
            if row.get("recommended_crop"):
                parts.append(f"  AI Recommended Crop: {row['recommended_crop']} "
                             f"(conf={row.get('crop_confidence', '?')})")
            if row.get("current_crop"):
                parts.append(f"  Current Crop: {row['current_crop']}")

            # Soil
            if row.get("soil_type") or row.get("soil_type_vision"):
                parts.append(f"  Soil Type: {row.get('soil_type_vision') or row.get('soil_type')}")

            # Health scores
            for label, key in [("Soil Health", "soil_health_score"),
                                ("Water Need", "water_requirement_idx"),
                                ("Fert Urgency", "fertilizer_urgency")]:
                if row.get(key) is not None:
                    parts.append(f"  {label}: {row[key]}/100")

            # Disease
            if row.get("disease_detected"):
                parts.append(f"  Disease: {row['disease_detected']} "
                             f"(conf={row.get('disease_confidence', '?')})")

            # Deficits
            deficits = []
            for nutrient in ["N", "P", "K"]:
                val = row.get(f"deficit_{nutrient}")
                if val is not None and val > 0.5:
                    deficits.append(f"{nutrient}={val:.1f}kg/ha")
            if deficits:
                parts.append(f"  Deficits: {', '.join(deficits)}")

            # User notes
            if row.get("user_notes"):
                parts.append(f"  User Note: {row['user_notes']}")
            if row.get("user_query"):
                parts.append(f"  User Asked: {row['user_query'][:80]}")

            lines.append("\n".join(parts))

        return "\n---\n".join(lines)

    def format_profile_for_llm(self) -> str:
        """Returns user profile as a text block for the LLM."""
        profile = self.get_user_profile()
        if not profile:
            return "No user profile data stored yet."
        lines = [f"  {k}: {v}" for k, v in profile.items()]
        return "\n".join(lines)

    def get_row_count(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM farm_ledger")
            return cursor.fetchone()[0]


# ─────────────────────────────────────────────────────────────────────────
# Quick smoke test
# ─────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    store = FarmDataStore()
    sample = {
        "sensor_N": 80.0, "sensor_P": 45.0, "sensor_K": 40.0,
        "sensor_temperature": 25.0, "sensor_humidity": 82.0,
        "sensor_ph": 6.5, "sensor_rainfall": 220.0,
        "recommended_crop": "rice", "crop_confidence": 0.95,
        "current_crop": "rice", "soil_type": "clay",
        "days_since_planting": 60,
        "deficit_N": 0.0, "deficit_P": 0.0, "deficit_K": 0.0,
        "soil_health_score": 94.0,
        "water_requirement_idx": 5.0, "ph_adjustment": 0.0,
        "temp_stress_score": 1.0, "fertilizer_urgency": 0.0,
        "planting_readiness": 94.0,
        "disease_detected": None, "disease_confidence": 0.0,
        "soil_type_vision": "clay", "soil_type_confidence": 0.91,
        "user_query": "Is my field doing okay?",
        "mitra_response": "Your rice field is in excellent condition.",
        "user_notes": None,
        "row_trigger": "smoke_test",
    }
    row_id = store.append_new_row(sample)
    print(f"\nInserted row #{row_id}")

    latest = store.get_latest_state(3)
    print(f"\nLatest {len(latest)} rows:")
    for row in latest:
        print(f"  #{row['id']}  {row['timestamp']}  crop={row['current_crop']}")

    print("\n" + "=" * 60)
    print("LLM Context Block:")
    print("=" * 60)
    print(store.format_history_for_llm())
