import pandas as pd
import numpy as np
import os
import glob
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib

def load_base_data(filepath):
    """Loads the core crop recommendation mapping dataset."""
    df = pd.read_csv(filepath)
    return df

def load_pollution_disease_data(filepath):
    """Extracts crop-specific environmental distributions to augment the base data."""
    df = pd.read_csv(filepath)
    df['label'] = df['Crop_Type'].str.lower()
    # Group by crop type and get the std/mean for variability injection
    crop_stats = df.groupby('label').agg({
        'Soil_pH': ['mean', 'std'],
        'Temperature_C': ['mean', 'std'],
        'Humidity_%': ['mean', 'std'],
        'Rainfall_mm': ['mean', 'std']
    }).reset_index()
    crop_stats.columns = ['label', 'ph_mean', 'ph_std', 'temp_mean', 'temp_std', 'hum_mean', 'hum_std', 'rain_mean', 'rain_std']
    # Fill any NaNs with overall means
    crop_stats = crop_stats.fillna(crop_stats.mean(numeric_only=True))
    return crop_stats

def load_nasa_power_data(filepath):
    """Extracts extreme weather events and natural historical bounds."""
    with open(filepath, 'r') as f:
        lines = f.readlines()
    skip_rows = 0
    for i, line in enumerate(lines):
        if '-END HEADER-' in line:
            skip_rows = i + 1
            break
    df = pd.read_csv(filepath, skiprows=skip_rows)
    df = df[df['T2M'] != -999.0]
    return df

def load_spectral_soil_data(filepath):
    """Extracts highly accurate real-world African soil chemical distributions."""
    df = pd.read_csv(filepath, usecols=['P', 'pH'])
    # Clean possible non-numeric data gracefully
    df['P'] = pd.to_numeric(df['P'], errors='coerce')
    df['pH'] = pd.to_numeric(df['pH'], errors='coerce')
    df = df.dropna()
    return df['P'].mean(), df['P'].std(), df['pH'].mean(), df['pH'].std()

def augment_and_fuse_data(base_df, pollution_stats, power_df, soil_stats, target_size_per_class=5000):
    """
    DATA FUSION ENGINE
    Combines distributions, handles shape mismatches via statistical mapping,
    and generates a robust, massive synthetic dataset for deep ML training.
    """
    augmented_data = []
    features = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']
    
    nasa_temp_std = power_df['T2M'].std()
    nasa_hum_std = power_df['RH2M'].std()
    nasa_rain_std = power_df['PRECTOTCORR'].std()
    
    soil_p_mean, soil_p_std, soil_ph_mean, soil_ph_std = soil_stats
    
    # We will generate synthetic variations around the base means per crop
    for label in base_df['label'].unique():
        class_data = base_df[base_df['label'] == label][features]
        mean_vec = class_data.mean().values
        cov_matrix = class_data.cov().values
        
        # Merge with pollution stats to increase the robustness variance
        poll_stat = pollution_stats[pollution_stats['label'] == label]
        if not poll_stat.empty:
            cov_matrix[3,3] = max(cov_matrix[3,3], poll_stat['temp_std'].values[0]**2)
            cov_matrix[4,4] = max(cov_matrix[4,4], poll_stat['hum_std'].values[0]**2)
            cov_matrix[5,5] = max(cov_matrix[5,5], poll_stat['ph_std'].values[0]**2)
            cov_matrix[6,6] = max(cov_matrix[6,6], poll_stat['rain_std'].values[0]**2)
            
        # Add background NASA power variability to simulate outdoor climate shifts
        cov_matrix[3,3] += nasa_temp_std * 0.1 
        cov_matrix[4,4] += nasa_hum_std * 0.1
        cov_matrix[6,6] += nasa_rain_std * 0.1
        
        # Ensure covariance matrix is positive semi-definite
        min_eig = np.min(np.real(np.linalg.eigvals(cov_matrix)))
        if min_eig < 0:
            cov_matrix -= 10 * min_eig * np.eye(*cov_matrix.shape)
            
        # Generative AI (Multivariate Gaussian) for Data Augmentation
        synthetic_samples = np.random.multivariate_normal(mean_vec, cov_matrix, size=target_size_per_class)
        
        # Hard limits based on biological / physical reality
        synthetic_samples[:, 0] = np.clip(synthetic_samples[:, 0], 0, 150) # N
        synthetic_samples[:, 1] = np.clip(synthetic_samples[:, 1], 0, 150) # P
        synthetic_samples[:, 2] = np.clip(synthetic_samples[:, 2], 0, 205) # K
        synthetic_samples[:, 3] = np.clip(synthetic_samples[:, 3], -5, 55) # Temp
        synthetic_samples[:, 4] = np.clip(synthetic_samples[:, 4], 0, 100) # Humidity
        synthetic_samples[:, 5] = np.clip(synthetic_samples[:, 5], 3.5, 9.5) # pH
        synthetic_samples[:, 6] = np.clip(synthetic_samples[:, 6], 0, 400) # Rainfall
        
        # Inject 10% extreme realistic African soil distributions to force the model to handle anomalies
        mask = np.random.rand(target_size_per_class) < 0.1
        synthetic_samples[mask, 1] = np.random.normal(soil_p_mean, soil_p_std, size=np.sum(mask))
        synthetic_samples[mask, 5] = np.random.normal(soil_ph_mean, soil_ph_std, size=np.sum(mask))
        synthetic_samples[:, 1] = np.clip(synthetic_samples[:, 1], 0, 150)
        synthetic_samples[:, 5] = np.clip(synthetic_samples[:, 5], 3.5, 9.5)
        
        df_syn = pd.DataFrame(synthetic_samples, columns=features)
        df_syn['label'] = label
        augmented_data.append(df_syn)
        
    final_df = pd.concat(augmented_data, ignore_axis=True)
    return final_df

def feature_engineering(df):
    """
    Advanced Feature Extraction. 
    These exact calculations will be run on the backend for Live ESP32 data.
    """
    df_fe = df.copy()
    
    # 1. Macro-nutrient interaction terms
    df_fe['N_P_ratio'] = df_fe['N'] / (df_fe['P'] + 1e-5)
    df_fe['N_K_ratio'] = df_fe['N'] / (df_fe['K'] + 1e-5)
    df_fe['P_K_ratio'] = df_fe['P'] / (df_fe['K'] + 1e-5)
    
    # 2. Weather/Soil Interaction terms
    df_fe['THI'] = df_fe['temperature'] * df_fe['humidity'] # Temp Humidity Index
    df_fe['water_availability'] = df_fe['rainfall'] * (df_fe['humidity'] / 100.0)
    df_fe['pH_stress'] = np.abs(df_fe['ph'] - 6.5) # Stress due to deviation from neutral pH
    
    return df_fe

def preprocess_live_data(live_payload):
    """
    BACKEND INTEGRATION FUNCTION
    Transforms sparse ESP32 data into the 13-parameter vector the XGBoost needs.
    Expected: {'N': val, 'P': val, 'K': val, 'Moisture': val} + API variables
    """
    # Global intelligent defaults if API/Sensor fails
    defaults = {
        'N': 50.0, 'P': 50.0, 'K': 50.0,
        'temperature': 25.0, 'humidity': 60.0,
        'ph': 6.5, 'rainfall': 100.0
    }
    
    # Map ESP32 'Moisture' -> 'humidity' if not explicitly provided
    if 'humidity' not in live_payload and 'Moisture' in live_payload:
        live_payload['humidity'] = live_payload['Moisture']
        
    for k in defaults.keys():
        if k not in live_payload or live_payload[k] is None:
            live_payload[k] = defaults[k]
            
    df = pd.DataFrame([live_payload])
    df_fe = feature_engineering(df)
    
    features = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall', 
                'N_P_ratio', 'N_K_ratio', 'P_K_ratio', 'THI', 'water_availability', 'pH_stress']
    
    return df_fe[features]

def train_high_accuracy_model(master_dataset):
    """Builds and validates the XGBoost master engine."""
    print("Initiating XGBoost Model Training...")
    try:
        from xgboost import XGBClassifier
    except Exception as e:
        print(f"XGBoost library could not be loaded: {e}")
        print("Skipping training. Please install libomp on macOS.")
        return
    features = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall', 
                'N_P_ratio', 'N_K_ratio', 'P_K_ratio', 'THI', 'water_availability', 'pH_stress']
    
    X = master_dataset[features]
    y = master_dataset['label']
    
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    model = XGBClassifier(
        n_estimators=600,
        learning_rate=0.05,
        max_depth=8,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric='mlogloss',
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train_scaled, y_train)
    y_pred = model.predict(X_test_scaled)
    acc = accuracy_score(y_test, y_pred)
    print(f"\n=> FINAL XGBOOST ACCURACY ON AUGMENTED DATA: {acc*100:.3f}%\n")
    
    joblib.dump(model, 'xgb_crop_model.pkl')
    joblib.dump(le, 'label_encoder.pkl')
    joblib.dump(scaler, 'scaler.pkl')
    print("=> Model objects serialized successfully (xgb_crop_model.pkl, label_encoder.pkl, scaler.pkl).")

def main():
    print("1. Loading multiple disparate datasets for fusion...")
    base_df = load_base_data('data/raw/Crop_recommendation_kaggle.csv')
    pollution_stats = load_pollution_disease_data('data/raw/soil_pollution_diseases.csv')
    power_df = load_nasa_power_data('data/raw/POWER_Point_Daily_20160106_20260428_023d59N_078d29E_UTC.csv')
    soil_stats = load_spectral_soil_data('data/raw/training.csv')
    
    print("2. Performing Statistical Data Fusion and Augmentation (Target: ~110,000 rows)...")
    # Generates 5000 rows per class (22 classes * 5000 = 110,000 rows)
    fused_dataset = augment_and_fuse_data(base_df, pollution_stats, power_df, soil_stats, target_size_per_class=5000)
    
    print("3. Executing Advanced Feature Engineering...")
    master_dataset = feature_engineering(fused_dataset)
    
    print(f"   => New Super-Dataset Shape: {master_dataset.shape}")
    master_dataset.to_csv('data/processed/master_crop_dataset.csv', index=False)
    print("   => Saved to 'data/processed/master_crop_dataset.csv'.")
    
    print("4. (Optional) Validating via Model Compilation...")
    print("   Please ensure libomp is installed to run XGBoost (e.g., `brew install libomp`).")
    # train_high_accuracy_model(master_dataset)

if __name__ == '__main__':
    main()
