import io
import logging

import cv2
import numpy as np
import torch
from PIL import Image
from ultralytics import YOLO

from config import (
    FUNDUS_IMAGE_SIZE, FUNDUS_MEAN, FUNDUS_STD,
    LR_IMAGE_SIZE, LR_MEAN, LR_STD,
    YOLO_CONF, YOLO_IOU, YOLO_IMGSZ, YOLO_IMGSZ_LARGE, YOLO_LARGE_DIM,
    FUNDUS_MODEL_PATH, LR_MODEL_PATH, YOLO_MODEL_PATH,
)

logger = logging.getLogger(__name__)


def load_models(device: str) -> dict:
    logger.info(f"Loading models on device: {device}")

    fundus_model = torch.jit.load(str(FUNDUS_MODEL_PATH), map_location=device)
    fundus_model.eval()
    logger.info("Fundus model loaded")

    lr_model = torch.jit.load(str(LR_MODEL_PATH), map_location=device)
    lr_model.eval()
    logger.info("L/R classifier loaded")

    yolo_model = YOLO(str(YOLO_MODEL_PATH))
    yolo_model.to(device)
    logger.info("YOLO disc model loaded")

    return {
        "device":       device,
        "fundus_model": fundus_model,
        "lr_model":     lr_model,
        "yolo_model":   yolo_model,
    }


# ── helpers ──────────────────────────────────────────────────────────────────

def _bytes_to_pil(image_bytes: bytes) -> Image.Image:
    return Image.open(io.BytesIO(image_bytes)).convert("RGB")


def _bytes_to_bgr(image_bytes: bytes) -> np.ndarray:
    arr = np.frombuffer(image_bytes, np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


class InvalidImageError(ValueError):
    """Raised when uploaded bytes cannot be decoded as an image."""


def validate_image(image_bytes: bytes) -> None:
    """Raise InvalidImageError if `image_bytes` cannot be decoded as an image.

    Checked once up front so a malformed upload fails cleanly instead of
    raising an unhandled PIL.UnidentifiedImageError deep inside check_fundus().
    """
    try:
        _bytes_to_pil(image_bytes)
    except Exception as exc:
        raise InvalidImageError("Uploaded file is not a valid image.") from exc


def _preprocess_fundus(image_bytes: bytes, device: str) -> torch.Tensor:
    img = _bytes_to_pil(image_bytes)
    img = img.resize((FUNDUS_IMAGE_SIZE, FUNDUS_IMAGE_SIZE))

    arr = np.array(img, dtype=np.float32) / 255.0
    mean = np.array(FUNDUS_MEAN, dtype=np.float32)
    std  = np.array(FUNDUS_STD,  dtype=np.float32)
    arr  = (arr - mean) / std
    tensor = torch.from_numpy(arr.transpose(2, 0, 1)).unsqueeze(0).to(device)
    return tensor


def _preprocess_lr(image_bytes: bytes, device: str) -> torch.Tensor:
    bgr = _bytes_to_bgr(image_bytes)
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    rgb = cv2.resize(rgb, (LR_IMAGE_SIZE, LR_IMAGE_SIZE))

    arr  = rgb.astype(np.float32) / 255.0
    mean = np.array(LR_MEAN, dtype=np.float32)
    std  = np.array(LR_STD,  dtype=np.float32)
    arr  = (arr - mean) / std
    tensor = torch.from_numpy(arr.transpose(2, 0, 1)).unsqueeze(0).to(device)
    return tensor


# ── step 1: fundus check ─────────────────────────────────────────────────────

def check_fundus(image_bytes: bytes, assets: dict) -> int:
    """Returns 1 if fundus image, 0 otherwise."""
    tensor = _preprocess_fundus(image_bytes, assets["device"])
    with torch.no_grad():
        output = assets["fundus_model"](tensor)
        pred = int(torch.argmax(output, dim=1).item())
    return pred


# ── step 2: L/R eye type check ───────────────────────────────────────────────

# ImageFolder sorts classes alphabetically: left=0, right=1
_LR_CLASSES = ["left", "right"]

def check_eye_type(image_bytes: bytes, claimed_type: str, assets: dict) -> bool:
    """Returns True if detected eye side matches claimed_type."""
    tensor = _preprocess_lr(image_bytes, assets["device"])
    with torch.no_grad():
        output = assets["lr_model"](tensor)
        pred_idx = int(torch.argmax(output, dim=1).item())
    detected = _LR_CLASSES[pred_idx]
    return detected == claimed_type.lower()


# ── step 3: optic disc visibility ────────────────────────────────────────────

def check_disc_visible(image_bytes: bytes, assets: dict) -> bool:
    """Returns True if optic disc is detected by YOLO.

    Inference size is chosen by image dimensions: large uploads (height or
    width above YOLO_LARGE_DIM) run at YOLO_IMGSZ_LARGE so the disc survives
    downscaling; everything else runs at the standard YOLO_IMGSZ.
    """
    bgr = _bytes_to_bgr(image_bytes)
    if bgr is None or bgr.size == 0:
        return False

    h, w = bgr.shape[:2]
    # imgsz = YOLO_IMGSZ_LARGE if max(h, w) > YOLO_LARGE_DIM else YOLO_IMGSZ
    imgsz = YOLO_IMGSZ
    results = assets["yolo_model"](
        bgr, conf=YOLO_CONF, iou=YOLO_IOU, imgsz=imgsz, verbose=False
    )[0]
    return results.boxes is not None and len(results.boxes) > 0
