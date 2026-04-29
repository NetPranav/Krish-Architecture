"""
==============================================================================
  SmartAgri · Mitra Brain — The Agentic Orchestrator
  ──────────────────────────────────────────────────
  VRAM-Aware orchestrator for 16GB RAM / 8GB VRAM systems.

  Key Design:
    - Phased GPU memory: clears VRAM before loading each model
    - Ollama gpt4o-s:20b with constrained context (4096 tokens)
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
import httpx
import numpy as np
import pandas as pd
import joblib

from datetime import datetime, timezone
from src.mitra.datastore import FarmDataStore

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "gpt4o-s:20b")

CROP_MODEL_DIR  = "models/crop_detection"
FERT_MODEL_PATH = "models/fertilizer_optimization/master_ag_model.pkl"


# ─────────────────────────────────────────────────────────────────────────
# VRAM Manager — clears GPU memory between model phases
# ─────────────────────────────────────────────────────────────────────────
class VRAMManager:
    """Manages GPU memory for systems with limited VRAM (8GB)."""

    @staticmethod
    def clear_gpu():
        """Force-clear all GPU memory so the next model can load."""
        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
                allocated = torch.cuda.memory_allocated() / 1024**2
                log.info("  GPU memory cleared. Allocated: %.1f MB", allocated)
        except ImportError:
            pass  # No torch = CPU-only XGBoost, no VRAM to manage

    @staticmethod
    def get_gpu_status() -> dict:
        try:
            import torch
            if torch.cuda.is_available():
                return {
                    "gpu_available": True,
                    "gpu_name": torch.cuda.get_device_name(0),
                    "allocated_mb": round(torch.cuda.memory_allocated() / 1024**2, 1),
                    "reserved_mb": round(torch.cuda.memory_reserved() / 1024**2, 1),
                }
        except ImportError:
            pass
        return {"gpu_available": False}


# ─────────────────────────────────────────────────────────────────────────
# THE ORCHESTRATOR
# ─────────────────────────────────────────────────────────────────────────
class MitraOrchestrator:
    """
    Central brain of SmartAgri. Accepts user text, live sensors,
    and optional image bytes. Orchestrates all models with VRAM-aware
    phased loading, queries the LLM, and persists everything to SQLite.
    """

    def __init__(self):
        self.vram = VRAMManager()
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

        # Ollama HTTP client
        self.llm_client = httpx.Client(timeout=180.0)

        log.info("MitraOrchestrator initialised.")

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
            self.vram.clear_gpu()
            log.info("Vision predictor unloaded, VRAM freed.")

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
        log.info("[Phase A] VRAM clear -> loading Vision AI...")
        self.vram.clear_gpu()

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
            # Always unload vision after use to free VRAM for LLM
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
    # Phase D: LLM Call (Ollama gpt4o-s:20b)
    # ─────────────────────────────────────────────────────────────────────
    def _call_llm(self, system_prompt: str, user_message: str) -> dict:
        """
        Calls Ollama with strict memory constraints:
          - num_ctx: 4096 (fits in 8GB VRAM with 20B model at Q4)
          - num_predict: 512 (limit output length)
          - temperature: 0.4 (factual, low hallucination)
        """
        log.info("[Phase D] VRAM clear -> calling Ollama %s...", OLLAMA_MODEL)
        self.vram.clear_gpu()

        payload = {
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.4,
                "num_ctx": 4096,
                "num_predict": 512,
                "num_gpu": 99,       # offload all layers to GPU
                "num_thread": 8,     # use 8 CPU threads for prompt eval
            },
        }

        try:
            resp = self.llm_client.post(
                f"{OLLAMA_BASE_URL}/api/chat", json=payload
            )
            resp.raise_for_status()
            content = resp.json().get("message", {}).get("content", "{}")
            parsed = json.loads(content)
            return {
                "farmer_response": parsed.get("farmer_response",
                    "I could not process your request right now."),
                "user_notes": parsed.get("user_notes"),
                "profile_updates": parsed.get("profile_updates"),
            }
        except json.JSONDecodeError:
            log.warning("LLM returned non-JSON, using raw text.")
            return {"farmer_response": content or "Processing error.",
                    "user_notes": None, "profile_updates": None}
        except Exception as e:
            log.error("Ollama call failed: %s", e)
            return {
                "farmer_response": (
                    "I'm having trouble connecting to my brain right now. "
                    "Please check that Ollama is running: ollama serve"
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
3. Keep responses concise (2-4 sentences for simple questions).
4. You MUST respond in this exact JSON format:
{{
  "farmer_response": "Your helpful answer...",
  "user_notes": "any NEW fact the user mentioned" or null,
  "profile_updates": {{"key": "value"}} or null
}}

5. Set "user_notes" ONLY if the user reveals something NEW (e.g. "I watered today", "my land is 5 acres").
6. Set "profile_updates" ONLY if the user mentions a PERSISTENT fact:
   - land_size_acres, irrigation_type, region, preferred_language
   - Example: user says "I have 3 acres" -> {{"land_size_acres": "3"}}
   - If the user just asks a question, set BOTH to null.

=== USER PROFILE ===
{profile_text}

=== FARM HISTORY (last 5 interactions) ===
{history_text}

=== CURRENT SESSION ===
Current Crop: {current_crop}
AI Recommended Crop: {recommended_crop} (confidence: {crop_confidence:.0%})
Soil Type: {soil_type}
Days Since Planting: {days}

LIVE SENSORS:
{sensor_text}

{disease_sec}
FERTILIZER AI (model output):
{fert_text}
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
        history_text = self.datastore.format_history_for_llm(n=5)
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

        # ── Phase D: LLM (clear VRAM first, then call Ollama) ────────
        log.info("[Phase D] Building prompt -> calling LLM...")
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
