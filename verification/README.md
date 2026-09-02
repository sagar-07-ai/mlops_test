# Verification service

- Compute: NVIDIA GPU
- Port: 8400
- Health: `GET /healthz`
- Verification: `POST /verify` with a multipart `image` and form field `eye_type`
- Active models: fundus, left/right classification, and optic-disc YOLO models

