"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  SmartAgri · Vision API Server                                               ║
║  FastAPI backend for leaf disease detection via Roboflow.                     ║
║                                                                              ║
║  RUN:                                                                        ║
║    uvicorn src.vision.main:app --reload --port 8000                          ║
║                                                                              ║
║  TEST:                                                                       ║
║    curl -X POST http://localhost:8000/api/vision/scan-leaf                    ║
║         -F "file=@my_leaf_photo.jpg"                                         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import logging
import time

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.vision.roboflow_client import CloudVisionPredictor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# APP SETUP
# ─────────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="SmartAgri Vision API",
    description="Leaf disease detection powered by Roboflow serverless inference.",
    version="1.0.0",
)

# Allow mobile app / frontend to hit this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Initialise the vision predictor once at startup ──────────────────────────
predictor: CloudVisionPredictor | None = None


@app.on_event("startup")
def startup_load_model():
    """Load the Roboflow client once when the server boots."""
    global predictor
    try:
        predictor = CloudVisionPredictor()
        log.info("Vision predictor ready.")
    except EnvironmentError as e:
        log.error("Failed to initialise predictor: %s", e)
        # Server will still start but the endpoint will return 503


# ─────────────────────────────────────────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def health_check():
    """Simple liveness probe for the mobile app / load balancer."""
    return {
        "service": "SmartAgri Vision API",
        "status": "online",
        "model_loaded": predictor is not None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENDPOINT — POST /api/vision/scan-leaf
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/vision/scan-leaf", tags=["Vision"])
async def scan_leaf(file: UploadFile = File(...)):
    """
    Accepts an image upload from the mobile app, runs it through the
    Roboflow leaf-disease segmentation workflow, and returns:

    ```json
    {
        "status": "success",
        "disease": "Tomato___Late_blight",
        "confidence": 0.9712,
        "inference_time_ms": 1423
    }
    ```

    Error responses use HTTP 500 / 503 with a structured body so the
    mobile client can display a user-friendly message without crashing.
    """

    # ── Guard: predictor must be loaded ───────────────────────────────────
    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "message": "Vision service is not available. "
                           "Check ROBOFLOW_API_KEY in .env.",
                "code": "SERVICE_UNAVAILABLE",
            },
        )

    # ── Validate the upload ──────────────────────────────────────────────
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": f"Expected an image file, got '{file.content_type}'.",
                "code": "INVALID_FILE_TYPE",
            },
        )

    try:
        # ── Read the uploaded bytes ──────────────────────────────────────
        image_bytes = await file.read()

        if len(image_bytes) == 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "error",
                    "message": "Uploaded file is empty.",
                    "code": "EMPTY_FILE",
                },
            )

        log.info(
            "Received image: %s (%d bytes, %s)",
            file.filename, len(image_bytes), file.content_type,
        )

        # ── Run inference ────────────────────────────────────────────────
        t0 = time.perf_counter()
        result = predictor.scan_image(image_bytes)
        elapsed_ms = int((time.perf_counter() - t0) * 1000)

        result["inference_time_ms"] = elapsed_ms
        log.info("Inference complete in %d ms → %s", elapsed_ms, result)

        return JSONResponse(content=result, status_code=200)

    # ── Handle network timeouts ──────────────────────────────────────────
    except TimeoutError as e:
        log.error("Roboflow API timeout: %s", e)
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "message": "The vision API timed out. Please try again.",
                "code": "TIMEOUT",
            },
        )

    except ConnectionError as e:
        log.error("Network error reaching Roboflow: %s", e)
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "message": "Could not reach the vision service. "
                           "Check your internet connection.",
                "code": "CONNECTION_ERROR",
            },
        )

    # ── Handle Roboflow rate limits (HTTP 429 wrapped in exceptions) ─────
    except Exception as e:
        error_str = str(e).lower()

        # Roboflow rate-limit responses usually contain "429" or "rate"
        if "429" in error_str or "rate" in error_str:
            log.warning("Roboflow rate limit hit: %s", e)
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "error",
                    "message": "Vision API rate limit reached. "
                               "Please wait a moment and try again.",
                    "code": "RATE_LIMITED",
                },
            )

        # ── Catch-all for unexpected errors ──────────────────────────────
        log.exception("Unexpected error during leaf scan:")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "An unexpected error occurred during image analysis.",
                "code": "INTERNAL_ERROR",
                "details": str(e),
            },
        )
