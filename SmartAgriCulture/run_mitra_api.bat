@echo off
REM ╔══════════════════════════════════════════════════════════════╗
REM ║  SmartAgri · Run Mitra API Server                           ║
REM ║  Starts the agentic orchestrator on port 8001               ║
REM ╚══════════════════════════════════════════════════════════════╝

echo.
echo  ===================================================
echo     SmartAgri Mitra - Agentic AI Farming Assistant
echo  ===================================================
echo.

REM Activate venv
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo  [OK] Virtual environment activated.
) else (
    echo  [WARN] No venv found. Using system Python.
)

echo.
echo  [1/2] Checking Ollama status...
echo  ─────────────────────────────────────────────────────

ollama list 2>NUL
if errorlevel 1 (
    echo  [ERROR] Ollama is not running!
    echo  Please start it with: ollama serve
    pause
    exit /b 1
)

echo.
echo  [2/2] Starting Mitra API Server on port 8001...
echo  ─────────────────────────────────────────────────────
echo  Endpoint: POST http://localhost:8001/api/mitra/chat
echo  History:  GET  http://localhost:8001/api/mitra/history
echo  Health:   GET  http://localhost:8001/
echo.

python -m uvicorn src.mitra.main:app --reload --host 0.0.0.0 --port 8001

pause
