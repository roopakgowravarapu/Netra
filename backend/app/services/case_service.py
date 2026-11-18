"""Case Service orchestrating Telemedicine workflow, state transitions, and audit logging."""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status

from backend.app.core.logging import logger
from backend.app.repositories.case_repository import case_repository
from backend.app.schemas.cases import (
    CaseAuditEntrySchema,
    CaseHistoryItemSchema,
    ScreeningCaseSchema,
    SpecialistReviewRequest,
)
from backend.app.schemas.screening import ScreeningReportResponse
from backend.app.services.patient_service import update_visit_with_specialist_decision


def clear_cases() -> None:
    """Helper to reset case database for testing."""
    case_repository.clear()


def determine_case_status(report_dict: dict) -> str:
    """
    Determines workflow status based on clinical grading rules:
    - Ungradable image -> RECAPTURE_REQUIRED
    - Grade 0 (No DR) -> ROUTINE_SCREENING
    - Grade 1 (Mild DR) -> FOLLOW_UP_RECOMMENDED
    - Grade 2 (Moderate DR) -> REQUIRES_SPECIALIST_REVIEW
    - Grade 3 (Severe DR) -> REQUIRES_SPECIALIST_REVIEW
    - Grade 4 (Proliferative DR) -> URGENT_SPECIALIST_REVIEW
    """
    iq_status = str(report_dict.get("image_quality", {}).get("status", "")).lower()
    retinal_analysis = report_dict.get("retinal_analysis") or {}
    q_status = str(retinal_analysis.get("quality_status", "")).upper()

    if iq_status == "ungradable" or q_status == "UNGRADABLE":
        return "RECAPTURE_REQUIRED"

    dr_pred = report_dict.get("dr_prediction")
    grade_retinal = retinal_analysis.get("dr_grade")
    grade_deep = dr_pred.get("grade") if isinstance(dr_pred, dict) else getattr(dr_pred, "grade", None) if dr_pred else None

    if grade_deep is not None and grade_retinal is not None:
        grade = max(int(grade_retinal), int(grade_deep))
    elif grade_deep is not None:
        grade = int(grade_deep)
    elif grade_retinal is not None:
        grade = int(grade_retinal)
    else:
        grade = 0

    if grade == 0:
        return "ROUTINE_SCREENING"
    elif grade == 1:
        return "FOLLOW_UP_RECOMMENDED"
    elif grade == 2:
        return "REQUIRES_SPECIALIST_REVIEW"
    elif grade == 3:
        return "REQUIRES_SPECIALIST_REVIEW"
    elif grade == 4:
        return "URGENT_SPECIALIST_REVIEW"
    else:
        return "REQUIRES_SPECIALIST_REVIEW"


def create_screening_case(report_dict: dict) -> ScreeningCaseSchema:
    """Creates a new telemedicine screening case from an AI screening report."""
    case_id = f"case_{report_dict['sample_id']}"
    now_str = datetime.now(timezone.utc).isoformat()
    initial_status = determine_case_status(report_dict)

    report_obj = ScreeningReportResponse(**report_dict)
    initial_history_item = CaseHistoryItemSchema(
        attempt=1,
        timestamp=now_str,
        screening_report=report_obj,
        specialist_decision=None,
        override_grade=None,
        specialist_notes=None,
        specialist_id=None,
    )

    initial_audit = [
        CaseAuditEntrySchema(
            timestamp=now_str,
            actor="system",
            action="CASE_CREATED",
            details=f"Initial automated screening completed. Status: {initial_status}",
        )
    ]

    case = ScreeningCaseSchema(
        case_id=case_id,
        patient_id=report_dict.get("patient_id"),
        patient_name=report_dict.get("patient_name") or "Anonymous Patient",
        age=report_dict.get("age"),
        gender=report_dict.get("gender") or "Unknown",
        diabetes_type=report_dict.get("diabetes_type") or "Unknown",
        diabetes_duration_years=report_dict.get("diabetes_duration_years"),
        eye_examined=report_dict.get("eye_examined") or "OD",
        patient_consent=report_dict.get("patient_consent", True),
        created_at=now_str,
        status=initial_status,
        screening_report=report_obj,
        attempt=1,
        history=[initial_history_item],
        audit_trail=initial_audit,
    )
    case_repository.save(case)
    return case


def get_all_cases(specialist_queue_only: bool = True) -> List[ScreeningCaseSchema]:
    """Returns cases. When specialist_queue_only=True, filters to cases requiring specialist attention."""
    cases = case_repository.get_all()
    if specialist_queue_only:
        specialist_statuses = {
            "DOCTOR_REFERRAL",
            "REQUIRES_SPECIALIST_REVIEW",
            "URGENT_SPECIALIST_REVIEW",
            "CONFIRMED",
            "OVERRIDDEN",
            "SPECIALIST_REVIEWED",
        }
        return [
            c for c in cases
            if c.status in specialist_statuses or (c.status == "RECAPTURE_REQUIRED" and (c.attempt > 1 or c.specialist_decision == "REQUEST_RECAPTURE"))
        ]
    return cases


def get_case_by_id(case_id: str) -> ScreeningCaseSchema:
    case = case_repository.get_by_id(case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Screening case '{case_id}' not found.",
        )
    return case


def delete_case_by_id(case_id: str) -> bool:
    """Deletes a screening case from the repository."""
    deleted = case_repository.delete(case_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Screening case '{case_id}' not found.",
        )
    return True


def delete_all_cases() -> int:
    """Deletes all screening cases from the repository."""
    return case_repository.clear_all()


def refer_case_to_doctor(case_id: str, referral_notes: Optional[str] = None) -> ScreeningCaseSchema:
    """Marks a screening case as referred to specialist and records in audit trail."""
    case = get_case_by_id(case_id)
    now_str = datetime.now(timezone.utc).isoformat()

    dr_pred = case.screening_report.dr_prediction
    grade = dr_pred.grade if dr_pred else 0
    if grade == 4:
        case.status = "URGENT_SPECIALIST_REVIEW"
    else:
        case.status = "REQUIRES_SPECIALIST_REVIEW"

    if referral_notes:
        case.specialist_notes = referral_notes

    case.updated_at = now_str
    case.audit_trail.append(
        CaseAuditEntrySchema(
            timestamp=now_str,
            actor="screener",
            action="REFERRED_TO_SPECIALIST",
            details=referral_notes or f"Referred with DR Grade {grade}",
        )
    )

    case_repository.save(case)
    return case


def submit_specialist_review(case_id: str, review: SpecialistReviewRequest) -> ScreeningCaseSchema:
    case = get_case_by_id(case_id)

    # Double-decision check
    if case.status in ["CONFIRMED", "OVERRIDDEN", "SPECIALIST_REVIEWED"] or case.specialist_decision is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Case has already been decided.",
        )

    # Cases waiting for recapture or routine screening cannot be reviewed directly
    if case.status not in ["REQUIRES_SPECIALIST_REVIEW", "URGENT_SPECIALIST_REVIEW", "DOCTOR_REFERRAL"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Case in status '{case.status}' does not require specialist review.",
        )

    # Normalize decision
    raw_decision = review.decision.strip().upper()
    if raw_decision in ["CONFIRM", "CONFIRMED"]:
        norm_decision = "CONFIRMED"
        new_status = "CONFIRMED"
    elif raw_decision in ["OVERRIDE", "OVERRIDDEN"]:
        norm_decision = "OVERRIDDEN"
        new_status = "OVERRIDDEN"
    elif raw_decision in ["REQUEST_RECAPTURE", "RECAPTURE"]:
        norm_decision = "REQUEST_RECAPTURE"
        new_status = "RECAPTURE_REQUIRED"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid decision '{review.decision}'. Must be one of ['CONFIRMED', 'OVERRIDDEN', 'REQUEST_RECAPTURE']",
        )

    if norm_decision == "OVERRIDDEN":
        if review.override_grade is None or not (0 <= review.override_grade <= 4):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Override decision requires a valid override_grade between 0 and 4.",
            )

    now_str = datetime.now(timezone.utc).isoformat()
    case.status = new_status
    case.specialist_decision = norm_decision
    case.override_grade = review.override_grade if norm_decision == "OVERRIDDEN" else None
    case.specialist_notes = review.specialist_notes
    case.specialist_id = review.specialist_id
    case.updated_at = now_str

    if case.history:
        case.history[-1].specialist_decision = norm_decision
        case.history[-1].override_grade = case.override_grade
        case.history[-1].specialist_notes = case.specialist_notes
        case.history[-1].specialist_id = case.specialist_id

    case.audit_trail.append(
        CaseAuditEntrySchema(
            timestamp=now_str,
            actor=review.specialist_id,
            action=f"SPECIALIST_{norm_decision}",
            details=(
                f"Grade Override to {review.override_grade}. Notes: {review.specialist_notes}"
                if norm_decision == "OVERRIDDEN"
                else f"Decision: {norm_decision}. Notes: {review.specialist_notes}"
            ),
        )
    )

    try:
        update_visit_with_specialist_decision(
            case_id=case_id,
            decision=norm_decision,
            override_grade=case.override_grade,
            specialist_notes=case.specialist_notes,
        )
    except Exception as e:
        logger.warning(f"Could not sync visit with specialist decision: {e}")

    case_repository.save(case)
    return case


def recapture_case(case_id: str, report_dict: dict) -> ScreeningCaseSchema:
    """Updates an existing case in RECAPTURE_REQUIRED with a replacement analyzed scan."""
    case = get_case_by_id(case_id)

    if case.status != "RECAPTURE_REQUIRED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Case '{case_id}' is not in RECAPTURE_REQUIRED status (current status: {case.status}).",
        )

    now_str = datetime.now(timezone.utc).isoformat()
    case.attempt += 1
    if not report_dict.get("patient_name") or report_dict.get("patient_name") == "Anonymous Patient":
        report_dict["patient_name"] = case.patient_name
    new_report = ScreeningReportResponse(**report_dict)
    case.screening_report = new_report
    case.patient_name = new_report.patient_name or case.patient_name

    case.specialist_decision = None
    case.override_grade = None
    case.specialist_notes = None
    case.specialist_id = None
    case.updated_at = now_str

    raw_status = determine_case_status(report_dict)
    if raw_status == "RECAPTURE_REQUIRED":
        case.status = "RECAPTURE_REQUIRED"
    elif raw_status == "URGENT_SPECIALIST_REVIEW":
        case.status = "URGENT_SPECIALIST_REVIEW"
    else:
        # Recaptured scans for existing specialist review cases return to the specialist queue
        case.status = "REQUIRES_SPECIALIST_REVIEW"

    case.history.append(
        CaseHistoryItemSchema(
            attempt=case.attempt,
            timestamp=now_str,
            screening_report=new_report,
            specialist_decision=None,
            override_grade=None,
            specialist_notes=None,
            specialist_id=None,
        )
    )

    case.audit_trail.append(
        CaseAuditEntrySchema(
            timestamp=now_str,
            actor="system",
            action=f"IMAGE_RECAPTURED_ATTEMPT_{case.attempt}",
            details=f"Recapture analyzed. New status: {case.status}",
        )
    )

    case_repository.save(case)
    return case
