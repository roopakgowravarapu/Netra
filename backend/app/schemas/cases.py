"""Pydantic schemas for Telemedicine Screening Cases & Specialist Review."""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.schemas.screening import ScreeningReportResponse


class SpecialistReviewRequest(BaseModel):
    decision: str = Field(..., description="'confirm', 'override', or 'request_recapture'")
    override_grade: Optional[int] = Field(None, description="New DR Grade 0-4 if decision is 'override'")
    specialist_notes: str = Field("", description="Clinical review notes by specialist")
    specialist_id: str = Field("dr_ophthalmologist_01", description="Specialist ID")


class ScreeningCaseSchema(BaseModel):
    case_id: str
    created_at: str
    status: str = Field(..., description="Workflow status ('RESULT_READY', 'REQUIRES_SPECIALIST_REVIEW', 'SPECIALIST_REVIEWED', 'UNGRADABLE', 'RECAPTURE_REQUIRED')")
    screening_report: ScreeningReportResponse
    specialist_decision: Optional[str] = None
    override_grade: Optional[int] = None
    specialist_notes: Optional[str] = None
    specialist_id: Optional[str] = None
    updated_at: Optional[str] = None
