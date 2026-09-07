"""Pydantic schemas for Netra API requests and responses."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ImageQualitySchema(BaseModel):
    score: float = Field(..., description="Normalized image quality score [0.0 - 1.0]")
    status: str = Field(..., description="'gradable' or 'ungradable'")
    issues: List[str] = Field(default_factory=list, description="List of detected quality issues")
    metrics: Dict[str, float] = Field(default_factory=dict, description="Raw feature metrics")


class UncertaintySchema(BaseModel):
    entropy: float
    margin: float


class DRPredictionSchema(BaseModel):
    grade: int = Field(..., description="DR Severity Grade (0: No DR, 1: Mild, 2: Moderate, 3: Severe, 4: Proliferative)")
    label: str = Field(..., description="DR Grade Label")
    confidence: float = Field(..., description="Temperature-Calibrated Confidence Probability [0.0 - 1.0]")
    probabilities: Dict[str, float] = Field(..., description="Class probabilities across all 5 DR grades")
    uncertainty: UncertaintySchema


class ExplanationSchema(BaseModel):
    gradcam_path: Optional[str] = Field(None, description="Path or URL to Grad-CAM heatmap overlay image")
    original_image_path: Optional[str] = Field(None, description="Path or URL to saved original fundus image")
    target_class: int = Field(..., description="Target DR class for Grad-CAM explanation")


class ScreeningReportResponse(BaseModel):
    sample_id: str
    case_id: Optional[str] = Field(None, description="Registered Telemedicine Case ID")
    original_image_path: Optional[str] = Field(None, description="Path or URL to saved original fundus image")
    image_quality: ImageQualitySchema
    dr_prediction: Optional[DRPredictionSchema] = None
    explanation: Optional[ExplanationSchema] = None
    recommendation: str
    disclaimer: str
