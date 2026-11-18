"""Core application configuration using Pydantic Settings and environment variables."""

import os
from pathlib import Path
from typing import List
from pydantic import BaseModel, Field

# Root directory of the repository
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseModel):
    """Application runtime settings with environment variable override support."""

    PROJECT_NAME: str = "Netra Retinal Screening & Telemedicine Platform"
    VERSION: str = "2.0.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = Field(default_factory=lambda: os.getenv("NETRA_DEBUG", "false").lower() == "true")

    # Host & Port
    HOST: str = Field(default_factory=lambda: os.getenv("NETRA_HOST", "0.0.0.0"))
    PORT: int = Field(default_factory=lambda: int(os.getenv("NETRA_PORT", "8000")))

    # Security & CORS
    CORS_ORIGINS: List[str] = ["*"]
    MAX_UPLOAD_SIZE_MB: int = Field(default_factory=lambda: int(os.getenv("NETRA_MAX_UPLOAD_MB", "15")))
    ALLOWED_CONTENT_TYPES: List[str] = ["image/jpeg", "image/png", "image/bmp"]

    # Storage paths
    OUTPUTS_DIR: Path = ROOT_DIR / "outputs"
    STATIC_DIR: Path = ROOT_DIR / "outputs"
    MODELS_DIR: Path = ROOT_DIR / "models"
    DATA_DIR: Path = ROOT_DIR / "data"

    # Model Weights
    PRIMARY_MODEL_PATH: Path = ROOT_DIR / "models" / "best_model_aptos_ddr.pth"
    FALLBACK_MODEL_PATH: Path = ROOT_DIR / "models" / "best_model.pth"
    CALIBRATION_PARAMS_PATH: Path = ROOT_DIR / "outputs" / "evaluation_aptos_ddr" / "calibration_parameters.json"

    # Persistence store paths
    CASES_STORE_PATH: Path = ROOT_DIR / "outputs" / "cases_store.json"
    PATIENTS_STORE_PATH: Path = ROOT_DIR / "outputs" / "patients_store.json"


settings = Settings()
