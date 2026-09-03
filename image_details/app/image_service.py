import base64
import io
from dataclasses import dataclass

from PIL import Image, ImageOps, UnidentifiedImageError

from app.config import RESIZED_HEIGHT, RESIZED_WIDTH


class InvalidImageError(ValueError):
    """Raised when uploaded bytes cannot be decoded safely as an image."""


@dataclass(frozen=True)
class ProcessedImage:
    width: int
    height: int
    format: str
    mode: str
    resized_base64: str


def process_image(image_bytes: bytes) -> ProcessedImage:
    try:
        with Image.open(io.BytesIO(image_bytes)) as source:
            source.verify()

        with Image.open(io.BytesIO(image_bytes)) as source:
            width, height = source.size
            image_format = source.format or "UNKNOWN"
            image_mode = source.mode
            normalized = ImageOps.exif_transpose(source).convert("RGB")
            resized = normalized.resize(
                (RESIZED_WIDTH, RESIZED_HEIGHT),
                Image.Resampling.LANCZOS,
            )

            output = io.BytesIO()
            resized.save(output, format="PNG", optimize=True)
    except (Image.DecompressionBombError, UnidentifiedImageError, OSError, ValueError) as exc:
        raise InvalidImageError("Uploaded file is not a valid image.") from exc

    return ProcessedImage(
        width=width,
        height=height,
        format=image_format,
        mode=image_mode,
        resized_base64=base64.b64encode(output.getvalue()).decode("ascii"),
    )
