import base64
import io

import pytest
from PIL import Image

from app.image_service import InvalidImageError, process_image


def image_bytes(
    image_format: str = "PNG",
    width: int = 48,
    height: int = 32,
) -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (width, height), color=(25, 100, 175)).save(
        output,
        format=image_format,
    )
    return output.getvalue()


def test_process_image_preserves_metadata_and_returns_png() -> None:
    result = process_image(image_bytes(width=48, height=32))

    assert result.width == 48
    assert result.height == 32
    assert result.format == "PNG"
    assert result.mode == "RGB"

    resized_bytes = base64.b64decode(result.resized_base64, validate=True)
    with Image.open(io.BytesIO(resized_bytes)) as resized:
        assert resized.size == (100, 100)
        assert resized.format == "PNG"
        assert resized.mode == "RGB"


@pytest.mark.parametrize("image_format", ["PNG", "JPEG", "WEBP"])
def test_process_image_accepts_supported_image_formats(image_format: str) -> None:
    result = process_image(image_bytes(image_format=image_format))

    assert result.format == image_format


def test_process_image_rejects_malformed_bytes() -> None:
    with pytest.raises(InvalidImageError):
        process_image(b"not-an-image")
