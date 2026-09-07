"""Screening Service wrapping AI Pipeline execution for FastAPI backend."""

import uuid
from pathlib import Path
from typing import Any, Dict
import cv2
import numpy as np
from fastapi import HTTPException, UploadFile, status

from backend.app.config.settings import settings
from src.reporting.screening_report import ScreeningPipeline

# Singleton pipeline instance
_pipeline_instance: ScreeningPipeline = None


def get_pipeline() -> ScreeningPipeline:
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = ScreeningPipeline()
    return _pipeline_instance


async def process_image_upload(file: UploadFile) -> Dict[str, Any]:
    """Validates file upload, decodes image, and runs Netra screening pipeline."""
    # 1. Content type check
    if file.content_type not in settings.ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{file.content_type}'. Allowed types: {settings.ALLOWED_CONTENT_TYPES}",
        )

    # 2. File size check
    contents = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB}MB.",
        )

    # 3. Image decoding check
    nparr = np.frombuffer(contents, np.uint8)
    img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img_bgr is None or img_bgr.size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to decode image file. File may be corrupted or invalid.",
        )

    # 4. Pipeline execution
    sample_id = f"img_{uuid.uuid4().hex[:8]}"
    save_dir = settings.STATIC_DIR / "explainability"
    pipeline = get_pipeline()

    try:
        report = pipeline.process_image(img_bgr, save_explanation_dir=save_dir, sample_id=sample_id)
        return report
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing screening pipeline: {str(e)}",
        )
