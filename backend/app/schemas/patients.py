"""Pydantic schemas for Patient Management, Longitudinal Visits & Screening History."""

from typing import List, Optional
from pydantic import BaseModel, Field


class ScreeningVisitSchema(BaseModel):
    visit_id: str
    date: str
    sample_id: str
    case_id: Optional[str] = None
    eye_examined: str = Field("OD", description="'OD' (Right Eye) or 'OS' (Left Eye)")
    image_path: Optional[str] = None
    iqa_status: str = "gradable"
    dr_grade: Optional[int] = None
    dr_stage: Optional[str] = None
    confidence: Optional[float] = None
    uncertain_prediction: bool = False
    macula_risk_level: Optional[str] = None
    specialist_status: Optional[str] = None
    specialist_grade: Optional[int] = None
    specialist_notes: Optional[str] = None


class PatientSchema(BaseModel):
    patient_id: str = Field(..., description="Unique Patient Identification Code (e.g. PAT-1001)")
    name: str = Field(..., description="Full Name of the patient")
    age: Optional[int] = Field(None, description="Age in years")
    gender: Optional[str] = Field("Unknown", description="Gender: Male, Female, Other, Unknown")
    diabetes_type: Optional[str] = Field("Unknown", description="Type 1, Type 2, Gestational, None, Unknown")
    diabetes_duration_years: Optional[float] = Field(None, description="Known duration of diabetes in years")
    created_at: str
    updated_at: str
    visits: List[ScreeningVisitSchema] = Field(default_factory=list)


class PatientCreateRequest(BaseModel):
    patient_id: Optional[str] = None
    name: str
    age: Optional[int] = None
    gender: Optional[str] = "Unknown"
    diabetes_type: Optional[str] = "Unknown"
    diabetes_duration_years: Optional[float] = None


class PatientProgressionComparison(BaseModel):
    patient_id: str
    patient_name: str
    eye_examined: str
    baseline_visit: Optional[ScreeningVisitSchema] = None
    current_visit: Optional[ScreeningVisitSchema] = None
    grade_change: Optional[int] = None  # e.g. +1 (worsened), 0 (stable), -1 (improved)
    progression_summary: str
    disclaimer: str = (
        "Longitudinal comparison provides observational alignment of findings across clinical visits. "
        "It does not constitute automated lesion tracking or autonomous progression prognosis. "
        "Formal comparison requires specialist ophthalmological assessment."
    )
