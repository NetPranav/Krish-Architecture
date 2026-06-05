@echo off
setlocal enabledelayedexpansion
title SmartAgri - Full System Launcher

echo ==============================================================
echo              SMARTAGRI FULL SYSTEM LAUNCHER
echo ==============================================================
echo.

cd /d "%~dp0"

echo [1] Checking and installing Backend dependencies...
cd SmartAgriCulture
if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate.bat
echo Installing requirements...
pip install -r requirements.txt -q
echo.

echo [2] Starting Backend Server (with auto ngrok)...
echo Keep this window open! The backend server will run here.
echo Starting FastAPI server in background...
start "SmartAgri Backend API" cmd /c "call venv\Scripts\activate.bat && uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload"

echo Waiting for backend to initialize and generate ngrok URL...
timeout /t 10 /nobreak >nul

echo.
echo [3] Fetching Ngrok URL for Frontend configuration...
set NGROK_URL=
for /f "delims=" %%i in ('python -c "import urllib.request, json; print(json.loads(urllib.request.urlopen('http://localhost:8000/api/ngrok').read())['url'])" 2^>nul') do set NGROK_URL=%%i

if "%NGROK_URL%"=="" (
    echo WARNING: Failed to fetch Ngrok URL. Make sure NGROK_ENABLED=true and NGROK_AUTHTOKEN is set in SmartAgriCulture\.env
    set NGROK_JSON={"url": null}
) else (
    echo Success! Ngrok Tunnel Active: %NGROK_URL%
    set NGROK_JSON={"url": "%NGROK_URL%"}
)

echo.
echo [4] Configuring Frontend...
cd ..\AI-Krishi-kapil-krishi\AI-Krishi-kapil-krishi

echo Writing ngrok.json...
echo !NGROK_JSON! > ngrok.json

echo Installing frontend dependencies (if needed)...
call npm install --silent

echo.
echo ==============================================================
echo SYSTEM READY!
echo ==============================================================
if not "%NGROK_URL%"=="" (
    echo Your API is publicly available at: %NGROK_URL%
    echo The mobile app can access it from ANYWHERE!
) else (
    echo Local mode active. Accessible only on local network.
)
echo.
echo [5] Starting Next.js Frontend Dev Server...
call npm run dev

pause
