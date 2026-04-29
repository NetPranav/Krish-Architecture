@echo off
:: ╔══════════════════════════════════════════════════════════════════╗
:: ║  SmartAgri · Multi-Output Regression — Full Pipeline Runner     ║
:: ║  Runs Phase 1 → Phase 2 → Phase 3 sequentially                 ║
:: ╚══════════════════════════════════════════════════════════════════╝

echo.
echo  ===================================================
echo     SmartAgri Multi-Output Regression Pipeline
echo  ===================================================
echo.

:: Activate venv
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo  [OK] Virtual environment activated.
) else (
    echo  [WARN] No venv found — using system Python.
)

echo.
echo  [1/3] Phase 1: Data Engineering ^& Target Generation
echo  ─────────────────────────────────────────────────────
python src\fertilizer_optimization\data_prep.py
if errorlevel 1 (
    echo  [ERROR] Phase 1 failed. Aborting.
    pause
    exit /b 1
)

echo.
echo  [2/3] Phase 2: Model Training (Multi-Output XGBoost)
echo  ─────────────────────────────────────────────────────
python src\fertilizer_optimization\model_trainer.py
if errorlevel 1 (
    echo  [ERROR] Phase 2 failed. Aborting.
    pause
    exit /b 1
)

echo.
echo  [3/3] Phase 3: Inference ^& Advisory Demo
echo  ─────────────────────────────────────────────────────
python src\fertilizer_optimization\inference.py

echo.
echo  ===================================================
echo     All 3 phases complete!
echo     Check: data\processed\engineered_training_data.csv
echo            models\fertilizer_optimization\master_ag_model.pkl
echo            models\fertilizer_optimization\artifacts\
echo  ===================================================
pause
