# How to Run the Complete SmartAgri System

This guide explains how to start the entire SmartAgri platform (Backend, ML Models, AI Orchestrator, and Frontend) from scratch.

---

## 1. Prerequisites
Ensure you have the following running in the background before starting the SmartAgri stack:
- **Ollama**: Must be running with the `gpt-oss:20b` model.
  - Start it via command prompt: `ollama serve` (or ensure the background service is running).

---

## 2. Start the Backend API (FastAPI)
The backend unifies the Crop Detection, Fertilizer Optimization, Vision AI, and Mitra LLM models into a single API served on **port 8000**.

1. Open a new Command Prompt or PowerShell terminal.
2. Navigate to the `SmartAgriCulture` directory:
   ```cmd
   cd "a:\Project Folder\SmartAgri\SmartAgriCulture"
   ```
3. Activate the virtual environment (optional but recommended):
   ```cmd
   venv\Scripts\activate
   ```
4. Start the Uvicorn server:
   ```cmd
   python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
   ```
5. *Wait for the models to load into memory.* You will see green ✅ marks in the console once all four models (Crop, Fertilizer, Vision, Mitra) are loaded and the API is ready.

---

## 3. Start the Frontend Application (Next.js)
The frontend provides the user interface for the dashboard, scanner, telemetry, and Mitra AI Chat. It connects to the backend API on port 8000.

1. Open a **second** Command Prompt or PowerShell terminal.
2. Navigate to the frontend directory:
   ```cmd
   cd "a:\Project Folder\SmartAgri\AI-Krishi-kapil-krishi\AI-Krishi-kapil-krishi"
   ```
3. Start the Next.js development server:
   ```cmd
   npm run dev
   ```
4. The frontend will be available at **http://localhost:3000**

---

## 4. Test the System

### Accessing the Web Interface
1. Open your browser and go to http://localhost:3000
2. Log in using the test credentials:
   - **Phone Number:** `9479436780`
   - **Password:** `smartagri123`
   - **OTP:** `123456`

### Accessing Backend API Documentation
- You can view and test the raw backend API endpoints via Swagger UI at: http://localhost:8000/docs

---

## Troubleshooting

- **"Address already in use" Error:** If you get an error that port 8000 or 3000 is already in use, find the process holding the port and kill it.
  - *Kill Port 8000 (Backend):* `netstat -ano | findstr :8000` -> Note the PID -> `taskkill /PID <PID> /F`
  - *Kill Port 3000 (Frontend):* `netstat -ano | findstr :3000` -> Note the PID -> `taskkill /PID <PID> /F`

- **Mitra Chat Not Working / "Error reaching Mitra":** Ensure that Ollama is actively running and has the `gpt-oss:20b` model loaded. You can verify the model is installed by running `ollama list` in the terminal.

- **SQLite Database Errors:** The central database is located at `SmartAgriCulture\data\mitra_ledger.db`. If there are schema mismatches or database corruption during development, you can delete this file, and the backend will recreate it with the correct schema upon the next startup.


netstat -ano | findstr :11434
netstat -ano | findstr :8000
taskkill /PID 18308 /F
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
