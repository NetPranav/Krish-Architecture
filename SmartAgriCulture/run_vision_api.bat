@echo off
:: ╔══════════════════════════════════════════════════════════════════╗
:: ║  SmartAgri · Vision API Server Launcher                         ║
:: ║  Starts the FastAPI leaf-disease detection endpoint.             ║
:: ╚══════════════════════════════════════════════════════════════════╝

echo.
echo  ===================================================
echo     SmartAgri Vision API — Leaf Disease Detection
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
echo  Starting FastAPI server on http://localhost:8000 ...
echo  Docs available at  http://localhost:8000/docs
echo.

uvicorn src.vision.main:app --reload --host 0.0.0.0 --port 8000
