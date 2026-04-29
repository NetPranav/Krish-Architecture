"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  PHASE 1 — Data Engineering & Target Generation                             ║
║  SmartAgri · Fault-Tolerant Multi-Output Regression Pipeline                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

Loads master_crop_dataset.csv (first 2000 rows), simulates user inputs,
engineers deficit targets + soil health score, injects 10% sensor faults,
and saves as engineered_training_data.csv.

RUN:  python data_prep.py
"""

import numpy as np
import pandas as pd
import warnings
import logging

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

DATASET_PATH = "data/processed/master_crop_dataset.csv"
OUTPUT_PATH  = "data/processed/engineered_training_data.csv"
N_ROWS       = 2000

# Sensor columns subject to fault injection
SENSOR_COLS = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]

# ─────────────────────────────────────────────────────────────────────────────
# IDEAL CROP PROFILES
# ─────────────────────────────────────────────────────────────────────────────
# These are the agronomically ideal N, P, K (kg/ha) and pH for each crop
# at full maturity. Built from domain knowledge + dataset medians.

def _build_ideal_profiles(df: pd.DataFrame) -> dict:
    """
    Derives ideal nutrient profiles per crop from the dataset itself.
    Uses the median of each nutrient per crop label as the 'ideal' target
    — this is the best statistical proxy when real agronomy tables aren't
    available, and it keeps the pipeline self-contained.
    """
    profiles = {}
    for crop in df["Recommended_Crop"].unique():
        crop_data = df[df["Recommended_Crop"] == crop]
        profiles[crop] = {
            "N_ideal":    float(crop_data["N"].median()),
            "P_ideal":    float(crop_data["P"].median()),
            "K_ideal":    float(crop_data["K"].median()),
            "ph_ideal":   float(crop_data["ph"].median()),
            "temp_ideal": float(crop_data["temperature"].median()),
            "hum_ideal":  float(crop_data["humidity"].median()),
            "rain_ideal": float(crop_data["rainfall"].median()),
        }
    return profiles


# ─────────────────────────────────────────────────────────────────────────────
# GROWTH STAGE MULTIPLIER
# ─────────────────────────────────────────────────────────────────────────────
def growth_stage_multiplier(days: int) -> float:
    """
    Nutrient demand varies non-linearly across the growth cycle.
    Returns a multiplier (0.3 → 1.0) representing how much of the
    total-season nutrient requirement is needed by this point.

    Stages:
      0-20   days : Seedling       → 30% of full requirement
      21-50  days : Vegetative     → 60%
      51-90  days : Reproductive   → 100% (peak demand)
      91-120 days : Maturation     → 80%
      121+   days : Harvest-ready  → 50%
    """
    if days <= 20:
        return 0.30 + (days / 20) * 0.10        # 0.30 → 0.40
    elif days <= 50:
        return 0.40 + ((days - 20) / 30) * 0.20  # 0.40 → 0.60
    elif days <= 90:
        return 0.60 + ((days - 50) / 40) * 0.40  # 0.60 → 1.00
    elif days <= 120:
        return 1.00 - ((days - 90) / 30) * 0.20  # 1.00 → 0.80
    else:
        return 0.80 - ((days - 120) / 30) * 0.30  # 0.80 → 0.50


# ─────────────────────────────────────────────────────────────────────────────
# TARGET ENGINEERING
# ─────────────────────────────────────────────────────────────────────────────
def compute_deficits(row, profiles: dict) -> pd.Series:
    """
    Computes Deficit_N, Deficit_P, Deficit_K for a single row.
    Deficit = (Ideal × GrowthMultiplier) − Current
    Negative deficit means surplus (crop has more than enough).
    """
    crop = row["Recommended_Crop"]
    days = row["Days_Since_Planting"]
    profile = profiles.get(crop, profiles[list(profiles.keys())[0]])
    mult = growth_stage_multiplier(int(days))

    deficit_n = max(0, profile["N_ideal"] * mult - row["N"])
    deficit_p = max(0, profile["P_ideal"] * mult - row["P"])
    deficit_k = max(0, profile["K_ideal"] * mult - row["K"])

    return pd.Series({
        "Deficit_N": round(deficit_n, 2),
        "Deficit_P": round(deficit_p, 2),
        "Deficit_K": round(deficit_k, 2),
    })


def compute_soil_health_score(row, profiles: dict) -> float:
    """
    Composite Soil Health Score (0–100).

    Scoring breakdown (100 = perfect):
      - Nutrient Match   : 40 pts (N=15, P=15, K=10)
      - pH Match         : 20 pts
      - Water Avail.     : 15 pts
      - pH Stress Penalty: 15 pts
      - Climate Match    : 10 pts (temp + humidity)
    """
    crop    = row["Recommended_Crop"]
    profile = profiles.get(crop, profiles[list(profiles.keys())[0]])
    score   = 100.0

    # ── Nutrient Match (40 pts) ───────────────────────────────────────────
    # Deduction proportional to % deviation from ideal
    for col, ideal_key, weight in [("N", "N_ideal", 15),
                                    ("P", "P_ideal", 15),
                                    ("K", "K_ideal", 10)]:
        ideal = profile[ideal_key]
        if ideal > 0:
            pct_deviation = abs(row[col] - ideal) / ideal
            deduction = min(weight, weight * pct_deviation)
            score -= deduction

    # ── pH Match (20 pts) ─────────────────────────────────────────────────
    ph_ideal = profile["ph_ideal"]
    ph_dev   = abs(row["ph"] - ph_ideal)
    score   -= min(20, 20 * (ph_dev / 3.0))   # 3 pH units = full deduction

    # ── Water Availability (15 pts) ───────────────────────────────────────
    water = row.get("water_availability", 0)
    ideal_water = profile["rain_ideal"] * (profile["hum_ideal"] / 100.0)
    if ideal_water > 0:
        water_dev = abs(water - ideal_water) / ideal_water
        score -= min(15, 15 * water_dev)

    # ── pH Stress Penalty (15 pts) ────────────────────────────────────────
    ph_stress = row.get("pH_stress", abs(row["ph"] - 6.5))
    score -= min(15, ph_stress * 5.0)   # 3.0 stress = full 15pt deduction

    # ── Climate Match (10 pts) ────────────────────────────────────────────
    temp_dev = abs(row["temperature"] - profile["temp_ideal"]) / max(profile["temp_ideal"], 1)
    hum_dev  = abs(row["humidity"]    - profile["hum_ideal"])  / max(profile["hum_ideal"], 1)
    score -= min(5, 5 * temp_dev)
    score -= min(5, 5 * hum_dev)

    return round(max(0.0, min(100.0, score)), 2)


def compute_advisory_targets(row, deficit_n, deficit_p, deficit_k, soil_score) -> pd.Series:
    """
    Computes the 5 new predictive targets for the farmer Q&A advisories.
    """
    hum   = row.get("humidity", np.nan)
    rain  = row.get("rainfall", np.nan)
    temp  = row.get("temperature", np.nan)
    ph    = row.get("ph", np.nan)

    # 1. Water_Requirement_Index (0 to 100)
    water_urgency = 0.0
    if not np.isnan(hum) and hum < 40:
        water_urgency += (40 - hum) * 2
    if not np.isnan(rain) and rain < 30:
        water_urgency += (30 - rain)
    water_urgency = max(0.0, min(100.0, water_urgency))

    # 2. pH_Adjustment_Required (-3.0 to +3.0)
    ph_adj = 0.0
    if not np.isnan(ph):
        ph_adj = round(6.5 - ph, 2)

    # 3. Temperature_Stress_Score (0 to 100)
    temp_stress = 0.0
    if not np.isnan(temp):
        if temp < 15:
            temp_stress = (15 - temp) * 5
        elif temp > 35:
            temp_stress = (temp - 35) * 5
    temp_stress = max(0.0, min(100.0, temp_stress))

    # 4. Fertilizer_Urgency_Score (0 to 100)
    total_deficit = deficit_n + deficit_p + deficit_k
    fert_urgency = min(100.0, total_deficit * 3.0)

    # 5. Planting_Readiness_Score (0 to 100)
    plant_ready = soil_score

    return pd.Series({
        "Water_Requirement_Index": round(water_urgency, 2),
        "pH_Adjustment_Required": ph_adj,
        "Temperature_Stress_Score": round(temp_stress, 2),
        "Fertilizer_Urgency_Score": round(fert_urgency, 2),
        "Planting_Readiness_Score": round(plant_ready, 2)
    })


# ─────────────────────────────────────────────────────────────────────────────
# FAULT INJECTION
# ─────────────────────────────────────────────────────────────────────────────
def inject_sensor_faults(df: pd.DataFrame, fault_rate: float = 0.10) -> pd.DataFrame:
    """
    Randomly sets ~10% of sensor column values to NaN.
    This simulates real-world ESP32 / LoRa hardware failures.
    """
    df = df.copy()
    n_rows, n_sensor_cols = len(df), len(SENSOR_COLS)
    total_cells = n_rows * n_sensor_cols
    n_faults    = int(total_cells * fault_rate)

    fault_rows = np.random.randint(0, n_rows, size=n_faults)
    fault_cols = np.random.choice(SENSOR_COLS, size=n_faults)

    for r, c in zip(fault_rows, fault_cols):
        df.at[df.index[r], c] = np.nan

    injected_pct = df[SENSOR_COLS].isna().sum().sum() / total_cells * 100
    log.info(f"  💥  Injected {n_faults:,} NaN faults across sensor columns ({injected_pct:.1f}%)")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────────────────────────────────────
def main():
    log.info("╔═══════════════════════════════════════════════════════╗")
    log.info("║  Phase 1 — Data Engineering & Target Generation      ║")
    log.info("╚═══════════════════════════════════════════════════════╝")

    # ── 1. Load base dataset ──────────────────────────────────────────────
    log.info(f"📂  Loading {DATASET_PATH} (first {N_ROWS} rows) …")
    df = pd.read_csv(DATASET_PATH, nrows=N_ROWS)
    log.info(f"  Loaded shape: {df.shape}")
    log.info(f"  Columns: {list(df.columns)}")

    # Rename 'label' → 'Recommended_Crop' for clarity
    df = df.rename(columns={"label": "Recommended_Crop"})

    # ── 2. Simulate user inputs ───────────────────────────────────────────
    log.info("🌱  Simulating user inputs (Current_Crop, Days_Since_Planting) …")
    unique_crops = df["Recommended_Crop"].unique()

    # ~40% chance Current_Crop matches Recommended_Crop (realistic)
    current_crops = []
    for _, row in df.iterrows():
        if np.random.random() < 0.40:
            current_crops.append(row["Recommended_Crop"])
        else:
            current_crops.append(np.random.choice(unique_crops))
    df["Current_Crop"] = current_crops

    # Days since planting: uniform 0-150
    df["Days_Since_Planting"] = np.random.randint(0, 151, size=len(df))

    # Soil type: randomly assign red, yellow, or clay
    soil_types = ["red", "yellow", "clay"]
    df["Soil_Type"] = np.random.choice(soil_types, size=len(df))

    match_pct = (df["Current_Crop"] == df["Recommended_Crop"]).mean() * 100
    log.info(f"  Current=Recommended match rate: {match_pct:.1f}%")
    log.info(f"  Added Soil_Type categorical feature")

    # ── 3. Build ideal profiles from data ─────────────────────────────────
    log.info("📊  Building ideal crop nutrient profiles …")
    # Use the FULL dataset for profile building (not just 2000 rows)
    full_df  = pd.read_csv(DATASET_PATH)
    full_df  = full_df.rename(columns={"label": "Recommended_Crop"})
    profiles = _build_ideal_profiles(full_df)
    log.info(f"  Built profiles for {len(profiles)} crops")
    for crop, prof in list(profiles.items())[:3]:
        log.info(f"    {crop}: N={prof['N_ideal']:.1f}, P={prof['P_ideal']:.1f}, "
                 f"K={prof['K_ideal']:.1f}, pH={prof['ph_ideal']:.2f}")

    # ── 4. Engineer deficit targets ───────────────────────────────────────
    log.info("🔬  Computing nutrient deficits (Deficit_N, Deficit_P, Deficit_K) …")
    deficits = df.apply(lambda row: compute_deficits(row, profiles), axis=1)
    df = pd.concat([df, deficits], axis=1)

    log.info(f"  Deficit_N  range: [{df['Deficit_N'].min():.1f}, {df['Deficit_N'].max():.1f}]")
    log.info(f"  Deficit_P  range: [{df['Deficit_P'].min():.1f}, {df['Deficit_P'].max():.1f}]")
    log.info(f"  Deficit_K  range: [{df['Deficit_K'].min():.1f}, {df['Deficit_K'].max():.1f}]")

    # ── 5. Engineer soil health score ─────────────────────────────────────
    log.info("🏥  Computing Soil_Health_Score (0–100) …")
    df["Soil_Health_Score"] = df.apply(
        lambda row: compute_soil_health_score(row, profiles), axis=1
    )
    log.info(f"  Score range: [{df['Soil_Health_Score'].min():.1f}, {df['Soil_Health_Score'].max():.1f}]")
    log.info(f"  Score mean : {df['Soil_Health_Score'].mean():.1f}")

    # ── 5.5 Engineer 5 new Advisory Targets ───────────────────────────────
    log.info("🤖  Computing 5 Smart Advisory Targets (Water, pH, Temp, Fert, Plant) …")
    advisory_targets = df.apply(
        lambda row: compute_advisory_targets(
            row, row["Deficit_N"], row["Deficit_P"], row["Deficit_K"], row["Soil_Health_Score"]
        ), axis=1
    )
    df = pd.concat([df, advisory_targets], axis=1)

    # ── 6. Fault injection ────────────────────────────────────────────────
    log.info("💥  Injecting 10% sensor faults (NaN simulation) …")
    df = inject_sensor_faults(df, fault_rate=0.10)

    nan_summary = df[SENSOR_COLS].isna().sum()
    log.info(f"  NaN counts per sensor:\n{nan_summary.to_string()}")

    # ── 7. Save ───────────────────────────────────────────────────────────
    log.info(f"💾  Saving to {OUTPUT_PATH} …")
    df.to_csv(OUTPUT_PATH, index=False)
    log.info(f"  Final shape: {df.shape}")
    log.info(f"  Final columns: {list(df.columns)}")

    # ── Summary ───────────────────────────────────────────────────────────
    print(f"""
==========================================================
  Phase 1 Complete                                        
==========================================================
  Rows          : {len(df):>6,}                                
  Features      : {len(df.columns) - 9:>6} input + 9 targets              
  Targets       : Deficit_N, Deficit_P, Deficit_K,        
                  Soil_Health_Score, Water_Req,           
                  pH_Adj, Temp_Stress, Fert_Urg, Plant_R  
  Added Feature : Soil_Type (red, yellow, clay)
  Fault rate    :  ~10% NaN across sensor columns          
  Output file   : {OUTPUT_PATH:<38} 
==========================================================
""")


if __name__ == "__main__":
    main()
