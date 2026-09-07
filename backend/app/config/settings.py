"""Backend configuration settings for Netra FastAPI app."""

import os
from pathlib import Path
from pydantic import BaseModel

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent

class Settings(BaseModel):
    PROJECT_NAME: str = "Netra DR Screening API"
    VERSION: str = "1.0.0"
    MAX_UPLOAD_SIZE_MB: int = 15
    ALLOWED_CONTENT_TYPES: list[str] = ["image/jpeg", "image/png", "image/bmp"]
    OUTPUTS_DIR: Path = ROOT_DIR / "outputs"
    STATIC_DIR: Path = ROOT_DIR / "outputs"

settings = Settings()
