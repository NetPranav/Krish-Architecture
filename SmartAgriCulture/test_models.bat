@echo off
:: ╔══════════════════════════════════════════════════════════════════╗
:: ║  SmartAgri · Master Test Launcher                              ║
:: ║  Runs demo_all_models.py to test both pipelines together       ║
:: ╚══════════════════════════════════════════════════════════════════╝

echo.
echo  ===================================================
echo     SmartAgri AI — End-to-End Master Test
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
set PYTHONIOENCODING=utf-8
python demo_all_models.py

echo.
pause
