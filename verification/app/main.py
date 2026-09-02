import logging
import time

import torch
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from config import API_HOST, API_PORT, DEVICE
from inference import (
    load_models, check_fundus, check_eye_type, check_disc_visible,
    validate_image, InvalidImageError,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Image Verification API",
    description="Fundus validation, eye-side verification, and optic disc visibility check",
    version="1.0.0",
)

assets = None


# ── startup / shutdown ────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    global assets
    device = DEVICE if torch.cuda.is_available() else "cpu"
    logger.info(f"Loading models on {device} ...")
    assets = load_models(device)
    logger.info("All models loaded.")


@app.on_event("shutdown")
async def shutdown():
    global assets
    assets = None


# ── verify endpoint ───────────────────────────────────────────────────────────

@app.post("/verify")
async def verify(
    file: UploadFile = File(...),
    type: str = Form(...),
):
    if assets is None:
        raise HTTPException(status_code=503, detail="Models not loaded")

    if type.lower() not in ("left", "right"):
        raise HTTPException(status_code=422, detail="type must be 'left' or 'right'")

    start = time.perf_counter()
    image_bytes = await file.read()

    try:
        validate_image(image_bytes)
    except InvalidImageError as exc:
        return JSONResponse(content={
            "prediction":   None,
            "isTypeValid":  None,
            "disc_visible": None,
            "error":        str(exc),
        })

    # Step 1: fundus check
    prediction = check_fundus(image_bytes, assets)
    if prediction == 0:
        return JSONResponse(content={
            "prediction":          0,
            "isTypeValid":         None,
            "disc_visible":        None,
            "processing_time_ms":  round((time.perf_counter() - start) * 1000, 2),
        })

    # Steps 2 & 3: run both regardless of each other's result
    is_type_valid = check_eye_type(image_bytes, type, assets)
    disc_visible  = check_disc_visible(image_bytes, assets)

    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    logger.info(f"verify completed in {elapsed_ms} ms")

    return JSONResponse(content={
        "prediction":          1,
        "isTypeValid":         is_type_valid,
        "disc_visible":        disc_visible,
        "processing_time_ms":  elapsed_ms,
    })


# ── health ────────────────────────────────────────────────────────────────────

@app.get("/healthz")
async def health():
    return {
        "status":        "ok",
        "models_loaded": assets is not None,
        "device":        assets["device"] if assets else None,
    }


@app.get("/")
async def root():
    return {
        "name":    "Image Verification API",
        "version": "1.0.0",
        "endpoint": "POST /verify  (form-data: file, type)",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)
