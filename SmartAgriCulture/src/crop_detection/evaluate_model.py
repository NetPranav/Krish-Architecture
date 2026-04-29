"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   SmartAgri · Crop Recommendation Engine — EVALUATION & TESTING             ║
║   Run AFTER train_model.py has completed.                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝

WHAT THIS SCRIPT DOES:
  1. Loads the saved model + scaler + encoder from model_artifacts/
  2. Runs a full evaluation on test.csv (the held-out test set)
  3. Prints a rich classification report + per-class accuracy table
  4. Simulates 5 live ESP32 sensor payloads to prove the backend pipeline works
  5. Stress-tests the model with edge-case inputs

RUN:
  python evaluate_model.py
"""

import os
import json
import warnings
import logging

import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.metrics import (accuracy_score, f1_score, classification_report,
                             balanced_accuracy_score, confusion_matrix)

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

MODEL_DIR    = "models/crop_detection"
TEST_CSV     = "data/processed/test.csv"
FEATURE_COLS = [
    "N", "P", "K", "temperature", "humidity", "ph", "rainfall",
    "N_P_ratio", "N_K_ratio", "P_K_ratio",
    "THI", "water_availability", "pH_stress"
]
TARGET_COL = "label"


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS — replicated here so this file is self-contained for the backend
# ─────────────────────────────────────────────────────────────────────────────
def feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["N_P_ratio"]          = df["N"]  / (df["P"]  + 1e-5)
    df["N_K_ratio"]          = df["N"]  / (df["K"]  + 1e-5)
    df["P_K_ratio"]          = df["P"]  / (df["K"]  + 1e-5)
    df["THI"]                = df["temperature"] * df["humidity"]
    df["water_availability"] = df["rainfall"] * (df["humidity"] / 100.0)
    df["pH_stress"]          = np.abs(df["ph"] - 6.5)
    return df


def preprocess_live_data(live_payload: dict) -> pd.DataFrame:
    """Exact same function as in train_model.py — single source of truth."""
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


# ─────────────────────────────────────────────────────────────────────────────
# 1. LOAD ARTIFACTS
# ─────────────────────────────────────────────────────────────────────────────
def load_artifacts():
    model_path   = os.path.join(MODEL_DIR, "xgb_crop_model.pkl")
    scaler_path  = os.path.join(MODEL_DIR, "scaler.pkl")
    encoder_path = os.path.join(MODEL_DIR, "label_encoder.pkl")
    meta_path    = os.path.join(MODEL_DIR, "model_metadata.json")

    for p in [model_path, scaler_path, encoder_path]:
        if not os.path.exists(p):
            raise FileNotFoundError(
                f"Artifact not found: {p}\n"
                "Please run  python train_model.py  first."
            )

    model  = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    le     = joblib.load(encoder_path)

    with open(meta_path) as f:
        meta = json.load(f)

    log.info(f"✅  Model loaded — {meta['num_classes']} classes")
    log.info(f"    Trained at : {meta.get('trained_at', 'unknown')}")
    log.info(f"    Train acc  : {meta['test_metrics'].get('accuracy', '?')}")
    return model, scaler, le, meta


# ─────────────────────────────────────────────────────────────────────────────
# 2. FULL TEST SET EVALUATION
# ─────────────────────────────────────────────────────────────────────────────
def evaluate_on_test_csv(model, scaler, le):
    if not os.path.exists(TEST_CSV):
        log.warning(f"⚠️  {TEST_CSV} not found. Run train_model.py first.")
        return

    log.info(f"\n{'═'*60}")
    log.info(f"  EVALUATION ON HELD-OUT TEST SET  ({TEST_CSV})")
    log.info(f"{'═'*60}")

    df = pd.read_csv(TEST_CSV)

    # Re-apply feature engineering in case any derived cols are missing
    missing_fe = [c for c in FEATURE_COLS if c not in df.columns]
    if missing_fe:
        df = feature_engineering(df)

    X_raw = df[FEATURE_COLS].values
    y_raw = df[TARGET_COL].values

    # Scale + encode
    X     = scaler.transform(X_raw)
    y     = le.transform(y_raw)

    # Predict
    y_pred      = model.predict(X)
    y_pred_prob = model.predict_proba(X)

    # ── Core Metrics ──────────────────────────────────────────────────────
    acc          = accuracy_score(y, y_pred)
    bal_acc      = balanced_accuracy_score(y, y_pred)
    f1_macro     = f1_score(y, y_pred, average="macro")
    f1_weighted  = f1_score(y, y_pred, average="weighted")

    top3_correct = _top_k_accuracy(y, y_pred_prob, k=3)
    top5_correct = _top_k_accuracy(y, y_pred_prob, k=5)

    print(f"""
┌────────────────────────────────────────────────────────┐
│           SMARTAGRI MODEL ACCURACY REPORT              │
├────────────────────────────────────────────────────────┤
│  Test rows evaluated  : {len(y):>8,}                      │
│  Unique crop classes  : {len(le.classes_):>8}                      │
├────────────────────────────────────────────────────────┤
│  Top-1 Accuracy       : {acc*100:>8.4f} %                  │
│  Top-3 Accuracy       : {top3_correct*100:>8.4f} %                  │
│  Top-5 Accuracy       : {top5_correct*100:>8.4f} %                  │
│  Balanced Accuracy    : {bal_acc*100:>8.4f} %                  │
│  F1 Score (Macro)     : {f1_macro*100:>8.4f} %                  │
│  F1 Score (Weighted)  : {f1_weighted*100:>8.4f} %                  │
└────────────────────────────────────────────────────────┘
""")

    # ── Per-class accuracy table ─────────────────────────────────────────
    print("\n── PER-CLASS ACCURACY ──────────────────────────────────────────")
    print(f"{'Crop':<20} {'Correct':>8} {'Total':>8} {'Accuracy':>10}")
    print("─" * 50)
    for cls_idx, cls_name in enumerate(le.classes_):
        mask      = (y == cls_idx)
        total     = mask.sum()
        correct   = (y_pred[mask] == cls_idx).sum()
        pct       = correct / total * 100 if total > 0 else 0.0
        bar       = "█" * int(pct / 5)
        print(f"{cls_name:<20} {correct:>8} {total:>8} {pct:>9.2f}%  {bar}")
    print()

    # Full sklearn report
    print("── SKLEARN CLASSIFICATION REPORT ───────────────────────────────")
    print(classification_report(y, y_pred, target_names=le.classes_))

    # Save per-class csv
    rows = []
    for cls_idx, cls_name in enumerate(le.classes_):
        mask    = (y == cls_idx)
        total   = mask.sum()
        correct = (y_pred[mask] == cls_idx).sum()
        rows.append({"crop": cls_name,
                     "correct": int(correct),
                     "total":   int(total),
                     "accuracy": round(correct/total*100 if total else 0, 4)})
    pd.DataFrame(rows).to_csv(
        os.path.join(MODEL_DIR, "per_class_accuracy.csv"), index=False
    )
    log.info(f"  Saved per-class CSV → {MODEL_DIR}/per_class_accuracy.csv")

    return acc


def _top_k_accuracy(y_true, y_proba, k):
    top_k = np.argsort(y_proba, axis=1)[:, -k:]
    correct = sum(y_true[i] in top_k[i] for i in range(len(y_true)))
    return correct / len(y_true)


# ─────────────────────────────────────────────────────────────────────────────
# 3. LIVE ESP32 SIMULATION
# ─────────────────────────────────────────────────────────────────────────────
def simulate_esp32_predictions(model, scaler, le):
    """
    Simulates 5 realistic sensor readings from an ESP32 field device.
    This proves the end-to-end backend pipeline works correctly.
    """
    log.info(f"\n{'═'*60}")
    log.info("  LIVE ESP32 SENSOR SIMULATION")
    log.info(f"{'═'*60}")

    # Realistic test payloads (N, P, K, Moisture — as ESP32 sends them)
    test_payloads = [
        # Expected → rice
        {"N": 90, "P": 42, "K": 43, "Moisture": 82.0,
         "temperature": 23.0, "ph": 6.2, "rainfall": 250.0,
         "description": "Wet paddy field (expected: rice)"},

        # Expected → maize
        {"N": 75, "P": 67, "K": 67, "Moisture": 65.0,
         "temperature": 22.0, "ph": 5.8, "rainfall": 60.0,
         "description": "Dry season maize plot (expected: maize)"},

        # Expected → cotton
        {"N": 118, "P": 46, "K": 20, "Moisture": 80.0,
         "temperature": 25.0, "ph": 7.0, "rainfall": 80.0,
         "description": "Black soil cotton plot (expected: cotton)"},

        # Expected → mungbean
        {"N": 20, "P": 40, "K": 20, "Moisture": 85.0,
         "temperature": 28.0, "ph": 6.9, "rainfall": 50.0,
         "description": "Legume test plot (expected: mungbean)"},

        # Minimal — only 4 params (real worst-case ESP32 scenario)
        {"N": 60, "P": 55, "K": 44, "Moisture": 72.0,
         "description": "Minimal payload — 4 params only"},
    ]

    print(f"\n{'─'*70}")
    print(f"  {'#':<3} {'Description':<42} {'Prediction':<15} {'Confidence'}")
    print(f"{'─'*70}")

    for i, payload in enumerate(test_payloads):
        desc    = payload.pop("description")
        X_live  = preprocess_live_data(payload)
        X_scaled = scaler.transform(X_live.values)

        pred_idx  = model.predict(X_scaled)[0]
        pred_proba = model.predict_proba(X_scaled)[0]
        crop_name  = le.inverse_transform([pred_idx])[0]
        confidence = pred_proba[pred_idx] * 100

        # Top-3 alternatives
        top3_idx  = np.argsort(pred_proba)[::-1][:3]
        top3      = [(le.classes_[j], round(pred_proba[j]*100, 2))
                     for j in top3_idx]

        print(f"  {i+1:<3} {desc[:40]:<42} {crop_name:<15} {confidence:.2f}%")
        print(f"       Top-3: {top3}")
        print()

    print(f"{'─'*70}\n")


# ─────────────────────────────────────────────────────────────────────────────
# 4. EDGE-CASE STRESS TEST
# ─────────────────────────────────────────────────────────────────────────────
def stress_test(model, scaler, le):
    log.info(f"{'═'*60}")
    log.info("  EDGE-CASE STRESS TEST")
    log.info(f"{'═'*60}")

    edge_cases = [
        {"N": 0,   "P": 0,   "K": 0,   "Moisture": 0,   "temperature": 0,  "ph": 3.5, "rainfall": 0},
        {"N": 200, "P": 200, "K": 250, "Moisture": 100, "temperature": 55, "ph": 9.5, "rainfall": 500},
        {"N": 50,  "P": 50,  "K": 50,  "Moisture": 50,  "temperature": 25, "ph": 7.0, "rainfall": 100},
    ]
    labels = ["All-zero inputs", "All-max inputs", "Neutral inputs"]

    print(f"\n{'─'*55}")
    print(f"  {'Edge Case':<25} {'Prediction':<18} {'Confidence'}")
    print(f"{'─'*55}")
    all_ok = True
    for case, lbl in zip(edge_cases, labels):
        try:
            X     = preprocess_live_data(case)
            Xs    = scaler.transform(X.values)
            pred  = model.predict(Xs)[0]
            prob  = model.predict_proba(Xs)[0]
            crop  = le.inverse_transform([pred])[0]
            conf  = prob[pred] * 100
            print(f"  {lbl:<25} {crop:<18} {conf:.2f}%")
        except Exception as e:
            print(f"  {lbl:<25} ❌ ERROR: {e}")
            all_ok = False
    print(f"{'─'*55}")
    if all_ok:
        log.info("✅  All edge cases handled without errors.")
    else:
        log.warning("⚠️  Some edge cases failed — review above.")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("\n" + "═"*60)
    print("   SmartAgri · Model Evaluation & Testing Suite")
    print("═"*60 + "\n")

    model, scaler, le, meta = load_artifacts()

    # 1. Full held-out evaluation
    evaluate_on_test_csv(model, scaler, le)

    # 2. Live ESP32 simulation
    simulate_esp32_predictions(model, scaler, le)

    # 3. Edge-case stress test
    stress_test(model, scaler, le)

    print("\n✅  Evaluation complete.\n")


if __name__ == "__main__":
    main()
