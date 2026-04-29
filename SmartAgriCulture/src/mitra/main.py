"""
==============================================================================
  SmartAgri · Mitra API Server
  ────────────────────────────
  FastAPI backend exposing:
    POST /api/mitra/chat     — Main agentic endpoint (text+sensors+image)
    GET  /api/mitra/history  — View ledger history
    GET  /api/mitra/profile  — View user profile
    GET  /api/mitra/status   — GPU + model status
    GET  /                   — Health check

  RUN:
    uvicorn src.mitra.main:app --reload --port 8001
==============================================================================
"""

import json
import logging
import time

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional

from src.mitra.mitra_brain import MitraOrchestrator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────
# APP SETUP
# ─────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="SmartAgri Mitra API",
    description=(
        "Agentic AI farming assistant — routes user queries through "
        "Vision AI, Crop Detection, Fertilizer Optimization, and a "
        "local LLM (gpt4o-s:20b via Ollama). VRAM-aware for 8GB GPUs."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mitra: MitraOrchestrator | None = None


@app.on_event("startup")
def startup():
    global mitra
    try:
        mitra = MitraOrchestrator()
        log.info("Mitra Orchestrator is ONLINE.")
    except Exception as e:
        log.error("Failed to initialise Mitra: %s", e)


# ─────────────────────────────────────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def health_check():
    return {
        "service": "SmartAgri Mitra API",
        "status": "online",
        "orchestrator_ready": mitra is not None,
        "models": {
            "crop_detection": mitra.crop_model is not None if mitra else False,
            "fertilizer_optimization": mitra.fert_pipeline is not None if mitra else False,
        },
    }


# ─────────────────────────────────────────────────────────────────────────
# POST /api/mitra/chat — Main agentic endpoint
# ─────────────────────────────────────────────────────────────────────────
@app.post("/api/mitra/chat", tags=["Mitra"])
async def mitra_chat(
    text: str = Form(..., description="The farmer's question or statement"),
    sensors: str = Form(
        ...,
        description='JSON string of sensor readings, e.g. {"N":80,"P":45,"K":40,"temperature":25}'
    ),
    crop: Optional[str] = Form(None, description="Current crop being grown"),
    days: Optional[int] = Form(60, description="Days since planting"),
    image: Optional[UploadFile] = File(None, description="Optional photo for disease/soil detection"),
):
    """
    The central Mitra agentic endpoint.
    Accepts text + JSON sensors + optional image via multipart form data.
    Returns a farmer-friendly AI response.
    """
    if mitra is None:
        raise HTTPException(status_code=503, detail={
            "status": "error",
            "message": "Mitra is not available. Models may still be loading.",
        })

    # Parse sensor JSON
    try:
        sensor_dict = json.loads(sensors)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail={
            "status": "error",
            "message": "Invalid JSON in 'sensors' field.",
        })

    # Read image bytes if provided
    image_bytes = None
    if image is not None:
        image_bytes = await image.read()
        if len(image_bytes) == 0:
            image_bytes = None
        else:
            log.info("Received image: %s (%d bytes)", image.filename, len(image_bytes))

    # Run the full pipeline
    try:
        t0 = time.perf_counter()
        response_text = mitra.process_interaction(
            user_text=text,
            live_sensors=sensor_dict,
            current_crop=crop,
            days_since_planting=days or 60,
            image_bytes=image_bytes,
        )
        elapsed_ms = int((time.perf_counter() - t0) * 1000)

        return JSONResponse(content={
            "status": "success",
            "response": response_text,
            "inference_time_ms": elapsed_ms,
        }, status_code=200)

    except Exception as e:
        log.exception("Mitra pipeline error:")
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "message": "An error occurred during processing.",
            "details": str(e),
        })


# ─────────────────────────────────────────────────────────────────────────
# GET /api/mitra/history — Ledger history
# ─────────────────────────────────────────────────────────────────────────
@app.get("/api/mitra/history", tags=["Mitra"])
def get_history(n: int = 10):
    """Returns the last n entries from the unified farm ledger."""
    if mitra is None:
        raise HTTPException(status_code=503, detail="Mitra not ready.")
    rows = mitra.datastore.get_latest_state(n)
    return {"status": "success", "count": len(rows), "history": rows}


# ─────────────────────────────────────────────────────────────────────────
# GET /api/mitra/profile — User profile
# ─────────────────────────────────────────────────────────────────────────
@app.get("/api/mitra/profile", tags=["Mitra"])
def get_profile():
    """Returns the AI-managed user profile."""
    if mitra is None:
        raise HTTPException(status_code=503, detail="Mitra not ready.")
    profile = mitra.datastore.get_user_profile()
    return {"status": "success", "profile": profile}


# ─────────────────────────────────────────────────────────────────────────
# GET /api/mitra/status — GPU + model status
# ─────────────────────────────────────────────────────────────────────────
@app.get("/api/mitra/status", tags=["Mitra"])
def get_status():
    """Returns GPU memory status and model readiness."""
    if mitra is None:
        raise HTTPException(status_code=503, detail="Mitra not ready.")
    gpu = mitra.vram.get_gpu_status()
    return {
        "status": "success",
        "gpu": gpu,
        "models": {
            "crop_detection": mitra.crop_model is not None,
            "fertilizer_optimization": mitra.fert_pipeline is not None,
            "vision_loaded": mitra.vision_predictor is not None,
        },
        "ledger_rows": mitra.datastore.get_row_count(),
    }
