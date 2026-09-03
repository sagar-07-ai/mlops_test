import logging

from fastapi import FastAPI, File, HTTPException, UploadFile, status

from app.config import (
    MAX_UPLOAD_BYTES,
    MAX_UPLOAD_MIB,
    RESIZED_HEIGHT,
    RESIZED_WIDTH,
    SUPPORTED_CONTENT_TYPES,
)
from app.image_service import InvalidImageError, process_image
from app.schemas import (
    HealthResponse,
    ImageDetailsResponse,
    OriginalImage,
    ResizedImage,
)


logger = logging.getLogger(__name__)

app = FastAPI(
    title="Image Details API",
    description="Lightweight image metadata and resize service for CI/CD testing.",
    version="1.0.0",
)


@app.get("/livez", response_model=HealthResponse)
async def liveness() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/readyz", response_model=HealthResponse)
async def readiness() -> HealthResponse:
    return HealthResponse(status="ready")


@app.post(
    "/api/v1/images/details",
    response_model=ImageDetailsResponse,
    status_code=status.HTTP_200_OK,
)
async def image_details(file: UploadFile = File(...)) -> ImageDetailsResponse:
    content_type = (file.content_type or "").lower()
    if content_type not in SUPPORTED_CONTENT_TYPES:
        supported = ", ".join(sorted(SUPPORTED_CONTENT_TYPES))
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Supported content types: {supported}.",
        )

    try:
        image_bytes = await file.read(MAX_UPLOAD_BYTES + 1)
    finally:
        await file.close()

    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Uploaded file exceeds {MAX_UPLOAD_MIB} MiB.",
        )

    try:
        processed = process_image(image_bytes)
    except InvalidImageError:
        logger.info("Rejected invalid image upload")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is not a valid image.",
        ) from None

    return ImageDetailsResponse(
        filename=file.filename or "upload",
        content_type=content_type,
        size_bytes=len(image_bytes),
        original=OriginalImage(
            width=processed.width,
            height=processed.height,
            format=processed.format,
            mode=processed.mode,
        ),
        resized=ResizedImage(
            width=RESIZED_WIDTH,
            height=RESIZED_HEIGHT,
            media_type="image/png",
            base64=processed.resized_base64,
        ),
    )
