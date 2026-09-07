"""Prediction & screening endpoint route."""

from fastapi import APIRouter, File, UploadFile
from backend.app.schemas.screening import ScreeningReportResponse
from backend.app.services.case_service import create_screening_case
from backend.app.services.screening_service import process_image_upload

router = APIRouter(tags=["Screening"])


@router.post("/predict", response_model=ScreeningReportResponse)
async def predict_dr(file: UploadFile = File(...)):
    """
    Accepts a fundus image upload, performs Image Quality Assessment (IQA),
    and if gradable, generates DR prediction, calibrated confidence, & Grad-CAM explanation.
    Automatically enqueues the screening case into the Telemedicine consultation network.
    """
    report = await process_image_upload(file)
    case = create_screening_case(report)
    report["case_id"] = case.case_id
    return report
