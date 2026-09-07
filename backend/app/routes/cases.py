"""FastAPI routes for Telemedicine screening cases."""

from typing import List
from fastapi import APIRouter, HTTPException, File, UploadFile
from backend.app.schemas.cases import ScreeningCaseSchema, SpecialistReviewRequest
from backend.app.services.case_service import create_screening_case, get_all_cases, get_case_by_id, submit_specialist_review
from backend.app.services.screening_service import process_image_upload

router = APIRouter(prefix="/api/cases", tags=["Telemedicine"])


@router.post("", response_model=ScreeningCaseSchema)
async def create_case_from_upload(file: UploadFile = File(...)):
    """Uploads an image, runs AI pipeline, and initializes a new Telemedicine screening case."""
    report_dict = await process_image_upload(file)
    case = create_screening_case(report_dict)
    return case


@router.get("", response_model=List[ScreeningCaseSchema])
def list_cases():
    """Lists all active telemedicine screening cases."""
    return get_all_cases()


@router.get("/{case_id}", response_model=ScreeningCaseSchema)
def get_case(case_id: str):
    """Retrieves a specific telemedicine screening case by ID."""
    return get_case_by_id(case_id)


@router.post("/{case_id}/review", response_model=ScreeningCaseSchema)
def review_case(case_id: str, review: SpecialistReviewRequest):
    """Submits remote specialist review notes and decision for a screening case."""
    return submit_specialist_review(case_id, review)
