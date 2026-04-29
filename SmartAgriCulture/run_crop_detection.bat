@echo off
:: ╔══════════════════════════════════════════════════════════════════╗
:: ║  SmartAgri · One-Click Install + Train                          ║
:: ║  Run this ONCE to set everything up and start training.         ║
:: ╚══════════════════════════════════════════════════════════════════╝

echo.
echo  ╔════════════════════════════════════════╗
echo  ║   SmartAgri Crop Engine — Setup        ║
echo  ╚════════════════════════════════════════╝
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b 1
)

:: Create virtual environment if it doesn't exist
if not exist "venv\" (
    echo [1/4] Creating virtual environment...
    python -m venv venv
)

:: Activate
echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat

:: Upgrade pip
echo [3/4] Installing dependencies...
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt

:: Check if CUDA GPU is available
python -c "import subprocess; r=subprocess.run(['nvidia-smi'],capture_output=True); print('[GPU] CUDA GPU detected!' if r.returncode==0 else '[CPU] No GPU — using CPU mode.')"

echo.
echo [4/4] Starting training pipeline...
echo       This will take 10-30 minutes depending on hardware.
echo.
python src\crop_detection\train_model.py

echo.
echo ════════════════════════════════════════════════
echo  Training complete! Now running evaluation...
echo ════════════════════════════════════════════════
echo.
python src\crop_detection\evaluate_model.py

echo.
echo  All done! Check models\crop_detection\ for saved model files.
pause
