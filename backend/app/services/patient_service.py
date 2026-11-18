"""Patient Service managing patient registration, visits, and longitudinal progression."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status

from backend.app.core.logging import logger
from backend.app.repositories.patient_repository import patient_repository
from backend.app.schemas.patients import (
    PatientCreateRequest,
    PatientProgressionComparison,
    PatientSchema,
    ScreeningVisitSchema,
)


def get_all_patients(query: Optional[str] = None) -> List[PatientSchema]:
    return patient_repository.get_all(query=query)


def get_patient_by_id(patient_id: str) -> PatientSchema:
    patient = patient_repository.get_by_id(patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient '{patient_id}' not found.",
        )
    return patient


def create_or_update_patient(req: PatientCreateRequest) -> PatientSchema:
    now_str = datetime.now(timezone.utc).isoformat()
    pid = req.patient_id.strip() if req.patient_id and req.patient_id.strip() else f"PAT-{uuid.uuid4().hex[:6].upper()}"

    patient = patient_repository.get_by_id(pid)
    if patient:
        patient.name = req.name or patient.name
        if req.age is not None:
            patient.age = req.age
        if req.gender:
            patient.gender = req.gender
        if req.diabetes_type:
            patient.diabetes_type = req.diabetes_type
        if req.diabetes_duration_years is not None:
            patient.diabetes_duration_years = req.diabetes_duration_years
        patient.updated_at = now_str
    else:
        patient = PatientSchema(
            patient_id=pid,
            name=req.name,
            age=req.age,
            gender=req.gender or "Unknown",
            diabetes_type=req.diabetes_type or "Unknown",
            diabetes_duration_years=req.diabetes_duration_years,
            created_at=now_str,
            updated_at=now_str,
            visits=[],
        )
    patient_repository.save(patient)
    return patient


def record_screening_visit(
    patient_id: str,
    patient_name: str,
    age: Optional[int],
    gender: Optional[str],
    diabetes_type: Optional[str],
    diabetes_duration_years: Optional[float],
    eye_examined: str,
    report_dict: dict,
    case_id: Optional[str] = None,
) -> ScreeningVisitSchema:
    now_str = datetime.now(timezone.utc).isoformat()
    pid = (patient_id or "").strip()
    if not pid:
        pid = f"PAT-{uuid.uuid4().hex[:6].upper()}"

    patient = patient_repository.get_by_id(pid)
    if not patient:
        patient = PatientSchema(
            patient_id=pid,
            name=patient_name or "Anonymous Patient",
            age=age,
            gender=gender or "Unknown",
            diabetes_type=diabetes_type or "Unknown",
            diabetes_duration_years=diabetes_duration_years,
            created_at=now_str,
            updated_at=now_str,
            visits=[],
        )
    else:
        if patient_name and patient_name != "Anonymous Patient":
            patient.name = patient_name
        if age is not None:
            patient.age = age
        if gender:
            patient.gender = gender
        if diabetes_type:
            patient.diabetes_type = diabetes_type
        if diabetes_duration_years is not None:
            patient.diabetes_duration_years = diabetes_duration_years
        patient.updated_at = now_str

    dr_pred = report_dict.get("dr_prediction") or {}
    iq = report_dict.get("image_quality") or {}

    grade = dr_pred.get("grade")
    stage = dr_pred.get("label") or dr_pred.get("stage")
    confidence = dr_pred.get("confidence")
    uncertain_pred = dr_pred.get("uncertain_prediction", False)

    visit = ScreeningVisitSchema(
        visit_id=f"vis_{uuid.uuid4().hex[:8]}",
        date=now_str,
        sample_id=str(report_dict.get("sample_id", "")),
        case_id=case_id,
        eye_examined=eye_examined.upper() if eye_examined else "OD",
        image_path=report_dict.get("image_path") or f"/api/cases/image/{report_dict.get('sample_id')}",
        iqa_status=str(iq.get("status", "gradable")).lower(),
        dr_grade=int(grade) if grade is not None else None,
        dr_stage=stage,
        confidence=float(confidence) if confidence is not None else None,
        uncertain_prediction=bool(uncertain_pred),
        macula_risk_level=dr_pred.get("macula_risk_level"),
        specialist_status="PENDING_REVIEW" if (grade and int(grade) >= 2) else "SCREENED",
    )

    patient.visits.append(visit)
    patient.updated_at = now_str
    patient_repository.save(patient)
    return visit


def update_visit_with_specialist_decision(
    case_id: str,
    decision: str,
    override_grade: Optional[int],
    specialist_notes: Optional[str],
) -> None:
    patients = patient_repository.get_all()
    for patient in patients:
        for visit in patient.visits:
            if visit.case_id == case_id:
                visit.specialist_status = decision
                if override_grade is not None:
                    visit.specialist_grade = override_grade
                if specialist_notes:
                    visit.specialist_notes = specialist_notes
                patient.updated_at = datetime.now(timezone.utc).isoformat()
                patient_repository.save(patient)
                return


def get_patient_progression(patient_id: str, eye: Optional[str] = None) -> PatientProgressionComparison:
    patient = get_patient_by_id(patient_id)
    visits = patient.visits
    if eye:
        eye_norm = eye.upper()
        visits = [v for v in visits if v.eye_examined == eye_norm]

    if not visits:
        return PatientProgressionComparison(
            patient_id=patient.patient_id,
            patient_name=patient.name,
            eye_examined=eye or "OD/OS",
            baseline_visit=None,
            current_visit=None,
            grade_change=None,
            progression_summary="No completed screening visits recorded for comparison.",
        )

    visits_sorted = sorted(visits, key=lambda v: v.date)
    baseline = visits_sorted[0]
    current = visits_sorted[-1]

    grade_change = None
    if baseline.dr_grade is not None and current.dr_grade is not None and len(visits_sorted) > 1:
        grade_change = current.dr_grade - baseline.dr_grade
        if grade_change > 0:
            summary = f"Observational increase of +{grade_change} grade(s) from Baseline ({baseline.dr_stage}) to Current ({current.dr_stage}). Specialist review recommended to evaluate progression."
        elif grade_change < 0:
            summary = f"Observational decrease of {grade_change} grade(s) from Baseline ({baseline.dr_stage}) to Current ({current.dr_stage}). Verified by clinical team."
        else:
            summary = f"Stable DR grade ({current.dr_stage}) observed between Baseline ({baseline.date[:10]}) and Current examination ({current.date[:10]})."
    else:
        summary = f"Single recorded visit on {current.date[:10]} ({current.dr_stage or 'Screened'}). Baseline comparison will become available on subsequent follow-up screening."

    return PatientProgressionComparison(
        patient_id=patient.patient_id,
        patient_name=patient.name,
        eye_examined=current.eye_examined,
        baseline_visit=baseline if len(visits_sorted) > 1 else None,
        current_visit=current,
        grade_change=grade_change,
        progression_summary=summary,
    )


def delete_patient(patient_id: str) -> bool:
    """Deletes a patient record completely."""
    success = patient_repository.delete(patient_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient '{patient_id}' not found.",
        )
    return True


def delete_patient_history(patient_id: str) -> PatientSchema:
    """Clears all screening visit history for a specific patient."""
    patient = get_patient_by_id(patient_id)
    patient.visits = []
    patient.updated_at = datetime.now(timezone.utc).isoformat()
    patient_repository.save(patient)
    return patient


def delete_all_patients() -> int:
    """Clears all registered patients from repository."""
    all_patients = patient_repository.get_all()
    count = len(all_patients)
    patient_repository.clear()
    return count
