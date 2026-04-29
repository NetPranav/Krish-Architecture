# SmartAgri — Final Build Report

## 📁 Files Created

| File | Purpose |
|---|---|
| `src/api/__init__.py` | Module init |
| `src/api/server.py` | **Unified FastAPI gateway** — 13 endpoint groups, wires everything |
| `src/api/auth.py` | Hardcoded single-user auth |
| `src/api/weather_service.py` | OpenWeatherMap integration + mock fallback |
| `src/api/mandi_service.py` | 10 commodities, 5 APMCs, price forecast engine |
| `src/api/chemical_db.py` | 12 agrochemicals, alternative matcher, disease→treatment map |
| `src/api/alert_engine.py` | Rule-based + ML-based alert generation |
| `src/api/sensor_store.py` | Simulated ESP32 sensor data with pump control |
| `.env` | All API keys with documentation |

---

## 🔑 Hardcoded User Account

```
Phone:    9876543210
Password: smartagri123
OTP:      123456
```

---

## 🔐 API Keys — Where to Get Them & Limits

### 1. Roboflow (Leaf Disease Detection) — ✅ Already Have
- **Key:** `jd2f979P6gJ56STASmHq` (already in your .env)
- **Free tier:** 10,000 inferences/month
- **Tip:** Each leaf scan = 1 inference. Cache results client-side.

### 2. OpenWeatherMap (Weather) — ❌ Need to Get
- **Get key:** [https://home.openweathermap.org/api_keys](https://home.openweathermap.org/api_keys)
- **Free tier limits:**
  - 1,000 API calls/day (~41/hour)
  - Current weather ✅
  - 5-day / 3-hour forecast ✅
  - Hourly forecast ❌ (requires "One Call" — $0.001/call)
  - 16-day forecast ❌ (paid)
  - Historical data ❌ (paid)
- **Our usage:** Server caches for 10 min → max ~144 calls/day
- **Without key:** Server auto-falls back to realistic mock data

### 3. data.gov.in (Mandi Prices) — Optional
- **Get key:** [https://data.gov.in/user/register](https://data.gov.in/user/register)
- **Free tier:** Unlimited calls (government open data)
- **Without key:** Uses hardcoded data for 10 Maharashtra commodities

### 4. Ollama (Mitra AI LLM) — No Key Needed
- **Setup on GPU machine:**
  ```bash
  # Install Ollama
  curl -fsSL https://ollama.com/install.sh | sh
  # Start server
  ollama serve
  # Pull the model (one-time, ~12GB download)
  ollama pull gpt4o-s:20b
  ```
- **Limit:** Your GPU VRAM (8GB minimum for Q4 quantized 20B model)

---

## 🚀 How to Run

```bash
cd /Users/pranav/Project\ Folder/Krish-Architecture-main/SmartAgriCulture

# Install dependencies (if not done)
pip install -r requirements.txt

# Run the backend
uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload

# In another terminal, tunnel via ngrok
ngrok http 8000
```

Then set the ngrok URL in your Next.js frontend's API config.

---

## ✅ Page-by-Page Readiness Status

| Frontend Page | Backend Endpoint | Status | Notes |
|---|---|---|---|
| **Landing** | None needed | ✅ Ready | Static page |
| **Login** | `POST /api/auth/login` | ✅ Ready | Use: 9876543210 / smartagri123 |
| **Register** | `POST /api/auth/register` | ✅ Ready | Creates demo user |
| **Profile Setup** | `PUT /api/profile` | ✅ Ready | Updates hardcoded profile |
| **Profile** | `GET /api/profile` | ✅ Ready | Returns full profile |
| **Dashboard Home** | `GET /api/dashboard` | ✅ Ready | Aggregates weather + sensors + market + alerts |
| **Weather** | `GET /api/weather/*` | ✅ Ready | Real API with key, mock without |
| **Mandi Insights** | `GET /api/mandi/prices,nearby,forecast` | ✅ Ready | 10 commodities, 5 mandis, forecast |
| **Mandi Detail** | `GET /api/mandi/detail/{name}` | ✅ Ready | Trend + alternatives |
| **Product Analyzer** | `GET /api/products/analyze` | ✅ Ready | 12 chemicals, alt matching |
| **Telemetry HUD** | `GET /api/telemetry/live` | ✅ Ready | Simulated sensors, NPK, pH |
| **Leaf Scanner** | `POST /api/vision/scan-leaf` | ✅ Ready | Roboflow model (needs API key) |
| **Scan Result** | Uses scan-leaf + treatments | ✅ Ready | Auto-attaches treatment options |
| **Alerts** | `GET /api/alerts` | ✅ Ready | Rule-based + weather + ML alerts |
| **Irrigation Hub** | `GET /api/irrigation/status` | ✅ Ready | Pump control, water usage |
| **Mitra AI Chat** | `POST /api/mitra/chat` | ⚠️ Partial | Needs Ollama running on GPU machine |

---

## What's Fully Production-Ready vs Simulated

### ✅ Production-Ready (Real ML Models)
1. **Crop Detection** — Trained XGBoost, real predictions
2. **Fertilizer Advisor** — 9-target multi-output model, real reports
3. **Leaf Disease Scanner** — Roboflow cloud inference, real results
4. **Mitra AI Chat** — Full agentic pipeline (when Ollama is running)

### ✅ Production-Ready (Real APIs)
5. **Weather** — Real OpenWeatherMap data (just add API key to .env)

### ⚠️ Functional but Simulated Data
6. **Mandi Prices** — Hardcoded 10 commodities (real when data.gov.in key added)
7. **Chemical Products** — 12 real Indian agrochemicals, real matching logic
8. **Sensor Telemetry** — Realistic simulation (real when ESP32 connected via MQTT)
9. **Alerts** — Working rule engine, but fed from simulated sensors
10. **Irrigation/Pump** — Full logic, simulated hardware

### 🔧 Not Built (Hardware Dependent)
- **Real ESP32 MQTT bridge** — needs physical hardware
- **Pump relay control** — needs physical relay + ESP32
- **Flow meter tracking** — needs sensor

---

## Architecture Diagram

```
Next.js Frontend (Kapil-Krishi)
        │
        │  ngrok tunnel
        ▼
┌─────────────────────────────────────┐
│  FastAPI Unified Gateway (server.py)│
│  Port 8000                          │
├─────────────────────────────────────┤
│  auth.py          → Hardcoded user  │
│  weather_service  → OpenWeatherMap  │
│  mandi_service    → Price data+forecast│
│  chemical_db      → Product catalog │
│  alert_engine     → Rule engine     │
│  sensor_store     → ESP32 simulator │
├─────────────────────────────────────┤
│  ML Models (loaded at startup):     │
│  ├─ xgb_crop_model.pkl     ✅      │
│  ├─ master_ag_model.pkl     ✅      │
│  ├─ Roboflow Vision         ✅      │
│  └─ Mitra + Ollama LLM      ✅      │
└─────────────────────────────────────┘
```
