"""
╔══════════════════════════════════════════════════════════════════════════════╗
║      SmartAgri · Crop Recommendation Engine — TRAINING PIPELINE             ║
║      GPU-Accelerated XGBoost + Optuna HPO + StratifiedKFold + SHAP          ║
╚══════════════════════════════════════════════════════════════════════════════╝

FEATURES:
  ✅ Smart GPU detection with seamless CPU fallback
  ✅ Optuna Bayesian Hyperparameter Optimisation (200 trials)
  ✅ 10-fold Stratified Cross-Validation
  ✅ Feature Importance + SHAP explainability
  ✅ Full model serialization (model + scaler + encoder)
  ✅ Modular — backend can import preprocess_live_data() directly

RUN:
  python train_model.py
"""

import os
import sys
import time
import warnings
import logging

import numpy as np
import pandas as pd
import joblib
import json
import matplotlib
matplotlib.use("Agg")          # headless rendering — no display needed
import matplotlib.pyplot as plt

from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import (StratifiedKFold, train_test_split,
                                     cross_val_score)
from sklearn.metrics import (accuracy_score, f1_score, classification_report,
                             confusion_matrix, balanced_accuracy_score)

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
DATASET_PATH    = "data/processed/master_crop_dataset.csv"
MODEL_DIR       = "models/crop_detection"
TEST_SIZE       = 0.15          # 15 % held-out test set
CV_FOLDS        = 10            # StratifiedKFold folds
OPTUNA_TRIALS   = 0             # Set to 0 to use pre-computed optimal parameters
RANDOM_STATE    = 42
EARLY_STOP      = 40            # Early stopping rounds

FEATURE_COLS = [
    "N", "P", "K", "temperature", "humidity", "ph", "rainfall",
    "N_P_ratio", "N_K_ratio", "P_K_ratio",
    "THI", "water_availability", "pH_stress"
]
TARGET_COL = "label"

os.makedirs(MODEL_DIR, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# 1. GPU DETECTION
# ─────────────────────────────────────────────────────────────────────────────
def detect_gpu() -> dict:
    """
    Detects CUDA GPU and returns the best XGBoost device config.
    Falls back to CPU optimised multi-thread config automatically.
    """
    try:
        import subprocess
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version",
             "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            gpu_name = result.stdout.strip().split(",")[0].strip()
            log.info(f"✅  GPU detected: {gpu_name}")
            return {
                "tree_method": "hist",
                "device": "cuda",
            }
    except Exception:
        pass

    import multiprocessing
    n_cpu = multiprocessing.cpu_count()
    log.info(f"⚠️  No GPU found — using CPU ({n_cpu} threads)")
    return {
        "tree_method": "hist",
        "device": "cpu",
        "n_jobs": n_cpu,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 2. DATA LOADING & VALIDATION
# ─────────────────────────────────────────────────────────────────────────────
def load_and_validate(path: str) -> pd.DataFrame:
    log.info(f"📂  Loading dataset: {path}")
    df = pd.read_csv(path)

    # Validate required columns
    missing = [c for c in FEATURE_COLS + [TARGET_COL] if c not in df.columns]
    if missing:
        raise ValueError(f"Dataset missing columns: {missing}")

    # Drop rows with all-NaN features
    before = len(df)
    df = df.dropna(subset=FEATURE_COLS)
    dropped = before - len(df)
    if dropped:
        log.warning(f"  Dropped {dropped} rows with NaN features.")

    # Clip physical bounds to remove extreme outliers / sensor errors
    clip_rules = {
        "N":           (0, 200),
        "P":           (0, 200),
        "K":           (0, 250),
        "temperature": (-5, 55),
        "humidity":    (0, 100),
        "ph":          (3.0, 10.0),
        "rainfall":    (0, 500),
    }
    for col, (lo, hi) in clip_rules.items():
        if col in df.columns:
            df[col] = df[col].clip(lo, hi)

    log.info(f"  Dataset shape  : {df.shape}")
    log.info(f"  Unique classes : {df[TARGET_COL].nunique()}")
    log.info(f"  Class balance  :\n{df[TARGET_COL].value_counts().to_string()}")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 3. FEATURE ENGINEERING  (mirrored in fusion_pipeline.py — keep in sync!)
# ─────────────────────────────────────────────────────────────────────────────
def feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes derived features. Call this on raw 7-column sensor data too.
    """
    df = df.copy()
    df["N_P_ratio"]         = df["N"]  / (df["P"]  + 1e-5)
    df["N_K_ratio"]         = df["N"]  / (df["K"]  + 1e-5)
    df["P_K_ratio"]         = df["P"]  / (df["K"]  + 1e-5)
    df["THI"]               = df["temperature"] * df["humidity"]
    df["water_availability"] = df["rainfall"] * (df["humidity"] / 100.0)
    df["pH_stress"]         = np.abs(df["ph"] - 6.5)
    return df


def preprocess_live_data(live_payload: dict) -> pd.DataFrame:
    """
    ╔═══════════════════════════════════════════════════════════════╗
    ║  BACKEND INTEGRATION POINT — import this in your FastAPI/     ║
    ║  Django view and call it with the raw ESP32 sensor dict.      ║
    ╚═══════════════════════════════════════════════════════════════╝

    Input  : {'N': float, 'P': float, 'K': float, 'Moisture': float}
              (temperature / humidity / ph / rainfall are optional —
               fill from weather API or use intelligent defaults)
    Output : DataFrame with all 13 feature columns ready for model.predict()
    """
    DEFAULTS = {
        "N": 50.0, "P": 50.0, "K": 50.0,
        "temperature": 25.0, "humidity": 60.0,
        "ph": 6.5, "rainfall": 100.0
    }

    payload = dict(live_payload)                          # don't mutate caller's dict

    # Map ESP32 'Moisture' sensor → 'humidity' if humidity not sent separately
    if "humidity" not in payload and "Moisture" in payload:
        payload["humidity"] = float(payload["Moisture"])

    for key, default_val in DEFAULTS.items():
        payload.setdefault(key, default_val)

    df = pd.DataFrame([payload])
    df = feature_engineering(df)
    return df[FEATURE_COLS]


# ─────────────────────────────────────────────────────────────────────────────
# 4. OPTUNA HYPERPARAMETER OPTIMISATION
# ─────────────────────────────────────────────────────────────────────────────
def run_optuna(X_tr, y_tr, gpu_cfg: dict, n_trials: int = OPTUNA_TRIALS) -> dict:
    try:
        import optuna
        optuna.logging.set_verbosity(optuna.logging.WARNING)
    except ImportError:
        log.warning("Optuna not installed — skipping HPO, using strong defaults.")
        return _default_params(gpu_cfg)

    if n_trials == 0:
        log.info("Optuna trials set to 0 — Using discovered optimal parameters from previous 5-hour run.")
        return _default_params(gpu_cfg)

    log.info(f"🔍  Running Optuna HPO — {n_trials} trials …")

    from xgboost import XGBClassifier

    def objective(trial):
        params = {
            "n_estimators":       trial.suggest_int("n_estimators", 300, 1200),
            "learning_rate":      trial.suggest_float("learning_rate", 0.005, 0.15, log=True),
            "max_depth":          trial.suggest_int("max_depth", 4, 12),
            "min_child_weight":   trial.suggest_int("min_child_weight", 1, 10),
            "subsample":          trial.suggest_float("subsample", 0.5, 1.0),
            "colsample_bytree":   trial.suggest_float("colsample_bytree", 0.4, 1.0),
            "colsample_bylevel":  trial.suggest_float("colsample_bylevel", 0.4, 1.0),
            "reg_alpha":          trial.suggest_float("reg_alpha", 1e-4, 5.0, log=True),
            "reg_lambda":         trial.suggest_float("reg_lambda", 1e-4, 5.0, log=True),
            "gamma":              trial.suggest_float("gamma", 0.0, 2.0),
            "max_delta_step":     trial.suggest_int("max_delta_step", 0, 5),
            "eval_metric":        "mlogloss",
            "random_state":       RANDOM_STATE,
            "use_label_encoder":  False,
            **gpu_cfg,
        }
        model = XGBClassifier(**params, verbosity=0)
        skf   = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
        scores = cross_val_score(model, X_tr, y_tr, cv=skf,
                                 scoring="accuracy", n_jobs=1)
        return scores.mean()

    study = optuna.create_study(direction="maximize",
                                sampler=optuna.samplers.TPESampler(seed=RANDOM_STATE))
    study.optimize(objective, n_trials=n_trials, show_progress_bar=True)

    best = study.best_params
    log.info(f"  Best CV accuracy : {study.best_value*100:.4f}%")
    log.info(f"  Best params      : {best}")
    return {**best, "eval_metric": "mlogloss",
            "random_state": RANDOM_STATE, "use_label_encoder": False, **gpu_cfg}


def _default_params(gpu_cfg: dict) -> dict:
    """Strong hand-tuned defaults used when Optuna is not available."""
    return {
        "n_estimators":      693,
        "learning_rate":     0.07331953467711058,
        "max_depth":         6,
        "min_child_weight":  4,
        "subsample":         0.6380501334454864,
        "colsample_bytree":  0.40037380366227054,
        "colsample_bylevel": 0.9647202834048598,
        "reg_alpha":         0.0005632106806819862,
        "reg_lambda":        0.088157343607158,
        "gamma":             1.2294189563755327,
        "max_delta_step":    0,
        "eval_metric":       "mlogloss",
        "random_state":      RANDOM_STATE,
        "use_label_encoder": False,
        **gpu_cfg,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 5. CROSS-VALIDATION
# ─────────────────────────────────────────────────────────────────────────────
def run_cross_validation(X, y, best_params: dict) -> np.ndarray:
    from xgboost import XGBClassifier

    log.info(f"📊  Running {CV_FOLDS}-Fold Stratified Cross-Validation …")
    model = XGBClassifier(**best_params, verbosity=0)
    skf   = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    scores = cross_val_score(model, X, y, cv=skf, scoring="accuracy", n_jobs=1)

    log.info(f"  CV Accuracy  : {scores.mean()*100:.4f}% ± {scores.std()*100:.4f}%")
    log.info(f"  Per-fold     : {[f'{s*100:.2f}%' for s in scores]}")
    return scores


# ─────────────────────────────────────────────────────────────────────────────
# 6. FINAL TRAINING + EVALUATION
# ─────────────────────────────────────────────────────────────────────────────
def train_final_model(X_train, X_test, y_train, y_test,
                      best_params: dict, le: LabelEncoder,
                      scaler: StandardScaler):
    from xgboost import XGBClassifier

    log.info("🚀  Training final model on full training split …")

    # Build eval set for early stopping
    X_tr_sub, X_val, y_tr_sub, y_val = train_test_split(
        X_train, y_train, test_size=0.1, stratify=y_train, random_state=RANDOM_STATE
    )

    model = XGBClassifier(
        **best_params,
        early_stopping_rounds=EARLY_STOP,
        verbosity=1,
    )

    model.fit(
        X_tr_sub, y_tr_sub,
        eval_set=[(X_val, y_val)],
        verbose=50,
    )

    # ── Evaluation ──────────────────────────────────────────────────────────
    y_pred      = model.predict(X_test)
    acc         = accuracy_score(y_test, y_pred)
    balanced_acc = balanced_accuracy_score(y_test, y_pred)
    f1_macro    = f1_score(y_test, y_pred, average="macro")
    f1_weighted = f1_score(y_test, y_pred, average="weighted")

    log.info("═" * 60)
    log.info(f"  ✅  TEST ACCURACY        : {acc*100:.4f}%")
    log.info(f"  ✅  BALANCED ACCURACY    : {balanced_acc*100:.4f}%")
    log.info(f"  ✅  F1 MACRO             : {f1_macro*100:.4f}%")
    log.info(f"  ✅  F1 WEIGHTED          : {f1_weighted*100:.4f}%")
    log.info("═" * 60)

    # Full classification report
    label_names = le.classes_
    report      = classification_report(y_test, y_pred,
                                        target_names=label_names)
    print("\n" + report)

    # Save report
    with open(os.path.join(MODEL_DIR, "classification_report.txt"), "w") as f:
        f.write(report)

    # ── Confusion Matrix Plot ────────────────────────────────────────────────
    _plot_confusion_matrix(y_test, y_pred, label_names)

    # ── Feature Importance Plot ──────────────────────────────────────────────
    _plot_feature_importance(model)

    # ── SHAP (optional) ─────────────────────────────────────────────────────
    _compute_shap(model, X_test, label_names)

    return model, {
        "accuracy":         round(acc, 6),
        "balanced_accuracy": round(balanced_acc, 6),
        "f1_macro":         round(f1_macro, 6),
        "f1_weighted":      round(f1_weighted, 6),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 7. PLOTTING HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _plot_confusion_matrix(y_true, y_pred, label_names):
    cm   = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots(figsize=(max(10, len(label_names)), max(8, len(label_names)-2)))
    im = ax.imshow(cm, interpolation="nearest", cmap="Blues")
    plt.colorbar(im, ax=ax)

    ax.set_xticks(range(len(label_names)))
    ax.set_yticks(range(len(label_names)))
    ax.set_xticklabels(label_names, rotation=45, ha="right", fontsize=8)
    ax.set_yticklabels(label_names, fontsize=8)

    thresh = cm.max() / 2.0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, format(cm[i, j], "d"),
                    ha="center", va="center", fontsize=6,
                    color="white" if cm[i, j] > thresh else "black")

    ax.set_xlabel("Predicted Label", fontsize=11)
    ax.set_ylabel("True Label",      fontsize=11)
    ax.set_title("Confusion Matrix — Crop Recommendation Engine", fontsize=13)
    plt.tight_layout()
    out = os.path.join(MODEL_DIR, "confusion_matrix.png")
    plt.savefig(out, dpi=150)
    plt.close()
    log.info(f"  📊  Saved confusion matrix → {out}")


def _plot_feature_importance(model):
    importance = model.feature_importances_
    fig, ax = plt.subplots(figsize=(10, 6))
    idx     = np.argsort(importance)
    bars    = ax.barh(np.array(FEATURE_COLS)[idx], importance[idx],
                      color="#2563EB", edgecolor="white", linewidth=0.5)
    ax.set_xlabel("XGBoost Gain Importance", fontsize=11)
    ax.set_title("Feature Importance — Crop Recommendation Engine", fontsize=13)
    ax.bar_label(bars, labels=[f"{v:.4f}" for v in importance[idx]],
                 padding=3, fontsize=8)
    plt.tight_layout()
    out = os.path.join(MODEL_DIR, "feature_importance.png")
    plt.savefig(out, dpi=150)
    plt.close()
    log.info(f"  📊  Saved feature importance → {out}")


def _compute_shap(model, X_test, label_names):
    try:
        import shap
        log.info("  🔬  Computing SHAP values …")
        explainer  = shap.TreeExplainer(model)
        shap_vals  = explainer.shap_values(X_test[:500])  # sample 500 for speed

        # Summary beeswarm (multi-class — use class 0 as representative)
        if isinstance(shap_vals, list):
            sv = shap_vals[0]
        elif len(shap_vals.shape) == 3:
            sv = shap_vals[:, :, 0]
        else:
            sv = shap_vals

        fig = plt.figure(figsize=(10, 7))
        shap.summary_plot(sv, X_test[:500],
                          feature_names=FEATURE_COLS,
                          show=False, max_display=13)
        plt.title("SHAP Feature Impact — Crop Recommendation Engine")
        plt.tight_layout()
        out = os.path.join(MODEL_DIR, "shap_summary.png")
        plt.savefig(out, dpi=150, bbox_inches="tight")
        plt.close()
        log.info(f"  📊  Saved SHAP summary → {out}")
    except ImportError:
        log.info("  ℹ️  SHAP not installed — skipping SHAP plots.")


# ─────────────────────────────────────────────────────────────────────────────
# 8. MODEL SERIALIZATION
# ─────────────────────────────────────────────────────────────────────────────
def save_artifacts(model, scaler: StandardScaler,
                   le: LabelEncoder, metrics: dict, best_params: dict):
    joblib.dump(model,  os.path.join(MODEL_DIR, "xgb_crop_model.pkl"))
    joblib.dump(scaler, os.path.join(MODEL_DIR, "scaler.pkl"))
    joblib.dump(le,     os.path.join(MODEL_DIR, "label_encoder.pkl"))

    # Also save model in native XGBoost format for fastest inference
    model.save_model(os.path.join(MODEL_DIR, "xgb_crop_model.json"))

    # Save metadata for the backend
    meta = {
        "feature_cols":   FEATURE_COLS,
        "target_col":     TARGET_COL,
        "num_classes":    len(le.classes_),
        "class_names":    list(le.classes_),
        "test_metrics":   metrics,
        "best_params":    {k: v for k, v in best_params.items()
                           if k not in ("device", "gpu_id", "n_jobs")},
        "trained_at":     time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    with open(os.path.join(MODEL_DIR, "model_metadata.json"), "w") as f:
        json.dump(meta, f, indent=2)

    log.info(f"💾  All artifacts saved to ./{MODEL_DIR}/")
    log.info("     ├── xgb_crop_model.pkl   (joblib)")
    log.info("     ├── xgb_crop_model.json  (native XGBoost — fastest)")
    log.info("     ├── scaler.pkl")
    log.info("     ├── label_encoder.pkl")
    log.info("     ├── model_metadata.json")
    log.info("     ├── classification_report.txt")
    log.info("     ├── confusion_matrix.png")
    log.info("     └── feature_importance.png")


# ─────────────────────────────────────────────────────────────────────────────
# 9. MAIN ORCHESTRATOR
# ─────────────────────────────────────────────────────────────────────────────
def main():
    t0 = time.time()
    log.info("╔══════════════════════════════════════════╗")
    log.info("║   SmartAgri · XGBoost Training Pipeline  ║")
    log.info("╚══════════════════════════════════════════╝")

    # --- GPU Config ---
    gpu_cfg = detect_gpu()

    # --- Load & validate data ---
    df = load_and_validate(DATASET_PATH)

    # Feature engineering (already applied in CSV, but re-apply for safety)
    base_cols = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
    missing_fe = [c for c in FEATURE_COLS if c not in df.columns]
    if missing_fe:
        log.info("  Re-applying feature engineering …")
        df = feature_engineering(df)

    X = df[FEATURE_COLS].values
    y_raw = df[TARGET_COL].values

    # --- Encode labels ---
    le = LabelEncoder()
    y  = le.fit_transform(y_raw)
    log.info(f"  Classes ({len(le.classes_)})  : {list(le.classes_)}")

    # --- Train / Test split (stratified 85/15) ---
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, stratify=y, random_state=RANDOM_STATE
    )
    log.info(f"  Train rows : {len(X_train):,}   Test rows : {len(X_test):,}")

    # --- Feature scaling ---
    scaler  = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test  = scaler.transform(X_test)

    # --- Optuna HPO ---
    best_params = run_optuna(X_train, y_train, gpu_cfg, n_trials=OPTUNA_TRIALS)

    # --- Cross-Validation ---
    cv_scores = run_cross_validation(X_train, y_train, best_params)

    # --- Final training + evaluation ---
    model, metrics = train_final_model(
        X_train, X_test, y_train, y_test, best_params, le, scaler
    )

    metrics["cv_mean_accuracy"] = round(float(cv_scores.mean()), 6)
    metrics["cv_std_accuracy"]  = round(float(cv_scores.std()),  6)

    # --- Save everything ---
    save_artifacts(model, scaler, le, metrics, best_params)

    # --- Generate test.csv from held-out set ---
    _save_test_csv(df, X_test, y_test, le, scaler)

    elapsed = time.time() - t0
    log.info(f"\n⏱️  Total training time : {elapsed/60:.1f} min")
    log.info(f"🎯  Final Test Accuracy : {metrics['accuracy']*100:.4f}%")
    log.info("✅  Done. See model_artifacts/ for all outputs.")


def _save_test_csv(df_orig, X_test_scaled, y_test, le, scaler):
    """Saves the scaled test-split back as a readable CSV for evaluate_model.py."""
    X_unscaled = scaler.inverse_transform(X_test_scaled)
    test_df    = pd.DataFrame(X_unscaled, columns=FEATURE_COLS)
    test_df[TARGET_COL] = le.inverse_transform(y_test)
    out = "data/processed/test.csv"
    test_df.to_csv(out, index=False)
    log.info(f"📄  Test CSV saved → {out}  ({len(test_df):,} rows)")


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
