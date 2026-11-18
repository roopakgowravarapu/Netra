"""Pydantic schemas for Telemedicine Screening Cases & Specialist Review."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.schemas.screening import ScreeningReportResponse


class SpecialistReviewRequest(BaseModel):
    decision: str = Field(..., description="'CONFIRMED', 'OVERRIDDEN', or 'REQUEST_RECAPTURE' (case-insensitive)")
    override_grade: Optional[int] = Field(None, description="New DR Grade 0-4 if decision is 'OVERRIDDEN'")
    specialist_notes: str = Field("", description="Clinical review notes by specialist")
    specialist_id: str = Field("dr_ophthalmologist_01", description="Specialist ID")


class ClinicalApprovalRequest(BaseModel):
    decision: str = Field(..., description="'APPROVE' or 'REJECT'")
    clinician_id: str = Field("consulting_clinician", description="Clinician identifier")
    notes: Optional[str] = Field("", description="Clinical decision rationale")


class DoctorReferralRequest(BaseModel):
    clinician_id: str = Field("consulting_clinician", description="Referring clinician identifier")
    referral_notes: Optional[str] = Field("", description="Notes for consulting ophthalmologist")


class CaseAuditEntrySchema(BaseModel):
    timestamp: str
    actor: str = Field("system", description="'system', 'screener', or specialist id")
    action: str = Field(..., description="Action performed, e.g. CREATED, REFERRED, REVIEW_CONFIRMED, REVIEW_OVERRIDDEN, RECAPTURE_REQUESTED")
    details: Optional[str] = None


class CaseHistoryItemSchema(BaseModel):
    attempt: int
    timestamp: str
    screening_report: ScreeningReportResponse
    specialist_decision: Optional[str] = None
    override_grade: Optional[int] = None
    specialist_notes: Optional[str] = None
    specialist_id: Optional[str] = None


class ScreeningCaseSchema(BaseModel):
    case_id: str
    patient_id: Optional[str] = Field(None, description="Unique Patient Identification Code")
    patient_name: Optional[str] = Field("Anonymous Patient", description="Patient Full Name")
    age: Optional[int] = Field(None, description="Patient Age")
    gender: Optional[str] = Field("Unknown", description="Gender")
    diabetes_type: Optional[str] = Field("Unknown", description="Diabetes Type")
    diabetes_duration_years: Optional[float] = Field(None, description="Duration of Diabetes")
    eye_examined: Optional[str] = Field("OD", description="Eye examined: OD (Right) or OS (Left)")
    patient_consent: Optional[bool] = Field(True, description="Informed patient consent verified")
    created_at: str
    status: str = Field(
        ...,
        description=(
            "Workflow status ('ROUTINE_SCREENING', 'FOLLOW_UP_RECOMMENDED', "
            "'REQUIRES_SPECIALIST_REVIEW', 'URGENT_SPECIALIST_REVIEW', "
            "'CONFIRMED', 'OVERRIDDEN', 'RECAPTURE_REQUIRED', 'SPECIALIST_REVIEWED')"
        ),
    )
    screening_report: ScreeningReportResponse
    specialist_decision: Optional[str] = None
    override_grade: Optional[int] = None
    specialist_notes: Optional[str] = None
    specialist_id: Optional[str] = None
    clinical_approval: Optional[str] = Field(None, description="'APPROVED' or 'REJECTED'")
    clinical_approved_at: Optional[str] = None
    clinical_approved_by: Optional[str] = None
    clinical_approval_notes: Optional[str] = None
    referred_to_doctor: bool = Field(False, description="Whether case has been referred to consulting doctor")
    referred_at: Optional[str] = None
    referred_by: Optional[str] = None
    referral_notes: Optional[str] = None
    updated_at: Optional[str] = None
    attempt: int = 1
    history: List[CaseHistoryItemSchema] = Field(default_factory=list)
    audit_trail: List[CaseAuditEntrySchema] = Field(default_factory=list)
