"""
SmartAgri · Unified API Gateway (v2 — All Systems Wired)
=========================================================
RUN:   uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
NGROK: ngrok http 8000
"""

import json, logging, time, os
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api import auth, weather_service, mandi_service, chemical_db
from src.api.alert_engine import AlertEngine
from src.api.sensor_store import SensorStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

app = FastAPI(title="SmartAgri Unified API", version="2.0.0",
              description="Complete backend for AI-Krishi frontend. Run on GPU machine, tunnel via ngrok.")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

# ── Singletons ───────────────────────────────────────────────────
alert_engine = AlertEngine()
sensor_store = SensorStore()

# ML models
crop_model = crop_scaler = crop_encoder = None
fert_advisor = vision_predictor = mitra_orchestrator = None


@app.on_event("startup")
def load_models():
    global crop_model, crop_scaler, crop_encoder, fert_advisor, vision_predictor, mitra_orchestrator
    try:
        import joblib
        base = "models/crop_detection"
        crop_model = joblib.load(f"{base}/xgb_crop_model.pkl")
        crop_scaler = joblib.load(f"{base}/scaler.pkl")
        crop_encoder = joblib.load(f"{base}/label_encoder.pkl")
        log.info("✅ Crop Detection loaded")
    except Exception as e:
        log.warning("⚠️  Crop Detection: %s", e)
    try:
        from src.fertilizer_optimization.inference import AgriAdvisor
        fert_advisor = AgriAdvisor()
        log.info("✅ Fertilizer Advisor loaded")
    except Exception as e:
        log.warning("⚠️  Fertilizer: %s", e)
    try:
        from src.vision.roboflow_client import CloudVisionPredictor
        vision_predictor = CloudVisionPredictor()
        log.info("✅ Vision loaded")
    except Exception as e:
        log.warning("⚠️  Vision: %s", e)
    try:
        from src.mitra.mitra_brain import MitraOrchestrator
        mitra_orchestrator = MitraOrchestrator()
        log.info("✅ Mitra loaded")
    except Exception as e:
        log.warning("⚠️  Mitra: %s", e)


# ═══════════════════════════════════════════════════════════════════
# HEALTH
# ═══════════════════════════════════════════════════════════════════
@app.get("/", tags=["Health"])
def health():
    return {"service": "SmartAgri Unified API", "status": "online",
            "weather_api": bool(os.getenv("OPENWEATHER_API_KEY")),
            "models": {"crop": crop_model is not None, "fertilizer": fert_advisor is not None,
                       "vision": vision_predictor is not None, "mitra": mitra_orchestrator is not None}}


# ═══════════════════════════════════════════════════════════════════
# 1. AUTH  (hardcoded: phone=9876543210, pass=smartagri123)
# ═══════════════════════════════════════════════════════════════════
@app.post("/api/auth/login", tags=["Auth"])
def api_login(email_or_phone: str = Form(...), password: str = Form(...)):
    return auth.login(email_or_phone, password)

@app.post("/api/auth/register", tags=["Auth"])
def api_register(full_name: str = Form(...), phone: str = Form(...),
                 language: str = Form("en"), operation: str = Form(...)):
    return auth.register(full_name, phone, language, operation)

@app.post("/api/auth/otp/send", tags=["Auth"])
def api_otp_send(phone: str = Form(...)):
    return {"status": "success", "message": f"OTP sent to {phone} (demo: use 123456)"}

@app.post("/api/auth/otp/verify", tags=["Auth"])
def api_otp_verify(phone: str = Form(...), otp: str = Form(...)):
    if otp == "123456":
        return {"status": "success", "token": auth.VALID_TOKEN}
    return {"status": "error", "message": "Invalid OTP. Demo OTP is 123456"}


# ═══════════════════════════════════════════════════════════════════
# 2. PROFILE
# ═══════════════════════════════════════════════════════════════════
@app.get("/api/profile", tags=["Profile"])
def api_get_profile():
    return {"status": "success", "profile": auth.get_profile()}

@app.put("/api/profile", tags=["Profile"])
def api_update_profile(land_size: Optional[str] = Form(None), land_unit: Optional[str] = Form(None),
                       soil_type: Optional[str] = Form(None), voice_assistance: Optional[bool] = Form(None),
                       language: Optional[str] = Form(None)):
    return auth.update_profile(land_size=land_size, land_unit=land_unit, soil_type=soil_type,
                               voice_assistance=voice_assistance, language=language)


# ═══════════════════════════════════════════════════════════════════
# 3. DASHBOARD (aggregated from all services)
# ═══════════════════════════════════════════════════════════════════
@app.get("/api/dashboard", tags=["Dashboard"])
def api_dashboard():
    profile = auth.get_profile()
    weather = weather_service.get_current(profile["lat"], profile["lon"])
    telemetry = sensor_store.get_live_telemetry()
    prices = mandi_service.get_prices()
    alerts = alert_engine.get_all()

    # Generate dynamic alerts from live data
    sensor_alerts = alert_engine.generate_from_sensors(telemetry["raw_sensors"])
    weather_alerts = alert_engine.generate_from_weather(weather)

    top_commodity = prices["commodities"][0] if prices["commodities"] else {}
    unread = sum(1 for a in alerts if not a.get("read"))

    return {
        "status": "success",
        "weather": {"temperature": weather.get("temperature", 28),
                    "description": weather.get("description", "Partly Cloudy"),
                    "rain_probability": weather.get("rain_probability", 10),
                    "location": profile["location"]},
        "moisture": telemetry["soil_moisture"],
        "market": {"commodity": top_commodity.get("name", "Soybeans"),
                   "price": top_commodity.get("price", 4200),
                   "unit": top_commodity.get("unit", "₹/qtl"),
                   "change_pct": round(top_commodity.get("change", 0) / max(top_commodity.get("price", 1), 1) * 100, 1)},
        "alerts_count": unread,
        "alerts": (sensor_alerts + weather_alerts + [a for a in alerts if not a.get("read")])[:3],
        "actions": [
            {"id": 1, "text": "Inspect Plot A for pests", "done": False},
            {"id": 2, "text": "Apply fertilizer to Plot C", "done": True},
            {"id": 3, "text": "Check drip lines in greenhouse", "done": False},
        ],
        "ai_insight": {
            "title": "Optimal Irrigation Window",
            "text": f"Moisture at {telemetry['soil_moisture']['value']}%. " +
                    ("Turn on pump now to save 15% water." if telemetry['soil_moisture']['value'] < 50
                     else "Levels are healthy. No action needed."),
        },
    }


# ═══════════════════════════════════════════════════════════════════
# 4. WEATHER (OpenWeatherMap with mock fallback)
# ═══════════════════════════════════════════════════════════════════
@app.get("/api/weather/current", tags=["Weather"])
def api_weather_current(lat: float = 20.0063, lon: float = 73.7895):
    return weather_service.get_current(lat, lon)

@app.get("/api/weather/forecast", tags=["Weather"])
def api_weather_forecast(lat: float = 20.0063, lon: float = 73.7895):
    return weather_service.get_forecast(lat, lon)


# ═══════════════════════════════════════════════════════════════════
# 5. MANDI (10 commodities, 5 APMCs, forecast engine)
# ═══════════════════════════════════════════════════════════════════
@app.get("/api/mandi/prices", tags=["Mandi"])
def api_mandi_prices(commodity: Optional[str] = None, search: str = ""):
    return mandi_service.get_prices(commodity, search)

@app.get("/api/mandi/nearby", tags=["Mandi"])
def api_mandi_nearby(lat: float = 20.0, lon: float = 73.8, sort: str = "nearest"):
    return mandi_service.get_nearby_mandis(lat, lon, sort)

@app.get("/api/mandi/detail/{mandi_name}", tags=["Mandi"])
def api_mandi_detail(mandi_name: str):
    return mandi_service.get_mandi_detail(mandi_name)

@app.get("/api/mandi/forecast", tags=["Mandi"])
def api_mandi_forecast(commodity: str = "onion"):
    return mandi_service.get_forecast(commodity)


# ═══════════════════════════════════════════════════════════════════
# 6. CHEMICAL PRODUCTS (12 products, alternative matching)
# ═══════════════════════════════════════════════════════════════════
@app.get("/api/products/analyze", tags=["Products"])
def api_analyze_product(name: str = "GlyphoMax 41%"):
    return chemical_db.analyze_product(name)

@app.get("/api/products/treatments", tags=["Products"])
def api_get_treatments(disease: str = "late_blight"):
    treatments = chemical_db.get_treatments(disease)
    return {"status": "success", "disease": disease, "treatments": treatments}


# ═══════════════════════════════════════════════════════════════════
# 7. CROP DETECTION (XGBoost — ✅ YOUR MODEL)
# ═══════════════════════════════════════════════════════════════════
@app.post("/api/crop/recommend", tags=["Crop Detection"])
def api_recommend_crop(sensors: str = Form(...)):
    if crop_model is None:
        raise HTTPException(503, "Crop detection model not loaded")
    import numpy as np, pandas as pd
    data = json.loads(sensors)
    defaults = {"N":50,"P":50,"K":50,"temperature":25,"humidity":60,"ph":6.5,"rainfall":100}
    for k,v in defaults.items(): data.setdefault(k, v)
    data["N_P_ratio"]=data["N"]/(data["P"]+1e-5); data["N_K_ratio"]=data["N"]/(data["K"]+1e-5)
    data["P_K_ratio"]=data["P"]/(data["K"]+1e-5); data["THI"]=data["temperature"]*data["humidity"]
    data["water_availability"]=data["rainfall"]*(data["humidity"]/100); data["pH_stress"]=abs(data["ph"]-6.5)
    cols=["N","P","K","temperature","humidity","ph","rainfall","N_P_ratio","N_K_ratio","P_K_ratio","THI","water_availability","pH_stress"]
    X = crop_scaler.transform(pd.DataFrame([data])[cols].values)
    idx = crop_model.predict(X)[0]
    proba = crop_model.predict_proba(X)[0]
    return {"status":"success","recommended_crop":crop_encoder.inverse_transform([idx])[0],
            "confidence":round(float(proba[idx])*100,2)}


# ═══════════════════════════════════════════════════════════════════
# 8. FERTILIZER (Multi-Output XGBoost — ✅ YOUR MODEL)
# ═══════════════════════════════════════════════════════════════════
@app.post("/api/fertilizer/advise", tags=["Fertilizer"])
def api_fertilizer_advise(current_crop: str = Form(...), soil_type: str = Form("clay"),
                          days: int = Form(60), sensors: str = Form(...)):
    if fert_advisor is None:
        raise HTTPException(503, "Fertilizer model not loaded")
    data = json.loads(sensors)
    rec_crop = current_crop
    if crop_model:
        try:
            import pandas as pd
            d = dict(data); defaults={"N":50,"P":50,"K":50,"temperature":25,"humidity":60,"ph":6.5,"rainfall":100}
            for k,v in defaults.items(): d.setdefault(k,v)
            d["N_P_ratio"]=d["N"]/(d["P"]+1e-5); d["N_K_ratio"]=d["N"]/(d["K"]+1e-5)
            d["P_K_ratio"]=d["P"]/(d["K"]+1e-5); d["THI"]=d["temperature"]*d["humidity"]
            d["water_availability"]=d["rainfall"]*(d["humidity"]/100); d["pH_stress"]=abs(d["ph"]-6.5)
            cols=["N","P","K","temperature","humidity","ph","rainfall","N_P_ratio","N_K_ratio","P_K_ratio","THI","water_availability","pH_stress"]
            X=crop_scaler.transform(pd.DataFrame([d])[cols].values)
            rec_crop=crop_encoder.inverse_transform([crop_model.predict(X)[0]])[0]
        except: pass
    report = fert_advisor.generate_report(current_crop, rec_crop, soil_type, days, data)
    return {"status":"success","report":report,"recommended_crop":rec_crop}


# ═══════════════════════════════════════════════════════════════════
# 9. VISION — Leaf Scanner (Roboflow — ✅ YOUR MODEL)
# ═══════════════════════════════════════════════════════════════════
@app.post("/api/vision/scan-leaf", tags=["Vision"])
async def api_scan_leaf(file: UploadFile = File(...)):
    if vision_predictor is None:
        raise HTTPException(503, "Vision service not available. Check ROBOFLOW_API_KEY.")
    img = await file.read()
    if not img: raise HTTPException(400, "Empty file")
    t0 = time.perf_counter()
    result = vision_predictor.scan_image(img)
    result["inference_time_ms"] = int((time.perf_counter()-t0)*1000)
    # Attach treatment recommendations
    disease = result.get("disease", "")
    if disease:
        result["treatments"] = chemical_db.get_treatments(disease)
    return JSONResponse(content=result)


# ═══════════════════════════════════════════════════════════════════
# 10. MITRA AI CHAT (Full pipeline — ✅ YOUR MODEL)
# ═══════════════════════════════════════════════════════════════════
@app.post("/api/mitra/chat", tags=["Mitra"])
async def api_mitra_chat(text: str = Form(...), sensors: str = Form(...),
                         crop: Optional[str] = Form(None), days: Optional[int] = Form(60),
                         image: Optional[UploadFile] = File(None)):
    if mitra_orchestrator is None:
        raise HTTPException(503, "Mitra not available. Ensure Ollama is running.")
    sensor_dict = json.loads(sensors)
    image_bytes = None
    if image:
        image_bytes = await image.read()
        if not image_bytes: image_bytes = None
    t0 = time.perf_counter()
    response = mitra_orchestrator.process_interaction(
        user_text=text, live_sensors=sensor_dict,
        current_crop=crop, days_since_planting=days or 60, image_bytes=image_bytes)
    return {"status":"success","response":response,
            "inference_time_ms":int((time.perf_counter()-t0)*1000)}

@app.get("/api/mitra/history", tags=["Mitra"])
def api_mitra_history(n: int = 10):
    if mitra_orchestrator is None: raise HTTPException(503, "Mitra not ready")
    return {"status":"success","history":mitra_orchestrator.datastore.get_latest_state(n)}

@app.get("/api/mitra/status", tags=["Mitra"])
def api_mitra_status():
    return {"status":"success","models":{"crop":crop_model is not None,"fert":fert_advisor is not None,
                                          "vision":vision_predictor is not None,"mitra":mitra_orchestrator is not None}}


# ═══════════════════════════════════════════════════════════════════
# 11. ALERTS (rule engine + ML-based)
# ═══════════════════════════════════════════════════════════════════
@app.get("/api/alerts", tags=["Alerts"])
def api_get_alerts():
    # Refresh alerts from current sensor data
    telemetry = sensor_store.get_live_telemetry()
    weather = weather_service.get_current()
    sensor_alerts = alert_engine.generate_from_sensors(telemetry["raw_sensors"])
    weather_alerts = alert_engine.generate_from_weather(weather)
    all_alerts = sensor_alerts + weather_alerts + alert_engine.get_all()
    # Deduplicate by title
    seen = set()
    unique = []
    for a in all_alerts:
        if a["title"] not in seen:
            seen.add(a["title"])
            unique.append(a)
    return {"status": "success", "alerts": unique}

@app.post("/api/alerts/read/{alert_id}", tags=["Alerts"])
def api_mark_alert_read(alert_id: str):
    alert_engine.mark_read(alert_id)
    return {"status": "success"}

@app.post("/api/alerts/read-all", tags=["Alerts"])
def api_mark_all_read():
    alert_engine.mark_all_read()
    return {"status": "success"}


# ═══════════════════════════════════════════════════════════════════
# 12. IRRIGATION (sensor-driven + pump control)
# ═══════════════════════════════════════════════════════════════════
@app.get("/api/irrigation/status", tags=["Irrigation"])
def api_irrigation_status():
    return sensor_store.get_irrigation_status()

@app.post("/api/irrigation/pump", tags=["Irrigation"])
def api_control_pump(action: str = Form("start")):
    return sensor_store.control_pump(action)


# ═══════════════════════════════════════════════════════════════════
# 13. TELEMETRY (simulated ESP32 sensors)
# ═══════════════════════════════════════════════════════════════════
@app.get("/api/telemetry/live", tags=["Telemetry"])
def api_telemetry_live():
    return sensor_store.get_live_telemetry()

from pydantic import BaseModel

class TelemetryPayload(BaseModel):
    N: Optional[int] = None
    P: Optional[int] = None
    K: Optional[int] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    ph: Optional[float] = None
    Moisture: Optional[int] = None

@app.post("/api/telemetry/sync", tags=["Telemetry"])
def api_telemetry_sync(payload: TelemetryPayload = None):
    if payload:
        # Save hardware payload so get_live_telemetry() returns real data
        sensor_store.last_hardware_data = payload.dict(exclude_none=True)
        return {"status": "success", "message": "Hardware telemetry synced", "data": sensor_store.last_hardware_data}
    return sensor_store.sync()
