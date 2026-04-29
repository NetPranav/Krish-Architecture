"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  PHASE 3 — The Gap Analysis & Advisory Engine                               ║
║  SmartAgri · AgriAdvisor — Inference + Report Generation                    ║
╚══════════════════════════════════════════════════════════════════════════════╝

Loads the trained multi-output regression pipeline (master_ag_model.pkl),
runs inference from raw sensor data, handles missing/offline sensors
gracefully, and generates a structured text advisory report.

USAGE:
  python inference.py                # runs demo scenarios
  
  # Or import in your backend:
  from inference import AgriAdvisor
  advisor = AgriAdvisor()
  report  = advisor.generate_report("maize", "rice", 45, {"N": 80, "P": 40, "K": 38})
  print(report)
"""

import os
import warnings
import logging
from datetime import datetime
from textwrap import dedent

import numpy as np
import pandas as pd
import joblib

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

MODEL_PATH = "models/fertilizer_optimization/master_ag_model.pkl"

# Full list of sensor keys the model expects
SENSOR_KEYS = [
    "N", "P", "K", "temperature", "humidity", "ph", "rainfall",
    "N_P_ratio", "N_K_ratio", "P_K_ratio",
    "THI", "water_availability", "pH_stress",
]

# Columns that go into the model (order matters to match CATEGORICAL + NUMERIC)
ALL_FEATURES = [
    "Current_Crop", "Recommended_Crop", "Soil_Type",
    "Days_Since_Planting",
    "N", "P", "K", "temperature", "humidity", "ph", "rainfall",
    "N_P_ratio", "N_K_ratio", "P_K_ratio",
    "THI", "water_availability", "pH_stress",
]

TARGETS = ["Deficit_N", "Deficit_P", "Deficit_K", "Soil_Health_Score"]

# Human-readable sensor names
SENSOR_LABELS = {
    "N": "Nitrogen (N) sensor",
    "P": "Phosphorus (P) sensor",
    "K": "Potassium (K) sensor",
    "temperature": "Temperature sensor",
    "humidity": "Humidity sensor",
    "ph": "pH sensor",
    "rainfall": "Rainfall gauge",
}


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE ENGINEERING (mirrors data_prep.py — single source of truth)
# ─────────────────────────────────────────────────────────────────────────────
def compute_derived_features(data: dict) -> dict:
    """
    Computes the 6 derived features from raw sensor values.
    Uses NaN-safe math — if any input is NaN, the derived value is also NaN,
    which XGBoost handles natively.
    """
    n    = data.get("N", np.nan)
    p    = data.get("P", np.nan)
    k    = data.get("K", np.nan)
    temp = data.get("temperature", np.nan)
    hum  = data.get("humidity", np.nan)
    ph   = data.get("ph", np.nan)
    rain = data.get("rainfall", np.nan)

    data["N_P_ratio"]          = n / (p + 1e-5) if not (np.isnan(n) or np.isnan(p)) else np.nan
    data["N_K_ratio"]          = n / (k + 1e-5) if not (np.isnan(n) or np.isnan(k)) else np.nan
    data["P_K_ratio"]          = p / (k + 1e-5) if not (np.isnan(p) or np.isnan(k)) else np.nan
    data["THI"]                = temp * hum      if not (np.isnan(temp) or np.isnan(hum)) else np.nan
    data["water_availability"] = rain * (hum / 100.0) if not (np.isnan(rain) or np.isnan(hum)) else np.nan
    data["pH_stress"]          = abs(ph - 6.5)   if not np.isnan(ph) else np.nan

    return data


# ─────────────────────────────────────────────────────────────────────────────
# AGRI ADVISOR CLASS
# ─────────────────────────────────────────────────────────────────────────────
class AgriAdvisor:
    """
    Loads the trained multi-output regression model and provides
    structured advisory reports from raw sensor inputs.

    Handles:
      - Missing sensor keys → sets to NaN (XGBoost-native fallback)
      - Derived feature computation
      - Structured text report generation
    """

    def __init__(self, model_path: str = MODEL_PATH):
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model not found: {model_path}\n"
                "Run `python data_prep.py` then `python model_trainer.py` first."
            )
        self.pipeline = joblib.load(model_path)
        log.info(f"✅  AgriAdvisor loaded model from {model_path}")

    def generate_report(self,
                        current_crop: str,
                        recommended_crop: str,
                        soil_type: str,
                        days_growing: int,
                        sensor_data: dict) -> str:
        """
        Runs inference and generates a structured advisory report.

        Args:
            current_crop:      What the farmer is currently growing (e.g. "maize")
            recommended_crop:  What the recommendation engine suggests (e.g. "rice")
            soil_type:         Soil type from vision model (e.g. "red", "clay", "yellow")
            days_growing:      Days since planting (0–150)
            sensor_data:       Dict of sensor readings. Missing keys are
                               treated as offline sensors → NaN → XGBoost fallback.
                               Expected keys: N, P, K, temperature, humidity, ph, rainfall

        Returns:
            Formatted string report.
        """
        # ── 1. Detect offline sensors ─────────────────────────────────────
        offline_sensors = []
        raw_base_keys   = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
        for key in raw_base_keys:
            if key not in sensor_data or sensor_data[key] is None:
                offline_sensors.append(key)

        # ── 2. Build feature dict ─────────────────────────────────────────
        feat_data = {}
        for key in raw_base_keys:
            feat_data[key] = float(sensor_data[key]) if key in sensor_data and sensor_data[key] is not None else np.nan

        # Compute derived features
        feat_data = compute_derived_features(feat_data)

        # Add crop + soil + days
        feat_data["Current_Crop"]       = current_crop
        feat_data["Recommended_Crop"]   = recommended_crop
        feat_data["Soil_Type"]          = soil_type
        feat_data["Days_Since_Planting"] = days_growing

        # ── 3. Build DataFrame in exact column order ──────────────────────
        X = pd.DataFrame([{col: feat_data.get(col, np.nan) for col in ALL_FEATURES}])

        # ── 4. Predict ────────────────────────────────────────────────────
        predictions = self.pipeline.predict(X)[0]

        deficit_n    = max(0, predictions[0])
        deficit_p    = max(0, predictions[1])
        deficit_k    = max(0, predictions[2])
        soil_score   = max(0, min(100, predictions[3]))
        
        # Unpack the 5 new ML-predicted advisory targets
        ml_water = max(0, min(100, predictions[4]))
        ml_ph_adj = predictions[5]
        ml_temp_stress = max(0, min(100, predictions[6]))
        ml_fert_urgency = max(0, min(100, predictions[7]))
        ml_plant_ready = max(0, min(100, predictions[8]))

        # ── 5. Generate smart advisories from ML predictions ──────────────
        advisories = self.build_advisories_from_ml(
            ml_water=ml_water,
            ml_ph_adj=ml_ph_adj,
            ml_temp_stress=ml_temp_stress,
            ml_fert_urgency=ml_fert_urgency,
            ml_plant_ready=ml_plant_ready
        )

        # ── 6. Generate report ────────────────────────────────────────────
        report = self._format_report(
            current_crop=current_crop,
            recommended_crop=recommended_crop,
            days_growing=days_growing,
            soil_type=soil_type,
            sensor_data=sensor_data,
            offline_sensors=offline_sensors,
            deficit_n=deficit_n,
            deficit_p=deficit_p,
            deficit_k=deficit_k,
            soil_score=soil_score,
            advisories=advisories,
        )
        return report

    # ─────────────────────────────────────────────────────────────────────
    # SMART ADVISORIES — 5 most common farmer questions
    # ─────────────────────────────────────────────────────────────────────
    def build_advisories_from_ml(self, *, ml_water, ml_ph_adj, ml_temp_stress, ml_fert_urgency, ml_plant_ready) -> dict:
        """
        Takes the 5 new targets predicted directly by the Multi-Output XGBoost model
        and translates them into the 5 farmer Q&A advisories.
        """
        advisories = {}

        # 1. Water
        if ml_water > 50:
            advisories["should_water"] = {
                "question": "Should I water my crop right now?",
                "answer": "YES",
                "reason": f"AI Water Requirement Index is high ({ml_water:.0f}/100). Irrigate soon.",
                "severity": "high" if ml_water > 80 else "medium",
            }
        else:
            advisories["should_water"] = {
                "question": "Should I water my crop right now?",
                "answer": "NO",
                "reason": f"AI Water Requirement Index is low ({ml_water:.0f}/100). No irrigation needed.",
                "severity": "low",
            }

        # 2. pH
        if abs(ml_ph_adj) > 0.5:
            direction = "lime" if ml_ph_adj > 0 else "sulfur"
            advisories["ph_status"] = {
                "question": "Is my soil pH okay for this crop?",
                "answer": "NO",
                "reason": f"AI suggests a pH adjustment of {ml_ph_adj:+.1f}. Consider adding {direction}.",
                "severity": "high" if abs(ml_ph_adj) > 1.5 else "medium",
            }
        else:
            advisories["ph_status"] = {
                "question": "Is my soil pH okay for this crop?",
                "answer": "YES",
                "reason": "AI predicts your soil pH is optimal for this crop.",
                "severity": "low",
            }

        # 3. Temperature
        if ml_temp_stress > 40:
            advisories["temperature_safe"] = {
                "question": "Is the temperature safe for my crop?",
                "answer": "NO",
                "reason": f"AI detected significant temperature stress (Score: {ml_temp_stress:.0f}/100).",
                "severity": "high" if ml_temp_stress > 70 else "medium",
            }
        else:
            advisories["temperature_safe"] = {
                "question": "Is the temperature safe for my crop?",
                "answer": "YES",
                "reason": f"AI Temperature stress score is low ({ml_temp_stress:.0f}/100). Safe growing conditions.",
                "severity": "low",
            }

        # 4. Fertilizer
        if ml_fert_urgency > 30:
            advisories["needs_fertilizer"] = {
                "question": "Do I need to add fertilizer right now?",
                "answer": "YES",
                "reason": f"AI Fertilizer Urgency Score is {ml_fert_urgency:.0f}/100. Check the action plan for amounts.",
                "severity": "high" if ml_fert_urgency > 70 else "medium",
            }
        else:
            advisories["needs_fertilizer"] = {
                "question": "Do I need to add fertilizer right now?",
                "answer": "NO",
                "reason": f"AI Fertilizer Urgency Score is low ({ml_fert_urgency:.0f}/100). Levels are adequate.",
                "severity": "low",
            }

        # 5. Plant Readiness
        if ml_plant_ready > 60:
            advisories["ready_to_plant"] = {
                "question": "Is my soil healthy enough to plant a new crop?",
                "answer": "YES",
                "reason": f"AI Planting Readiness Score is excellent ({ml_plant_ready:.0f}/100).",
                "severity": "low",
            }
        else:
            advisories["ready_to_plant"] = {
                "question": "Is my soil healthy enough to plant a new crop?",
                "answer": "NO",
                "reason": f"AI Planting Readiness Score is poor ({ml_plant_ready:.0f}/100). Amend soil first.",
                "severity": "high",
            }

        return advisories

    def _format_report(self, *, current_crop, recommended_crop, days_growing,
                       soil_type, sensor_data, offline_sensors,
                       deficit_n, deficit_p, deficit_k, soil_score,
                       advisories) -> str:

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        crop_match = current_crop.lower() == recommended_crop.lower()

        # ── System Status ─────────────────────────────────────────────────
        if offline_sensors:
            status_lines = []
            for s in offline_sensors:
                label = SENSOR_LABELS.get(s, s)
                status_lines.append(f"    ⚠️  {label} OFFLINE. Proceeding with predictive fallback.")
            system_status = "\n".join(status_lines)
        else:
            system_status = "    ✅  All sensors reporting normally."

        # ── Soil Health Bar ───────────────────────────────────────────────
        filled    = int(soil_score / 5)
        empty     = 20 - filled
        score_bar = "█" * filled + "░" * empty

        if soil_score >= 80:
            health_label = "EXCELLENT"
            health_emoji = "🟢"
        elif soil_score >= 60:
            health_label = "GOOD"
            health_emoji = "🟡"
        elif soil_score >= 40:
            health_label = "FAIR"
            health_emoji = "🟠"
        else:
            health_label = "POOR"
            health_emoji = "🔴"

        # ── Reality Check ─────────────────────────────────────────────────
        if crop_match:
            reality = (
                f"    ✅  You are growing [{current_crop.upper()}], which matches\n"
                f"        the AI-recommended crop for your soil conditions.\n"
                f"        Your field is operating at optimal crop-soil alignment."
            )
        else:
            reality = (
                f"    ⚡  You are currently growing [{current_crop.upper()}], but your\n"
                f"        soil and environment are optimized for [{recommended_crop.upper()}].\n"
                f"        Consider transitioning for higher yield and profit."
            )

        # ── Action Plan ───────────────────────────────────────────────────
        actions = []
        if deficit_n > 1:
            actions.append(f"    💊  Apply {deficit_n:.1f} kg/ha of Nitrogen (N)")
        if deficit_p > 1:
            actions.append(f"    💊  Apply {deficit_p:.1f} kg/ha of Phosphorus (P)")
        if deficit_k > 1:
            actions.append(f"    💊  Apply {deficit_k:.1f} kg/ha of Potassium (K)")

        if not actions:
            action_text = "    ✅  No significant nutrient deficits detected.\n        Your nutrient levels are adequate for the current growth stage."
        else:
            action_text = "\n".join(actions)
            action_text += f"\n        ↑ Required to sustain [{current_crop.upper()}] at Day {days_growing}."

        if not crop_match and (deficit_n > 1 or deficit_p > 1 or deficit_k > 1):
            action_text += (
                f"\n\n    🔄  TRANSITION ADVISORY:\n"
                f"        To switch to [{recommended_crop.upper()}] for optimal yield,\n"
                f"        adjust nutrient inputs based on the recommended crop's profile."
            )

        # ── Sensor Readings ───────────────────────────────────────────────
        sensor_lines = []
        for key in ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]:
            if key in sensor_data and sensor_data[key] is not None:
                val = sensor_data[key]
                unit = {"N": "kg/ha", "P": "kg/ha", "K": "kg/ha",
                        "temperature": "°C", "humidity": "%",
                        "ph": "", "rainfall": "mm"}.get(key, "")
                sensor_lines.append(f"    {key:<14} : {val:>8.1f} {unit}")
            else:
                sensor_lines.append(f"    {key:<14} :      N/A  (offline)")
        sensor_table = "\n".join(sensor_lines)

        # ── Assemble Report ───────────────────────────────────────────────
        report = f"""
╔══════════════════════════════════════════════════════════════════╗
║           SmartAgri · Gap Analysis Advisory Report              ║
╠══════════════════════════════════════════════════════════════════╣
║  Generated : {timestamp:<49}║
║  Crop      : {current_crop:<20} → Recommended: {recommended_crop:<13}║
║  Day       : {days_growing:<49}║
║  Soil Type : {soil_type:<49}║
╠══════════════════════════════════════════════════════════════════╣

  ── SYSTEM STATUS ────────────────────────────────────────────────
{system_status}

  ── SENSOR READINGS ──────────────────────────────────────────────
{sensor_table}

  ── SOIL HEALTH ──────────────────────────────────────────────────
    {health_emoji}  Soil Health Score: {soil_score:.1f} / 100  [{health_label}]
       [{score_bar}]

  ── THE REALITY CHECK ────────────────────────────────────────────
{reality}

  ── NUTRIENT DEFICIT ANALYSIS ────────────────────────────────────
    Deficit_N  : {deficit_n:>8.1f} kg/ha
    Deficit_P  : {deficit_p:>8.1f} kg/ha
    Deficit_K  : {deficit_k:>8.1f} kg/ha

  ── ACTION PLAN ──────────────────────────────────────────────────
{action_text}

  ── SMART ADVISORIES (Farmer Q&A) ────────────────────────────────
{self._format_advisories(advisories)}

╚══════════════════════════════════════════════════════════════════╝"""
        return report

    @staticmethod
    def _format_advisories(advisories: dict) -> str:
        """Formats the 5 advisories as readable text for the report."""
        lines = []
        icons = {"YES": "[YES]", "NO": "[NO] ", "UNKNOWN": "[???]"}
        sev_icons = {"low": "    ", "medium": " (!) ", "high": " (!!) ", "critical": "(!!!)"}
        for key, adv in advisories.items():
            ans = icons.get(adv["answer"], "[???]")
            sev = sev_icons.get(adv["severity"], "")
            lines.append(f"    {ans} {adv['question']}")
            lines.append(f"         {adv['reason']}")
            lines.append("")
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# DEMO SCENARIOS
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("\n" + "═" * 65)
    print("   SmartAgri · Phase 3 — Inference & Advisory Demo")
    print("═" * 65 + "\n")

    advisor = AgriAdvisor()

    # ── Scenario 1: Full sensor data, crop mismatch ───────────────────────
    print("\n" + "─" * 65)
    print("  SCENARIO 1: Full sensors, crop mismatch")
    print("─" * 65)
    report1 = advisor.generate_report(
        current_crop="maize",
        recommended_crop="rice",
        soil_type="clay",
        days_growing=45,
        sensor_data={
            "N": 65.0, "P": 38.0, "K": 35.0,
            "temperature": 24.5, "humidity": 78.0,
            "ph": 6.2, "rainfall": 220.0,
        }
    )
    print(report1)

    # ── Scenario 2: Missing sensors (hardware failure) ────────────────────
    print("\n" + "─" * 65)
    print("  SCENARIO 2: Partial sensor failure (humidity + pH offline)")
    print("─" * 65)
    report2 = advisor.generate_report(
        current_crop="chickpea",
        recommended_crop="chickpea",
        soil_type="yellow",
        days_growing=80,
        sensor_data={
            "N": 40.0, "P": 65.0, "K": 78.0,
            "temperature": 28.0,
            # humidity and ph are MISSING → simulates hardware failure
            "rainfall": 45.0,
        }
    )
    print(report2)

    # ── Scenario 3: Minimal payload (ESP32 sends only N, P, K, Moisture) ──
    print("\n" + "─" * 65)
    print("  SCENARIO 3: Minimal ESP32 payload (only N, P, K)")
    print("─" * 65)
    report3 = advisor.generate_report(
        current_crop="banana",
        recommended_crop="mango",
        soil_type="red",
        days_growing=120,
        sensor_data={
            "N": 100.0, "P": 18.0, "K": 50.0,
        }
    )
    print(report3)

    # ── Scenario 4: Perfect conditions ────────────────────────────────────
    print("\n" + "─" * 65)
    print("  SCENARIO 4: Ideal conditions — crop match")
    print("─" * 65)
    report4 = advisor.generate_report(
        current_crop="rice",
        recommended_crop="rice",
        soil_type="clay",
        days_growing=60,
        sensor_data={
            "N": 80.0, "P": 48.0, "K": 40.0,
            "temperature": 25.0, "humidity": 85.0,
            "ph": 6.5, "rainfall": 230.0,
        }
    )
    print(report4)

    print("\n✅  All scenarios complete.\n")


if __name__ == "__main__":
    main()
