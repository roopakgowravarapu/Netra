"""FastAPI routes for Telemedicine screening cases."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, File, Form, UploadFile
from backend.app.schemas.cases import (
    ScreeningCaseSchema,
    SpecialistReviewRequest,
    ClinicalApprovalRequest,
    DoctorReferralRequest,
)
from backend.app.services.case_service import (
    create_screening_case,
    get_all_cases,
    get_case_by_id,
    delete_case_by_id,
    delete_all_cases,
    submit_specialist_review,
    recapture_case,
    record_clinical_approval,
    refer_case_to_doctor,
    get_doctor_cases,
)
from backend.app.services.screening_service import process_image_upload

router = APIRouter(prefix="/api/cases", tags=["Telemedicine"])


@router.get("/doctor-queue", response_model=List[ScreeningCaseSchema])
def list_doctor_cases():
    """Lists eligible approved cases referred to the Doctor Portal."""
    return get_doctor_cases()


@router.post("", response_model=ScreeningCaseSchema)
async def create_case_from_upload(
    file: UploadFile = File(...),
    patient_name: Optional[str] = Form(None),
):
    """Uploads an image, runs AI pipeline, and initializes a new Telemedicine screening case."""
    report_dict = await process_image_upload(file, patient_name=patient_name)
    case = create_screening_case(report_dict)
    # If case was explicitly uploaded to Telemedicine cases queue and is gradable, ensure specialist review status
    if case.status in ["ROUTINE_SCREENING", "FOLLOW_UP_RECOMMENDED"]:
        case.status = "REQUIRES_SPECIALIST_REVIEW"
    return case


@router.get("", response_model=List[ScreeningCaseSchema])
def list_cases(all: bool = False):
    """Lists telemedicine screening cases. Defaults to specialist review queue."""
    return get_all_cases(specialist_queue_only=not all)


@router.get("/{case_id}", response_model=ScreeningCaseSchema)
def get_case(case_id: str):
    """Retrieves a specific telemedicine screening case by ID."""
    return get_case_by_id(case_id)


@router.post("/{case_id}/review", response_model=ScreeningCaseSchema)
def review_case(case_id: str, review: SpecialistReviewRequest):
    """Submits remote specialist review notes and decision for a screening case."""
    return submit_specialist_review(case_id, review)


@router.post("/{case_id}/recapture", response_model=ScreeningCaseSchema)
async def recapture_case_image(case_id: str, file: UploadFile = File(...)):
    """Uploads a replacement fundus scan for a case in RECAPTURE_REQUIRED and triggers re-analysis."""
    report_dict = await process_image_upload(file)
    return recapture_case(case_id, report_dict)


@router.post("/{case_id}/clinical-approval", response_model=ScreeningCaseSchema)
def approve_case_clinically(case_id: str, request: ClinicalApprovalRequest):
    """Records clinician approval or rejection for referral with one-way locked decision."""
    return record_clinical_approval(case_id, request)


@router.post("/{case_id}/refer-to-doctor", response_model=ScreeningCaseSchema)
def send_case_to_doctor(case_id: str, request: DoctorReferralRequest):
    """Submits an approved case to the Doctor Portal queue."""
    return refer_case_to_doctor(case_id, request)


@router.delete("")
def delete_all_screening_cases():
    """Deletes all screening cases from the queue."""
    count = delete_all_cases()
    return {"message": f"All {count} cases deleted successfully.", "count": count}


@router.delete("/{case_id}")
def delete_case(case_id: str):
    """Deletes a screening case from the queue."""
    delete_case_by_id(case_id)
    return {"message": f"Case '{case_id}' deleted successfully.", "case_id": case_id}


