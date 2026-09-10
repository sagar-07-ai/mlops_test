import base64
import io

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app


client = TestClient(app)


def png_bytes(width: int = 320, height: int = 180) -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (width, height), color=(20, 80, 140)).save(output, "PNG")
    return output.getvalue()


def test_liveness() -> None:
    response = client.get("/livez")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness() -> None:
    response = client.get("/readyz")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_image_details_returns_metadata_and_100_by_100_png() -> None:
    content = png_bytes()

    response = client.post(
        "/api/v1/images/details",
        files={"file": ("retina.png", content, "image/png")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "retina.png"
    assert body["content_type"] == "image/png"
    assert body["size_bytes"] == len(content)
    assert body["original"] == {
        "width": 320,
        "height": 180,
        "format": "PNG",
        "mode": "RGB",
    }
    assert body["resized"]["width"] == 100
    assert body["resized"]["height"] == 100
    assert body["resized"]["media_type"] == "image/png"

    resized_bytes = base64.b64decode(body["resized"]["base64"])
    with Image.open(io.BytesIO(resized_bytes)) as resized:
        assert resized.size == (100, 100)
        assert resized.format == "PNG"


def test_empty_upload_is_rejected() -> None:
    response = client.post(
        "/api/v1/images/details",
        files={"file": ("empty.png", b"", "image/png")},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Uploaded file is empty."}


def test_invalid_image_is_rejected_without_internal_details() -> None:
    response = client.post(
        "/api/v1/images/details",
        files={"file": ("fake.png", b"not-an-image", "image/png")},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Uploaded file is not a valid image."}


def test_unsupported_media_type_is_rejected() -> None:
    response = client.post(
        "/api/v1/images/details",
        files={"file": ("image.gif", b"GIF89a", "image/gif")},
    )

    assert response.status_code == 415
    assert response.json() == {
        "detail": "Supported content types: image/jpeg, image/png, image/webp."
    }


def test_oversized_upload_is_rejected() -> None:
    response = client.post(
        "/api/v1/images/details",
        files={"file": ("large.png", b"x" * (10 * 1024 * 1024 + 1), "image/png")},
    )

    assert response.status_code == 413
    assert response.json() == {"detail": "Uploaded file exceeds 10 MiB."}


def test_missing_upload_is_rejected() -> None:
    response = client.post("/api/v1/images/details")

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "file"]
