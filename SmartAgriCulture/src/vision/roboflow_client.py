"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  SmartAgri · Cloud Vision Service                                           ║
║  Roboflow Workflow API client for leaf disease detection.                    ║
║                                                                              ║
║  Uses direct HTTP requests to the Roboflow Serverless API instead of the     ║
║  inference_sdk package (which requires Python <3.13).  This is functionally  ║
║  identical to client.run_workflow() but works on any Python version.         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import base64
import tempfile
import logging
import httpx

from dotenv import load_dotenv

# Load environment variables from .env at project root
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# Roboflow workflow endpoint template
WORKFLOW_URL = (
    "https://serverless.roboflow.com"
    "/{workspace}/workflows/{workflow_id}"
)


class CloudVisionPredictor:
    """
    Wraps the Roboflow Serverless Workflow API to provide a clean
    scan_image(image_bytes) → dict interface for the FastAPI layer.

    Equivalent to InferenceHTTPClient.run_workflow() but uses direct
    HTTP calls via httpx — no Python version constraint.
    """

    def __init__(self):
        # ── Pull API key securely from environment ────────────────────────
        self.api_key = os.getenv("ROBOFLOW_API_KEY")
        if not self.api_key:
            raise EnvironmentError(
                "ROBOFLOW_API_KEY is not set. "
                "Add it to your .env file:  ROBOFLOW_API_KEY=your_key_here"
            )

        # Roboflow workspace / workflow identifiers
        self.workspace = "pranav-dubey"
        self.workflow_disease = "general-segmentation-api"
        self.workflow_soil = "general-segmentation-api-2"

        # Build the workflow URLs
        self.url_disease = WORKFLOW_URL.format(
            workspace=self.workspace,
            workflow_id=self.workflow_disease,
        )
        self.url_soil = WORKFLOW_URL.format(
            workspace=self.workspace,
            workflow_id=self.workflow_soil,
        )

        # Reusable HTTP client with generous timeout for large images
        self.http_client = httpx.Client(timeout=60.0)

        log.info(
            "CloudVisionPredictor initialised (workspace=%s, disease=%s, soil=%s)",
            self.workspace, self.workflow_disease, self.workflow_soil,
        )

    # ─────────────────────────────────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────────────────────────────────
    def scan_image(self, image_bytes: bytes) -> dict:
        """
        Accepts raw image bytes (e.g. from a mobile upload), sends them
        to the Roboflow serverless workflow, and returns a clean result.

        Returns
        -------
        dict
            {
                "status": "success",
                "disease": "Predicted_Class_Name",
                "confidence": 0.98
            }
            or
            {
                "status": "no_detection",
                "disease": None,
                "confidence": 0.0,
                "message": "No disease class detected in the image."
            }
        """
        log.info("Scanning image (%d bytes)...", len(image_bytes))

        # ── 1. Encode image as base64 for the API payload ─────────────
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        # ── 2. Build the payloads ─────────────────────────────────────
        payload_disease = {
            "api_key": self.api_key,
            "inputs": {
                "image": {
                    "type": "base64",
                    "value": image_b64,
                }
            },
            "use_cache": True,
        }
        
        payload_soil = {
            "api_key": self.api_key,
            "inputs": {
                "image": {
                    "type": "base64",
                    "value": image_b64,
                }
            },
            "parameters": {
                "classes": "red, yellow, clay"
            },
            "use_cache": True,
        }

        # ── 3. Call the Roboflow workflows ────────────────────────────
        # We do this sequentially for simplicity, but could be parallelized
        try:
            resp_disease = self.http_client.post(self.url_disease, json=payload_disease)
            if resp_disease.status_code == 429:
                raise RuntimeError("429 rate limit exceeded for disease workflow.")
            resp_disease.raise_for_status()
            result_disease = resp_disease.json()
        except Exception as e:
            log.error(f"Disease detection failed: {e}")
            result_disease = {}

        try:
            resp_soil = self.http_client.post(self.url_soil, json=payload_soil)
            if resp_soil.status_code == 429:
                raise RuntimeError("429 rate limit exceeded for soil workflow.")
            resp_soil.raise_for_status()
            result_soil = resp_soil.json()
        except Exception as e:
            log.error(f"Soil detection failed: {e}")
            result_soil = {}

        # ── 4. Parse the responses ────────────────────────────────────
        disease_parsed = self._parse_response(result_disease, default_msg="No disease class detected in the image.")
        soil_parsed = self._parse_response(result_soil, default_msg="No soil type detected in the image.")

        return {
            "status": "success",
            "disease": disease_parsed.get("class_name"),
            "disease_confidence": disease_parsed.get("confidence", 0.0),
            "soil_type": soil_parsed.get("class_name"),
            "soil_confidence": soil_parsed.get("confidence", 0.0)
        }

    # ─────────────────────────────────────────────────────────────────────
    # PRIVATE HELPERS
    # ─────────────────────────────────────────────────────────────────────
    @staticmethod
    def _parse_response(result, default_msg: str) -> dict:
        """
        Walks the Roboflow workflow JSON to find the prediction with
        the highest confidence score.
        """
        best_class = None
        best_confidence = 0.0

        # ── Normalise to a list if the SDK returns a single dict ──────
        if isinstance(result, dict):
            items = [result]
        elif isinstance(result, list):
            items = result
        else:
            return {
                "status": "error",
                "class_name": None,
                "confidence": 0.0,
                "message": f"Unexpected response type: {type(result).__name__}",
            }

        # ── Recursively search for prediction objects ─────────────────
        for item in items:
            predictions = _extract_predictions(item)
            for pred in predictions:
                cls_name = pred.get("class", pred.get("class_name", ""))
                conf = float(pred.get("confidence", 0.0))
                if conf > best_confidence:
                    best_confidence = conf
                    best_class = cls_name

        if best_class is None:
            return {
                "status": "no_detection",
                "class_name": None,
                "confidence": 0.0,
                "message": default_msg,
            }

        return {
            "status": "success",
            "class_name": best_class,
            "confidence": round(best_confidence, 4),
        }


# ─────────────────────────────────────────────────────────────────────────
# Module-level helper: recursively pull prediction dicts out of the
# nested workflow response (handles varying Roboflow response shapes).
# ─────────────────────────────────────────────────────────────────────────
def _extract_predictions(obj, _depth: int = 0) -> list:
    """
    Recursively searches a nested dict/list for objects that look like
    predictions (contain 'class'/'class_name' + 'confidence').
    """
    if _depth > 10:  # guard against absurd nesting
        return []

    found = []

    if isinstance(obj, dict):
        # Does this dict itself look like a prediction?
        if ("class" in obj or "class_name" in obj) and "confidence" in obj:
            found.append(obj)

        # Also recurse into every value
        for value in obj.values():
            found.extend(_extract_predictions(value, _depth + 1))

    elif isinstance(obj, list):
        for element in obj:
            found.extend(_extract_predictions(element, _depth + 1))

    return found
