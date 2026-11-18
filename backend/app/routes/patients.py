"""FastAPI routes for Patient Management and Retinal Progression Tracking."""

from typing import List, Optional
from fastapi import APIRouter, Query, status

from backend.app.schemas.patients import (
    PatientCreateRequest,
    PatientProgressionComparison,
    PatientSchema,
    ScreeningVisitSchema,
)
from backend.app.services.patient_service import (
    create_or_update_patient,
    get_all_patients,
    get_patient_by_id,
    get_patient_progression,
    delete_patient,
    delete_patient_history,
    delete_all_patients,
)

router = APIRouter(prefix="/api/patients", tags=["Patient Management"])


@router.get("", response_model=List[PatientSchema])
def list_patients(query: Optional[str] = Query(None, description="Search by Patient ID or Name")):
    """List all registered patients with their demographics and visit count."""
    return get_all_patients(query=query)


@router.post("", response_model=PatientSchema, status_code=status.HTTP_201_CREATED)
def register_or_update_patient(req: PatientCreateRequest):
    """Register a new patient or update existing patient demographics."""
    return create_or_update_patient(req)


@router.get("/{patient_id}", response_model=PatientSchema)
def get_patient(patient_id: str):
    """Retrieve full patient demographic record and screening visits."""
    return get_patient_by_id(patient_id)


@router.get("/{patient_id}/history", response_model=List[ScreeningVisitSchema])
def get_patient_visit_history(patient_id: str):
    """Retrieve longitudinal screening visit history for a patient."""
    patient = get_patient_by_id(patient_id)
    return sorted(patient.visits, key=lambda v: v.date, reverse=True)


@router.get("/{patient_id}/progression", response_model=PatientProgressionComparison)
def get_patient_progression_comparison(
    patient_id: str,
    eye: Optional[str] = Query(None, description="Filter comparison by eye: 'OD' or 'OS'"),
):
    """Retrieve side-by-side longitudinal progression comparison between baseline and current visit."""
    return get_patient_progression(patient_id, eye=eye)


@router.delete("")
def delete_all_patients_endpoint():
    """Deletes all registered patient records."""
    count = delete_all_patients()
    return {"message": f"All {count} patient records deleted successfully.", "count": count}


@router.delete("/{patient_id}")
def delete_single_patient(patient_id: str):
    """Deletes a specific patient record."""
    delete_patient(patient_id)
    return {"message": f"Patient '{patient_id}' deleted successfully.", "patient_id": patient_id}


@router.delete("/{patient_id}/history")
def clear_patient_history_endpoint(patient_id: str):
    """Clears all screening visit history for a specific patient while retaining patient demographics."""
    patient = delete_patient_history(patient_id)
    return {"message": f"Visit history for patient '{patient_id}' cleared successfully.", "patient": patient}
