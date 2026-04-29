"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  MASTER TEST SCRIPT — SmartAgriCulture                                      ║
║  Runs both Crop Detection and Fertilizer Optimization models sequentially.   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import warnings
import pandas as pd
import numpy as np
import joblib

# Suppress sklearn/xgboost warnings for clean output
warnings.filterwarnings("ignore")

# Import the inference advisor from the fertilizer optimization module
from src.fertilizer_optimization.inference import AgriAdvisor

CROP_MODEL_DIR = "models/crop_detection"

def load_crop_detection_model():
    """Loads the Crop Detection artifacts."""
    model_path   = os.path.join(CROP_MODEL_DIR, "xgb_crop_model.pkl")
    scaler_path  = os.path.join(CROP_MODEL_DIR, "scaler.pkl")
    encoder_path = os.path.join(CROP_MODEL_DIR, "label_encoder.pkl")
    
    if not os.path.exists(model_path):
        print(f"[ERROR] Crop Detection model not found at {model_path}.")
        print("Please run `run_crop_detection.bat` first.")
        sys.exit(1)
        
    model  = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    le     = joblib.load(encoder_path)
    return model, scaler, le

def feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    """Applies necessary derived features for the Crop Detection model."""
    df = df.copy()
    df["N_P_ratio"]          = df["N"]  / (df["P"]  + 1e-5)
    df["N_K_ratio"]          = df["N"]  / (df["K"]  + 1e-5)
    df["P_K_ratio"]          = df["P"]  / (df["K"]  + 1e-5)
    df["THI"]                = df["temperature"] * df["humidity"]
    df["water_availability"] = df["rainfall"] * (df["humidity"] / 100.0)
    df["pH_stress"]          = np.abs(df["ph"] - 6.5)
    return df

def preprocess_live_data_crop(live_payload: dict) -> pd.DataFrame:
    """Preprocesses a raw sensor dictionary for the Crop Detection model."""
    FEATURE_COLS = [
        "N", "P", "K", "temperature", "humidity", "ph", "rainfall",
        "N_P_ratio", "N_K_ratio", "P_K_ratio",
        "THI", "water_availability", "pH_stress"
    ]
    DEFAULTS = {
        "N": 50.0, "P": 50.0, "K": 50.0,
        "temperature": 25.0, "humidity": 60.0,
        "ph": 6.5, "rainfall": 100.0
    }
    payload = dict(live_payload)
    if "humidity" not in payload and "Moisture" in payload:
        payload["humidity"] = float(payload["Moisture"])
    for key, val in DEFAULTS.items():
        payload.setdefault(key, val)
    df = pd.DataFrame([payload])
    df = feature_engineering(df)
    return df[FEATURE_COLS]


def run_demo():
    print("="*70)
    print("   SmartAgri AI — Master Test Suite")
    print("="*70 + "\n")
    
    print("[1/2] Loading Crop Detection Model...")
    crop_model, crop_scaler, crop_le = load_crop_detection_model()
    
    print("[2/2] Loading Fertilizer Optimization Model...")
    try:
        advisor = AgriAdvisor()
    except FileNotFoundError:
        print("[ERROR] Fertilizer Optimization model not found.")
        print("Please run `run_fertilizer_optimization.bat` first.")
        sys.exit(1)
        
    print("\n[OK] Both models loaded successfully.\n")

    # Define realistic sample datasets
    sample_payloads = [
        {
            "description": "High Moisture, Low N (Rice conditions)",
            "current_crop": "maize",
            "soil_type": "clay",
            "days_growing": 40,
            "sensor_data": {
                "N": 65.0, "P": 42.0, "K": 43.0, 
                "temperature": 23.0, "humidity": 82.0, 
                "ph": 6.2, "rainfall": 250.0
            }
        },
        {
            "description": "Dry Season, High Temp (Cotton conditions)",
            "current_crop": "cotton",
            "soil_type": "yellow",
            "days_growing": 80,
            "sensor_data": {
                "N": 118.0, "P": 46.0, "K": 20.0, 
                "temperature": 28.0, "humidity": 45.0, 
                "ph": 7.0, "rainfall": 80.0
            }
        },
        {
            "description": "Minimal Sensor Data (Hardware failure simulation)",
            "current_crop": "banana",
            "soil_type": "red",
            "days_growing": 110,
            "sensor_data": {
                "N": 40.0, "P": 50.0, "K": 60.0
                # Missing temp, humidity, pH, rainfall
            }
        }
    ]

    for i, scenario in enumerate(sample_payloads):
        print("="*70)
        print(f"  TEST SCENARIO {i+1}: {scenario['description']}")
        print("="*70)
        
        sensor_data = scenario["sensor_data"]
        current_crop = scenario["current_crop"]
        soil_type = scenario["soil_type"]
        days_growing = scenario["days_growing"]
        
        # --- MODEL 1: CROP DETECTION ---
        print("\n>>> RUNNING MODEL 1: Crop Detection")
        X_crop = preprocess_live_data_crop(sensor_data)
        X_scaled = crop_scaler.transform(X_crop.values)
        
        pred_idx = crop_model.predict(X_scaled)[0]
        pred_proba = crop_model.predict_proba(X_scaled)[0]
        recommended_crop = crop_le.inverse_transform([pred_idx])[0]
        confidence = pred_proba[pred_idx] * 100
        
        print(f"   => Predicted Best Crop : [{recommended_crop.upper()}]")
        print(f"   => AI Confidence       : {confidence:.2f}%")
        
        # --- MODEL 2: FERTILIZER OPTIMIZATION ---
        print(f"\n>>> RUNNING MODEL 2: Fertilizer Optimization (using detected crop '{recommended_crop}')")
        report = advisor.generate_report(
            current_crop=current_crop,
            recommended_crop=recommended_crop,
            soil_type=soil_type,
            days_growing=days_growing,
            sensor_data=sensor_data
        )
        print(report)
        print("\n")

if __name__ == "__main__":
    run_demo()
