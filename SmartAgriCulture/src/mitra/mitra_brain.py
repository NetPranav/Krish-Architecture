"""
==============================================================================
  SmartAgri · Mitra Brain — The Agentic Orchestrator
  ──────────────────────────────────────────────────
  Cloud-first orchestrator using NVIDIA NIM API.

  Key Design:
    - NVIDIA NIM API (OpenAI-compatible) for LLM inference
    - Fast model: meta/llama-3.1-8b-instruct (~1-2s responses)
    - AI writes new DB rows ONLY when user reveals new facts
    - Vision models lazy-loaded and unloaded after use
==============================================================================
"""

import os
import sys
import gc
import json
import logging
import warnings
import time
import numpy as np
import pandas as pd
import joblib

from datetime import datetime, timezone
from openai import OpenAI
from src.mitra.datastore import FarmDataStore

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

# ── NVIDIA NIM API Configuration ─────────────────────────────────────────
NVIDIA_API_KEY  = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_MODEL    = os.getenv("NVIDIA_MODEL", "meta/llama-3.1-8b-instruct")
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

CROP_MODEL_DIR  = "models/crop_detection"
FERT_MODEL_PATH = "models/fertilizer_optimization/master_ag_model.pkl"




# ─────────────────────────────────────────────────────────────────────────
# THE ORCHESTRATOR
# ─────────────────────────────────────────────────────────────────────────
class MitraOrchestrator:
    """
    Central brain of SmartAgri. Accepts user text, live sensors,
    and optional image bytes. Orchestrates all models, queries the
    NVIDIA NIM LLM API, and persists everything to SQLite.
    """

    def __init__(self):
        self.datastore = FarmDataStore()

        # ML models (loaded on-demand, unloaded after use if needed)
        self.crop_model = None
        self.crop_scaler = None
        self.crop_encoder = None
        self.fert_pipeline = None
        self.vision_predictor = None

        # Pre-load lightweight CPU models at startup
        self._load_crop_model()
        self._load_fert_model()

        # NVIDIA NIM API client (OpenAI-compatible)
        if not NVIDIA_API_KEY:
            log.warning("NVIDIA_API_KEY not set — LLM calls will fail!")
        self.llm_client = OpenAI(
            base_url=NVIDIA_BASE_URL,
            api_key=NVIDIA_API_KEY or "placeholder",
        )

        log.info("MitraOrchestrator initialised (model=%s).", NVIDIA_MODEL)

    # ─────────────────────────────────────────────────────────────────────
    # Model Loaders
    # ─────────────────────────────────────────────────────────────────────
    def _load_crop_model(self):
        model_path = os.path.join(CROP_MODEL_DIR, "xgb_crop_model.pkl")
        if not os.path.exists(model_path):
            log.warning("Crop model not found at %s", model_path)
            return
        self.crop_model = joblib.load(model_path)
        self.crop_scaler = joblib.load(os.path.join(CROP_MODEL_DIR, "scaler.pkl"))
        self.crop_encoder = joblib.load(os.path.join(CROP_MODEL_DIR, "label_encoder.pkl"))
        log.info("Crop Detection model loaded.")

    def _load_fert_model(self):
        if not os.path.exists(FERT_MODEL_PATH):
            log.warning("Fertilizer model not found at %s", FERT_MODEL_PATH)
            return
        self.fert_pipeline = joblib.load(FERT_MODEL_PATH)
        log.info("Fertilizer Optimization model loaded.")

    def _get_vision_predictor(self):
        if self.vision_predictor is None:
            try:
                from src.vision.roboflow_client import CloudVisionPredictor
                self.vision_predictor = CloudVisionPredictor()
            except Exception as e:
                log.error("Vision predictor load failed: %s", e)
        return self.vision_predictor

    def _unload_vision(self):
        """Free vision predictor memory after use."""
        if self.vision_predictor is not None:
            del self.vision_predictor
            self.vision_predictor = None
            gc.collect()
            log.info("Vision predictor unloaded.")

    # ─────────────────────────────────────────────────────────────────────
    # Feature Engineering
    # ─────────────────────────────────────────────────────────────────────
    @staticmethod
    def _compute_derived_features(raw: dict) -> dict:
        N = raw.get("N", 50.0)
        P = raw.get("P", 50.0)
        K = raw.get("K", 50.0)
        temp = raw.get("temperature", 25.0)
        hum = raw.get("humidity", 60.0)
        ph = raw.get("ph", 6.5)
        rain = raw.get("rainfall", 100.0)
        return {
            "N": N, "P": P, "K": K,
            "temperature": temp, "humidity": hum,
            "ph": ph, "rainfall": rain,
            "N_P_ratio": N / (P + 1e-5),
            "N_K_ratio": N / (K + 1e-5),
            "P_K_ratio": P / (K + 1e-5),
            "THI": temp * hum,
            "water_availability": rain * (hum / 100.0),
            "pH_stress": abs(ph - 6.5),
        }

    # ─────────────────────────────────────────────────────────────────────
    # Phase A: Vision AI (image → disease + soil)
    # ─────────────────────────────────────────────────────────────────────
    def _run_vision(self, image_bytes: bytes) -> dict:
        log.info("[Phase A] Loading Vision AI...")

        predictor = self._get_vision_predictor()
        if predictor is None:
            return {"disease": None, "disease_confidence": 0.0,
                    "soil_type": None, "soil_confidence": 0.0}
        try:
            result = predictor.scan_image(image_bytes)
            return {
                "disease": result.get("disease"),
                "disease_confidence": result.get("disease_confidence", 0.0),
                "soil_type": result.get("soil_type"),
                "soil_confidence": result.get("soil_confidence", 0.0),
            }
        except Exception as e:
            log.error("Vision inference failed: %s", e)
            return {"disease": None, "disease_confidence": 0.0,
                    "soil_type": None, "soil_confidence": 0.0}
        finally:
            self._unload_vision()

    # ─────────────────────────────────────────────────────────────────────
    # Phase B: Crop Detection (sensors → recommended crop)
    # ─────────────────────────────────────────────────────────────────────
    def _run_crop_detection(self, sensors: dict) -> tuple:
        if self.crop_model is None:
            return "unknown", 0.0
        features = self._compute_derived_features(sensors)
        COLS = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall",
                "N_P_ratio", "N_K_ratio", "P_K_ratio",
                "THI", "water_availability", "pH_stress"]
        df = pd.DataFrame([features])[COLS]
        X = self.crop_scaler.transform(df.values)
        pred_idx = self.crop_model.predict(X)[0]
        proba = self.crop_model.predict_proba(X)[0]
        crop = self.crop_encoder.inverse_transform([pred_idx])[0]
        return crop, round(float(proba[pred_idx]), 4)

    # ─────────────────────────────────────────────────────────────────────
    # Phase C: Fertilizer Optimization (sensors+crop → 9 targets)
    # ─────────────────────────────────────────────────────────────────────
    def _run_fertilizer_model(self, sensors: dict, current_crop: str,
                              recommended_crop: str, soil_type: str,
                              days: int) -> dict:
        if self.fert_pipeline is None:
            return {}
        features = self._compute_derived_features(sensors)
        features["Current_Crop"] = current_crop
        features["Recommended_Crop"] = recommended_crop
        features["Soil_Type"] = soil_type or "clay"
        features["Days_Since_Planting"] = days

        COLS = ["Current_Crop", "Recommended_Crop", "Soil_Type",
                "Days_Since_Planting",
                "N", "P", "K", "temperature", "humidity", "ph", "rainfall",
                "N_P_ratio", "N_K_ratio", "P_K_ratio",
                "THI", "water_availability", "pH_stress"]
        df = pd.DataFrame([features])[COLS]
        preds = self.fert_pipeline.predict(df)[0]

        TARGETS = ["Deficit_N", "Deficit_P", "Deficit_K", "Soil_Health_Score",
                    "Water_Requirement_Index", "pH_Adjustment_Required",
                    "Temperature_Stress_Score", "Fertilizer_Urgency_Score",
                    "Planting_Readiness_Score"]
        return {name: round(float(preds[i]), 2) if i < len(preds) else 0.0
                for i, name in enumerate(TARGETS)}

    # ─────────────────────────────────────────────────────────────────────
    # Phase D: LLM Call (NVIDIA NIM API — meta/llama-3.1-8b-instruct)
    # ─────────────────────────────────────────────────────────────────────
    def _call_llm(self, system_prompt: str, user_message: str) -> dict:
        """
        Calls NVIDIA NIM API (OpenAI-compatible) for fast cloud inference.
          - Model: meta/llama-3.1-8b-instruct (fastest, ~1-2s)
          - max_tokens: 200 (keep responses short)
          - temperature: 0.3 (factual, low hallucination)
        """
        log.info("[Phase D] Calling NVIDIA NIM API (%s)...", NVIDIA_MODEL)

        try:
            completion = self.llm_client.chat.completions.create(
                model=NVIDIA_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.3,
                top_p=0.5,
                max_tokens=200,
            )
            content = completion.choices[0].message.content or "{}"

            # Try to parse as JSON first
            try:
                parsed = json.loads(content)
                return {
                    "farmer_response": parsed.get("farmer_response",
                        "I could not process your request right now."),
                    "user_notes": parsed.get("user_notes"),
                    "profile_updates": parsed.get("profile_updates"),
                }
            except json.JSONDecodeError:
                # If the model didn't return valid JSON, try to extract it
                import re
                json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
                if json_match:
                    try:
                        parsed = json.loads(json_match.group())
                        return {
                            "farmer_response": parsed.get("farmer_response", content),
                            "user_notes": parsed.get("user_notes"),
                            "profile_updates": parsed.get("profile_updates"),
                        }
                    except json.JSONDecodeError:
                        pass
                log.warning("LLM returned non-JSON, using raw text.")
                return {"farmer_response": content.strip(),
                        "user_notes": None, "profile_updates": None}

        except Exception as e:
            log.error("NVIDIA NIM API call failed: %s", e)
            return {
                "farmer_response": (
                    "I'm having trouble connecting right now. "
                    "Please try again in a moment."
                ),
                "user_notes": None, "profile_updates": None,
            }

    # ─────────────────────────────────────────────────────────────────────
    # System Prompt Builder
    # ─────────────────────────────────────────────────────────────────────
    def _build_system_prompt(self, *, history_text, profile_text,
                             live_sensors, current_crop, recommended_crop,
                             crop_confidence, soil_type, fert_output,
                             vision_result, days) -> str:
        # Disease section
        if vision_result.get("disease"):
            disease_sec = (
                f"VISION AI (from uploaded photo):\n"
                f"  Disease: {vision_result['disease']} "
                f"(conf: {vision_result['disease_confidence']:.0%})\n"
                f"  Soil Type: {vision_result.get('soil_type', 'N/A')} "
                f"(conf: {vision_result.get('soil_confidence', 0):.0%})\n"
            )
        else:
            disease_sec = "VISION AI: No photo uploaded.\n"

        # Sensor lines
        sensor_lines = []
        for key in ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]:
            val = live_sensors.get(key)
            sensor_lines.append(f"  {key}: {val}" if val is not None
                                else f"  {key}: OFFLINE")
        sensor_text = "\n".join(sensor_lines)

        # Fert output
        fert_lines = [f"  {k}: {v}" for k, v in fert_output.items()]
        fert_text = "\n".join(fert_lines) if fert_lines else "  (unavailable)"

        return f"""You are Mitra, the AI farming assistant for SmartAgri.
You help Indian farmers understand their crop health and make decisions.

RULES:
1. Respond in simple, clear language a farmer can understand.
2. Base advice on the REAL DATA below only. Never guess.
3. EXTREMELY CRITICAL: Keep your answer incredibly short (1-2 sentences maximum). Do not over-explain.
4. You MUST respond ONLY with valid JSON in this exact format (no extra text before or after):
{{"farmer_response": "Your 1-2 sentence helpful answer...", "user_notes": null, "profile_updates": null}}

5. Set "user_notes" ONLY if the user reveals something NEW (e.g. "I watered today", "my land is 5 acres").
6. Set "profile_updates" ONLY if the user mentions a PERSISTENT fact:
   - land_size_acres, irrigation_type, region, preferred_language
   - Example: user says "I have 3 acres" -> {{"land_size_acres": "3"}}
   - If the user just asks a question, set BOTH to null.

Current Crop: {current_crop} | Recommended: {recommended_crop} ({crop_confidence:.0%}) | Soil: {soil_type} | Day: {days}
Sensors: {sensor_text}
{disease_sec}
Fert: {fert_text}
"""

    # ─────────────────────────────────────────────────────────────────────
    # THE MAIN PIPELINE
    # ─────────────────────────────────────────────────────────────────────
    def process_interaction(
        self,
        user_text: str,
        live_sensors: dict,
        current_crop: str = None,
        days_since_planting: int = 60,
        image_bytes: bytes = None,
    ) -> str:
        """
        Full agentic pipeline with VRAM-aware phased execution:
          Phase A: Vision AI (if image) -> unload -> free VRAM
          Phase B: Crop Detection (CPU/GPU XGBoost)
          Phase C: Fertilizer Optimization (CPU/GPU XGBoost)
          Phase D: Clear VRAM -> Ollama LLM (needs full 8GB)
          Phase E: Parse response -> write to SQLite
        """
        t0 = time.perf_counter()
        log.info("=" * 60)
        log.info("MITRA PIPELINE START")
        log.info("  User: %s", user_text[:100])
        log.info("=" * 60)

        # ── Step 1: Historical Context ────────────────────────────────
        log.info("[Step 1] Reading ledger + profile...")
        history_text = self.datastore.format_history_for_llm(n=3)
        profile_text = self.datastore.format_profile_for_llm()
        latest_rows = self.datastore.get_latest_state(n=1)
        latest = latest_rows[0] if latest_rows else {}

        if not current_crop:
            current_crop = latest.get("current_crop", "unknown")

        # ── Phase A: Vision (if image provided) ──────────────────────
        vision_result = {"disease": None, "disease_confidence": 0.0,
                         "soil_type": None, "soil_confidence": 0.0}
        if image_bytes:
            log.info("[Phase A] Running Vision AI...")
            vision_result = self._run_vision(image_bytes)
            log.info("  Disease: %s (%.2f)", vision_result["disease"],
                     vision_result["disease_confidence"])
        else:
            log.info("[Phase A] No image -> skip vision.")

        soil_type = (vision_result.get("soil_type")
                     or latest.get("soil_type_vision")
                     or latest.get("soil_type") or "clay")

        # ── Phase B: Crop Detection ──────────────────────────────────
        log.info("[Phase B] Running Crop Detection...")
        recommended_crop, crop_conf = self._run_crop_detection(live_sensors)
        log.info("  Recommended: %s (%.1f%%)", recommended_crop, crop_conf * 100)

        # ── Phase C: Fertilizer Optimization ─────────────────────────
        log.info("[Phase C] Running Fertilizer Optimization...")
        fert_output = self._run_fertilizer_model(
            live_sensors, current_crop, recommended_crop, soil_type,
            days_since_planting)
        log.info("  Soil Health: %.1f/100", fert_output.get("Soil_Health_Score", 0))

        # ── Phase D: LLM (NVIDIA NIM API call) ────────────────────────
        log.info("[Phase D] Building prompt -> calling NVIDIA NIM API...")
        derived = self._compute_derived_features(live_sensors)

        system_prompt = self._build_system_prompt(
            history_text=history_text, profile_text=profile_text,
            live_sensors=live_sensors, current_crop=current_crop,
            recommended_crop=recommended_crop, crop_confidence=crop_conf,
            soil_type=soil_type, fert_output=fert_output,
            vision_result=vision_result, days=days_since_planting)

        llm_result = self._call_llm(system_prompt, user_text)
        farmer_response = llm_result["farmer_response"]
        user_notes = llm_result.get("user_notes")
        profile_updates = llm_result.get("profile_updates")

        log.info("[Phase D] LLM done.")
        if user_notes:
            log.info("  Extracted note: %s", user_notes)

        # ── Phase E: Write to SQLite ─────────────────────────────────
        log.info("[Phase E] Writing to ledger...")
        ledger_row = {
            # Sensors
            "sensor_N": live_sensors.get("N"),
            "sensor_P": live_sensors.get("P"),
            "sensor_K": live_sensors.get("K"),
            "sensor_temperature": live_sensors.get("temperature"),
            "sensor_humidity": live_sensors.get("humidity"),
            "sensor_ph": live_sensors.get("ph"),
            "sensor_rainfall": live_sensors.get("rainfall"),
            "sensor_moisture": live_sensors.get("Moisture"),
            # Derived features
            "feat_N_P_ratio": derived.get("N_P_ratio"),
            "feat_N_K_ratio": derived.get("N_K_ratio"),
            "feat_P_K_ratio": derived.get("P_K_ratio"),
            "feat_THI": derived.get("THI"),
            "feat_water_availability": derived.get("water_availability"),
            "feat_pH_stress": derived.get("pH_stress"),
            # Crop Detection
            "recommended_crop": recommended_crop,
            "crop_confidence": crop_conf,
            # Fertilizer
            "current_crop": current_crop,
            "soil_type": soil_type,
            "days_since_planting": days_since_planting,
            "deficit_N": fert_output.get("Deficit_N", 0.0),
            "deficit_P": fert_output.get("Deficit_P", 0.0),
            "deficit_K": fert_output.get("Deficit_K", 0.0),
            "soil_health_score": fert_output.get("Soil_Health_Score", 0.0),
            "water_requirement_idx": fert_output.get("Water_Requirement_Index", 0.0),
            "ph_adjustment": fert_output.get("pH_Adjustment_Required", 0.0),
            "temp_stress_score": fert_output.get("Temperature_Stress_Score", 0.0),
            "fertilizer_urgency": fert_output.get("Fertilizer_Urgency_Score", 0.0),
            "planting_readiness": fert_output.get("Planting_Readiness_Score", 0.0),
            # Vision
            "disease_detected": vision_result.get("disease"),
            "disease_confidence": vision_result.get("disease_confidence", 0.0),
            "soil_type_vision": vision_result.get("soil_type"),
            "soil_type_confidence": vision_result.get("soil_confidence", 0.0),
            "image_analyzed": 1 if image_bytes else 0,
            # LLM
            "user_query": user_text,
            "mitra_response": farmer_response,
            "user_notes": user_notes,
            # Meta
            "interaction_source": "mitra_chat",
            "row_trigger": "user_chat",
        }
        self.datastore.append_new_row(ledger_row)

        # ── Profile updates (AI-gated — only when user reveals facts) ─
        if profile_updates and isinstance(profile_updates, dict):
            for key, value in profile_updates.items():
                if value is not None and str(value).strip():
                    self.datastore.update_user_meta(key, str(value))
                    log.info("  Profile updated: %s = %s", key, value)

        elapsed = time.perf_counter() - t0
        log.info("=" * 60)
        log.info("MITRA PIPELINE COMPLETE  (%.1fs)", elapsed)
        log.info("=" * 60)

        return farmer_response


# ─────────────────────────────────────────────────────────────────────────
# Standalone smoke test
# ─────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  Mitra Brain - Smoke Test")
    print("=" * 60)

    m = MitraOrchestrator()
    resp = m.process_interaction(
        user_text="My rice field has yellow leaves. I have 5 acres of land.",
        live_sensors={
            "N": 80.0, "P": 45.0, "K": 40.0,
            "temperature": 32.0, "humidity": 55.0,
            "ph": 6.3, "rainfall": 10.0,
        },
        current_crop="rice",
        days_since_planting=45,
    )
    print("\nMITRA SAYS:")
    print(resp)
