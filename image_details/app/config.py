import os


MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", 10 * 1024 * 1024))
MAX_UPLOAD_MIB = MAX_UPLOAD_BYTES // (1024 * 1024)
RESIZED_WIDTH = 100
RESIZED_HEIGHT = 100
SUPPORTED_CONTENT_TYPES = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/webp",
    }
)
