"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  PHASE 2 — Fault-Tolerant Multi-Output Training Pipeline                    ║
║  SmartAgri · XGBoostRegressor × MultiOutputRegressor                        ║
╚══════════════════════════════════════════════════════════════════════════════╝

Loads engineered_training_data.csv, builds a sklearn Pipeline with
ColumnTransformer (OHE for crops, passthrough for sensors with NaN),
trains XGBRegressor wrapped in MultiOutputRegressor, evaluates,
and saves as master_ag_model.pkl.

XGBoost handles NaN natively — no imputation needed for sensor faults.

RUN:  python model_trainer.py
"""

import os
import time
import warnings
import logging
import json

import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.multioutput import MultiOutputRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (mean_absolute_error, mean_squared_error,
                             r2_score)

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
INPUT_PATH    = "data/processed/engineered_training_data.csv"
MODEL_PATH    = "models/fertilizer_optimization/master_ag_model.pkl"
ARTIFACTS_DIR = "models/fertilizer_optimization/artifacts"
RANDOM_STATE  = 42
TEST_SIZE     = 0.20

# We use OneHotEncoder for these, handling unseen categories gracefully
CATEGORICAL_FEATURES = ["Current_Crop", "Recommended_Crop", "Soil_Type"]
NUMERIC_FEATURES     = [
    "Days_Since_Planting",
    "N", "P", "K", "temperature", "humidity", "ph", "rainfall",
    "N_P_ratio", "N_K_ratio", "P_K_ratio",
    "THI", "water_availability", "pH_stress",
]
ALL_FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES

TARGETS = [
    "Deficit_N", "Deficit_P", "Deficit_K", "Soil_Health_Score",
    "Water_Requirement_Index", "pH_Adjustment_Required", 
    "Temperature_Stress_Score", "Fertilizer_Urgency_Score", 
    "Planting_Readiness_Score"
]

os.makedirs(ARTIFACTS_DIR, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# GPU DETECTION (reused from train_model.py)
# ─────────────────────────────────────────────────────────────────────────────
def detect_gpu() -> dict:
    try:
        import subprocess
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name",
             "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            gpu_name = result.stdout.strip().split("\n")[0].strip()
            log.info(f"✅  GPU detected: {gpu_name}")
            return {"tree_method": "hist", "device": "cuda"}
    except Exception:
        pass

    import multiprocessing
    n_cpu = multiprocessing.cpu_count()
    log.info(f"⚠️  No GPU — CPU mode ({n_cpu} threads)")
    return {"tree_method": "hist", "device": "cpu", "n_jobs": n_cpu}


# ─────────────────────────────────────────────────────────────────────────────
# BUILD PIPELINE
# ─────────────────────────────────────────────────────────────────────────────
def build_pipeline(gpu_cfg: dict) -> Pipeline:
    """
    Builds a fault-tolerant sklearn Pipeline:
      1. ColumnTransformer: OHE for crop names, passthrough for numerics (NaN-safe)
      2. MultiOutputRegressor wrapping XGBRegressor

    XGBoost handles NaN natively via its tree-splitting algorithm, so we
    intentionally do NOT impute missing sensor values — the model learns
    which direction to send missing-value samples at each split.
    """
    from xgboost import XGBRegressor

    # OHE for categorical, passthrough for numeric (preserves NaN for XGB)
    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False),
             CATEGORICAL_FEATURES),
            ("num", "passthrough", NUMERIC_FEATURES),
        ],
        remainder="drop"
    )

    # XGBoost base estimator with strong defaults
    xgb_params = {
        "n_estimators":      500,
        "learning_rate":     0.05,
        "max_depth":         8,
        "min_child_weight":  3,
        "subsample":         0.8,
        "colsample_bytree":  0.8,
        "reg_alpha":         0.1,
        "reg_lambda":        1.5,
        "gamma":             0.05,
        "random_state":      RANDOM_STATE,
        "verbosity":         0,
        **gpu_cfg,
    }

    base_regressor = XGBRegressor(**xgb_params)
    multi_regressor = MultiOutputRegressor(base_regressor, n_jobs=1)

    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("regressor",    multi_regressor),
    ])

    return pipeline


# ─────────────────────────────────────────────────────────────────────────────
# EVALUATION
# ─────────────────────────────────────────────────────────────────────────────
def evaluate(pipeline, X_test, y_test) -> dict:
    y_pred = pipeline.predict(X_test)

    metrics = {}
    print(f"\n{'═'*65}")
    print(f"  {'Target':<22} {'MAE':>8} {'RMSE':>8} {'R²':>8}")
    print(f"{'─'*65}")

    for i, target in enumerate(TARGETS):
        y_true_col = y_test.iloc[:, i].values
        y_pred_col = y_pred[:, i]

        mae  = mean_absolute_error(y_true_col, y_pred_col)
        rmse = np.sqrt(mean_squared_error(y_true_col, y_pred_col))
        r2   = r2_score(y_true_col, y_pred_col)

        metrics[target] = {"MAE": round(mae, 4), "RMSE": round(rmse, 4), "R2": round(r2, 4)}
        print(f"  {target:<22} {mae:>8.3f} {rmse:>8.3f} {r2:>8.4f}")

    print(f"{'═'*65}\n")
    return metrics


def plot_predictions(pipeline, X_test, y_test):
    """Plots actual vs predicted for each target."""
    y_pred = pipeline.predict(X_test)

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes = axes.ravel()

    for i, (target, ax) in enumerate(zip(TARGETS, axes)):
        y_true = y_test.iloc[:, i].values
        y_p    = y_pred[:, i]

        ax.scatter(y_true, y_p, alpha=0.3, s=10, color="#2563EB")
        lims = [min(y_true.min(), y_p.min()), max(y_true.max(), y_p.max())]
        ax.plot(lims, lims, "r--", linewidth=1.5, label="Perfect")
        ax.set_xlabel("Actual", fontsize=10)
        ax.set_ylabel("Predicted", fontsize=10)
        ax.set_title(f"{target}  (R²={r2_score(y_true, y_p):.4f})", fontsize=11)
        ax.legend()

    plt.suptitle("Multi-Output Regression — Actual vs Predicted", fontsize=14, fontweight="bold")
    plt.tight_layout()
    out = os.path.join(ARTIFACTS_DIR, "actual_vs_predicted.png")
    plt.savefig(out, dpi=150)
    plt.close()
    log.info(f"  📊  Saved predictions plot → {out}")


def plot_feature_importance(pipeline):
    """Extracts and plots average feature importance across all outputs."""
    preprocessor = pipeline.named_steps["preprocessor"]
    regressor    = pipeline.named_steps["regressor"]

    # Get feature names from the preprocessor
    cat_features = list(preprocessor.transformers_[0][1].get_feature_names_out(CATEGORICAL_FEATURES))
    all_features = cat_features + NUMERIC_FEATURES

    # Average importance across all 4 output regressors
    importances = np.zeros(len(all_features))
    for estimator in regressor.estimators_:
        importances += estimator.feature_importances_

    importances /= len(regressor.estimators_)

    # Plot top 20
    idx = np.argsort(importances)[-20:]
    fig, ax = plt.subplots(figsize=(10, 8))
    bars = ax.barh(np.array(all_features)[idx], importances[idx],
                   color="#10B981", edgecolor="white", linewidth=0.5)
    ax.set_xlabel("Average Gain Importance", fontsize=11)
    ax.set_title("Top 20 Features — Multi-Output Regression", fontsize=13)
    ax.bar_label(bars, labels=[f"{v:.4f}" for v in importances[idx]],
                 padding=3, fontsize=8)
    plt.tight_layout()
    out = os.path.join(ARTIFACTS_DIR, "feature_importance_regression.png")
    plt.savefig(out, dpi=150)
    plt.close()
    log.info(f"  📊  Saved feature importance → {out}")


# ─────────────────────────────────────────────────────────────────────────────
# NaN FAULT ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────
def report_fault_resilience(df):
    """Reports how the dataset's NaN faults are distributed."""
    sensor_nans = df[["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]].isna()
    total   = sensor_nans.size
    faults  = sensor_nans.sum().sum()
    per_row = sensor_nans.sum(axis=1)

    log.info(f"  🛡️  Fault Analysis:")
    log.info(f"     Total sensor cells : {total:,}")
    log.info(f"     Faulty cells       : {faults:,} ({faults/total*100:.1f}%)")
    log.info(f"     Rows with ≥1 fault : {(per_row > 0).sum():,} ({(per_row > 0).mean()*100:.1f}%)")
    log.info(f"     Max faults/row     : {per_row.max()}")
    log.info(f"  ℹ️  XGBoost handles these NaN values natively — no imputation used.")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    t0 = time.time()
    log.info("╔═══════════════════════════════════════════════════════╗")
    log.info("║  Phase 2 — Fault-Tolerant Training Pipeline          ║")
    log.info("╚═══════════════════════════════════════════════════════╝")

    # ── GPU detection ─────────────────────────────────────────────────────
    gpu_cfg = detect_gpu()

    # ── Load data ─────────────────────────────────────────────────────────
    log.info(f"📂  Loading {INPUT_PATH} …")
    df = pd.read_csv(INPUT_PATH)
    log.info(f"  Shape: {df.shape}")

    # Validate columns
    missing_feat = [c for c in ALL_FEATURES if c not in df.columns]
    missing_tgt  = [c for c in TARGETS     if c not in df.columns]
    if missing_feat:
        raise ValueError(f"Missing features: {missing_feat}")
    if missing_tgt:
        raise ValueError(f"Missing targets: {missing_tgt}")

    # ── Report fault distribution ─────────────────────────────────────────
    report_fault_resilience(df)

    # ── Split ─────────────────────────────────────────────────────────────
    X = df[ALL_FEATURES]
    y = df[TARGETS]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )
    log.info(f"  Train: {len(X_train):,}   Test: {len(X_test):,}")

    # ── Build & train pipeline ────────────────────────────────────────────
    log.info("🔧  Building pipeline (OHE + MultiOutput × XGBRegressor) …")
    pipeline = build_pipeline(gpu_cfg)

    log.info("🚀  Training …")
    pipeline.fit(X_train, y_train)

    # ── Evaluate ──────────────────────────────────────────────────────────
    log.info("📊  Evaluating on held-out test set …")
    metrics = evaluate(pipeline, X_test, y_test)

    # ── Plots ─────────────────────────────────────────────────────────────
    plot_predictions(pipeline, X_test, y_test)
    plot_feature_importance(pipeline)

    # ── Save ──────────────────────────────────────────────────────────────
    log.info(f"💾  Saving pipeline → {MODEL_PATH}")
    joblib.dump(pipeline, MODEL_PATH)

    # Save metadata
    meta = {
        "features":     ALL_FEATURES,
        "targets":      TARGETS,
        "categorical":  CATEGORICAL_FEATURES,
        "numeric":      NUMERIC_FEATURES,
        "test_metrics": metrics,
        "test_size":    TEST_SIZE,
        "trained_at":   time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    meta_path = os.path.join(ARTIFACTS_DIR, "regression_metadata.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    elapsed = time.time() - t0
    log.info(f"\n⏱️  Training time: {elapsed:.1f}s")
    log.info(f"💾  Model saved  : {MODEL_PATH}")
    log.info(f"📁  Artifacts    : {ARTIFACTS_DIR}/")
    log.info("✅  Phase 2 complete.")


if __name__ == "__main__":
    main()
