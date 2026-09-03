# Image Details API

A lightweight FastAPI service for exercising the CI/CD pipeline without CUDA,
Torch, model weights, or inference dependencies.

## API

```text
GET  /livez
GET  /readyz
POST /api/v1/images/details  (multipart field: file)
```

Accepted upload types are JPEG, PNG, and WebP. Uploads are limited to 10 MiB.
The response contains original image metadata and an exact 100x100 PNG encoded
as Base64.

Example response shape:

```json
{
  "filename": "sample.png",
  "content_type": "image/png",
  "size_bytes": 612,
  "original": {
    "width": 320,
    "height": 180,
    "format": "PNG",
    "mode": "RGB"
  },
  "resized": {
    "width": 100,
    "height": 100,
    "media_type": "image/png",
    "base64": "iVBORw0KGgo..."
  }
}
```

## Test locally

```bash
cd /home/sagar/Desktop/MLOPS/mlops_test/image_details
python3 -m venv .venv
.venv/bin/python -m pip install --requirement requirements-dev.txt
.venv/bin/pytest tests -q
```

## Build and run

```bash
cd /home/sagar/Desktop/MLOPS/mlops_test
docker build -t image-details-service:test image_details
docker run --rm -d \
  --name image-details-service \
  -p 127.0.0.1:8000:8000 \
  image-details-service:test
```

Check health:

```bash
curl -fsS http://127.0.0.1:8000/livez
curl -fsS http://127.0.0.1:8000/readyz
```

Upload an image:

```bash
curl -fsS \
  -F 'file=@/absolute/path/to/sample.png;type=image/png' \
  http://127.0.0.1:8000/api/v1/images/details
```

Stop the demo container:

```bash
docker stop image-details-service
```
