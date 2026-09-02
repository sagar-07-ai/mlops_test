import os
from pathlib import Path

MODEL_DIR = Path(os.getenv("MODEL_DIR", "/app/weights"))

FUNDUS_MODEL_PATH  = MODEL_DIR / "scripted_model.pt"
LR_MODEL_PATH      = MODEL_DIR / "lr_classifier_b3.pt"
YOLO_MODEL_PATH    = MODEL_DIR / "best1.pt"

DEVICE = os.getenv("DEVICE", "cuda")

FUNDUS_IMAGE_SIZE = 224
LR_IMAGE_SIZE     = 600

# ImageNet stats used during LR model training
LR_MEAN = (0.485, 0.456, 0.406)
LR_STD  = (0.229, 0.224, 0.225)

# Fundus model normalisation
FUNDUS_MEAN = (0.5, 0.5, 0.5)
FUNDUS_STD  = (0.5, 0.5, 0.5)

# YOLO thresholds
YOLO_CONF = float(os.getenv("YOLO_CONF", 0.3))
YOLO_IOU  = float(os.getenv("YOLO_IOU",  0.5))

# Disc detection inference size. Large uploads lose the optic disc when
# downscaled to 640, so images whose height or width exceeds YOLO_LARGE_DIM
# are run at the larger YOLO_IMGSZ_LARGE instead. Everything else uses 640.
YOLO_IMGSZ       = int(os.getenv("YOLO_IMGSZ", 640))
YOLO_IMGSZ_LARGE = int(os.getenv("YOLO_IMGSZ_LARGE", 1280))
YOLO_LARGE_DIM   = int(os.getenv("YOLO_LARGE_DIM", 3000))

API_HOST    = os.getenv("HOST", "127.0.0.1")
API_PORT    = int(os.getenv("PORT", 8400))
