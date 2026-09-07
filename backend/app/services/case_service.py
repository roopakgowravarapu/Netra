"""In-memory Case Service for Telemedicine Workflow management."""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from fastapi import HTTPException, status

from backend.app.schemas.cases import ScreeningCaseSchema, SpecialistReviewRequest
from backend.app.schemas.screening import ScreeningReportResponse

# In-memory database store for cases
_cases_db: Dict[str, ScreeningCaseSchema] = {}


def create_screening_case(report_dict: dict) -> ScreeningCaseSchema:
    """Creates a new telemedicine screening case from an AI screening report."""
    case_id = f"case_{report_dict['sample_id']}"
    now_str = datetime.now(timezone.utc).isoformat()

    is_gradable = report_dict["image_quality"]["status"] == "gradable"
    if is_gradable:
        initial_status = "REQUIRES_SPECIALIST_REVIEW"
    else:
        initial_status = "RECAPTURE_REQUIRED"

    case = ScreeningCaseSchema(
        case_id=case_id,
        created_at=now_str,
        status=initial_status,
        screening_report=ScreeningReportResponse(**report_dict),
    )
    _cases_db[case_id] = case
    return case


def get_all_cases() -> List[ScreeningCaseSchema]:
    return list(_cases_db.values())


def get_case_by_id(case_id: str) -> ScreeningCaseSchema:
    if case_id not in _cases_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Screening case '{case_id}' not found.",
        )
    return _cases_db[case_id]


def submit_specialist_review(case_id: str, review: SpecialistReviewRequest) -> ScreeningCaseSchema:
    case = get_case_by_id(case_id)

    # Validate decision string
    valid_decisions = ["confirm", "override", "request_recapture"]
    if review.decision not in valid_decisions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid decision '{review.decision}'. Must be one of {valid_decisions}",
        )

    if review.decision == "override" and (review.override_grade is None or not (0 <= review.override_grade <= 4)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Override decision requires a valid override_grade between 0 and 4.",
        )

    case.specialist_decision = review.decision
    case.override_grade = review.override_grade
    case.specialist_notes = review.specialist_notes
    case.specialist_id = review.specialist_id
    case.updated_at = datetime.now(timezone.utc).isoformat()

    if review.decision == "request_recapture":
        case.status = "RECAPTURE_REQUIRED"
    else:
        case.status = "SPECIALIST_REVIEWED"

    _cases_db[case_id] = case
    return case
