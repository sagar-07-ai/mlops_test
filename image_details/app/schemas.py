from pydantic import BaseModel, Field


class OriginalImage(BaseModel):
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    format: str
    mode: str


class ResizedImage(BaseModel):
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    media_type: str
    base64: str


class ImageDetailsResponse(BaseModel):
    filename: str
    content_type: str
    size_bytes: int = Field(gt=0)
    original: OriginalImage
    resized: ResizedImage


class HealthResponse(BaseModel):
    status: str
