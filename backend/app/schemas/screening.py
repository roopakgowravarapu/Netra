"""Pydantic schemas for Netra API requests and responses."""

from typing import Any, Dict, List, Optional
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
    raw_confidence: Optional[float] = Field(None, description="Uncalibrated Softmax Confidence Probability [0.0 - 1.0]")
    temperature: Optional[float] = Field(None, description="Temperature scaling factor T")
    probabilities: Dict[str, float] = Field(..., description="Class probabilities across all 5 DR grades")
    uncertainty: UncertaintySchema
    uncertain_prediction: bool = Field(False, description="Whether prediction exhibits high entropy/margin uncertainty requiring specialist review")
    uncertainty_warning: Optional[str] = Field(None, description="Clinical guidance warning if model uncertainty is elevated")


class ExplanationSchema(BaseModel):
    gradcam_path: Optional[str] = Field(None, description="Path or URL to Grad-CAM heatmap overlay image")
    original_image_path: Optional[str] = Field(None, description="Path or URL to saved original fundus image")
    heatmap_image_path: Optional[str] = Field(None, description="Path or URL to pure heatmap image")
    target_class: int = Field(..., description="Target DR class for Grad-CAM explanation")
    highlighted_region: Optional[str] = Field(None, description="Approximate region of peak activation")
    xai_explanation: Optional[Dict[str, Any]] = Field(None, description="Human-readable explainability narrative")


class RetinalStructuresSchema(BaseModel):
    optic_disc: Optional[Dict[str, Any]] = None
    fovea: Optional[Dict[str, Any]] = None
    vessel_mask: Optional[str] = None
    vessel_density: float = 0.0


class LesionEvidenceSchema(BaseModel):
    microaneurysms: Optional[Dict[str, Any]] = None
    exudates: Optional[Dict[str, Any]] = None
    hemorrhages: Optional[Dict[str, Any]] = None
    neovascularization: Optional[Dict[str, Any]] = None
    lesion_overlay: Optional[str] = None


class SpatialZoneSchema(BaseModel):
    zone_id: str = Field(..., description="Unique zone identifier (macula, superior_temporal, etc.)")
    zone_name: str = Field(..., description="Clinical anatomical zone name")
    short_code: str = Field(..., description="Short acronym (MAC, ST, IT, SN, IN, OD)")
    status: str = Field(..., description="CLEAR, EARLY_SIGNS, ACTIVE_LESIONS, MACULAR_THREAT, CRITICAL_NEOVASCULARIZATION")
    status_label: str = Field(..., description="Human-readable zone status label")
    lesion_summary: str = Field(..., description="Summary of lesions present in this place")
    microaneurysms_count: int = Field(0, description="Count of microaneurysms in this zone")
    exudates_count: int = Field(0, description="Count of hard exudates in this zone")
    exudates_area_px: int = Field(0, description="Area of exudates in pixels")
    hemorrhages_count: int = Field(0, description="Count of hemorrhages in this zone")
    neovascularization: bool = Field(False, description="Whether neovascularization is in this zone")
    attention_mean: float = Field(0.0, description="Mean Grad-CAM model saliency weight in this zone [0.0 - 1.0]")
    attention_peak: float = Field(0.0, description="Peak Grad-CAM model saliency weight in this zone [0.0 - 1.0]")
    anatomical_role: str = Field("", description="Clinical role of this anatomical region")
    clinical_explanation: str = Field(..., description="Detailed clinical narrative explaining this place")


class SpatialAnalysisSchema(BaseModel):
    spatial_map_image: Optional[str] = Field(None, description="Path/URL to the annotated quadrant spatial map")
    macula_threat_level: str = Field("LOW_RISK", description="LOW_RISK, BORDERLINE, or HIGH_THREAT")
    quadrants_affected_count: int = Field(0, description="Number of the 4 quadrants with microaneurysms/hemorrhages")
    affected_quadrants: List[str] = Field(default_factory=list, description="Names of affected quadrants")
    primary_attention_hotspot: str = Field("", description="Zone with highest deep learning model attention")
    zones: List[SpatialZoneSchema] = Field(default_factory=list, description="Detailed analysis for every retinal place")


class RetinalAnalysisSchema(BaseModel):
    quality_status: str = Field(..., description="'GOOD', 'BORDERLINE', or 'UNGRADABLE'")
    quality_score: float = Field(..., description="Calculated retinal image quality score [0.0 - 1.0]")
    quality_feedback: List[str] = Field(default_factory=list)
    recapture_instructions: Optional[str] = None
    enhancement_applied: bool = False
    enhanced_image: Optional[str] = None
    retinal_structures: Optional[RetinalStructuresSchema] = None
    lesion_evidence: Optional[LesionEvidenceSchema] = None
    spatial_analysis: Optional[SpatialAnalysisSchema] = Field(None, description="Detailed anatomical retinal place & quadrant explainability")
    dr_grade: Optional[int] = None
    severity: str = "No DR"
    referable_dr: bool = False
    raw_confidence: float = 0.0
    calibrated_confidence: float = 0.0
    calibration_status: str = ""
    gradcam_image: Optional[str] = None
    gradcam_description: str = "Regions receiving high attention from the DR classification model."
    heatmap_image: Optional[str] = None
    xai_explanation: Optional[Dict[str, Any]] = None
    lesion_evidence_image: Optional[str] = None
    lesion_evidence_description: str = "Regions identified by the retinal lesion analysis module."
    annotated_report: Optional[str] = None
    referral_recommendation: str = ""
    macula_risk_description: str = Field(
        "Spatial proximity assessment of lesions to the 2-disc-diameter macular ring. "
        "Autonomous DME diagnosis requires OCT confirmation.",
        description="Clinical disclaimer for macular risk assessment"
    )


class ScreeningReportResponse(BaseModel):
    sample_id: str
    case_id: Optional[str] = Field(None, description="Registered Telemedicine Case ID")
    patient_id: Optional[str] = Field("PAT-2026-0001", description="Unique Patient Identifier")
    patient_name: Optional[str] = Field("John Doe", description="Patient Full Name")
    age: Optional[int] = Field(None, ge=0, le=130, description="Patient Age")
    gender: Optional[str] = Field(None, description="Patient Gender")
    diabetes_type: Optional[str] = Field("Type 2", description="Diabetes Type (Type 1, Type 2, Gestational)")
    diabetes_duration_years: Optional[float] = Field(None, ge=0, description="Duration of Diabetes in Years")
    eye_examined: Optional[str] = Field("OD", description="Eye Examined: OD (Right Eye) or OS (Left Eye)")
    patient_consent: bool = Field(True, description="Informed patient consent obtained")
    screening_date: Optional[str] = Field(None, description="Screening Date (DD/MM/YYYY)")
    screening_time: Optional[str] = Field(None, description="Screening Time (hh:mm AM/PM in Asia/Kolkata)")
    created_at: Optional[str] = Field(None, description="ISO Timestamp in Asia/Kolkata")
    original_image_path: Optional[str] = Field(None, description="Path or URL to saved original fundus image")
    image_quality: ImageQualitySchema
    dr_prediction: Optional[DRPredictionSchema] = None
    explanation: Optional[ExplanationSchema] = None
    recommendation: str
    disclaimer: str
    retinal_analysis: Optional[RetinalAnalysisSchema] = Field(None, description="Retinal Computer Vision screening results")


class QualityAssessmentV1(BaseModel):
    status: str = Field(..., description="PASS | BORDERLINE_ENHANCED | UNGRADEABLE")
    focus_score: float = Field(..., description="Tenengrad focus gradient energy score")
    mean_illumination: float = Field(..., description="Mean green channel illumination intensity")
    recapture_required: bool = Field(..., description="True if UNGRADEABLE")
    recapture_feedback: str = Field("", description="Actionable recapture feedback string")


class BiomarkerCountsV1(BaseModel):
    microaneurysms: int = Field(0, description="Count of detected microaneurysms")
    hard_exudates_area_px: int = Field(0, description="Area of hard exudates in pixels")
    hemorrhages: int = Field(0, description="Count of hemorrhages")


class ClinicalResultsV1(BaseModel):
    icdr_grade: int = Field(..., description="ICDR DR severity grade (0 to 4)")
    severity_label: str = Field(..., description="Clinical DR severity label")
    is_referable: bool = Field(..., description="True if ICDR grade >= 2")
    referable_confidence: float = Field(..., description="Platt-calibrated referral probability")
    biomarker_counts: BiomarkerCountsV1 = Field(default_factory=BiomarkerCountsV1)
    clinical_rule_match: str = Field("", description="Rule 4-2-1 diagnostic criteria string")


class ArtifactsV1(BaseModel):
    enhanced_image_url: Optional[str] = Field(None, description="URL for adaptive enhanced image")
    gradcam_heatmap_url: Optional[str] = Field(None, description="URL for Grad-CAM activation map")
    lesion_overlay_url: Optional[str] = Field(None, description="URL for biomarker overlay map")


class ScreeningV1Response(BaseModel):
    patient_id: str = Field(..., description="Patient identifier")
    quality_assessment: QualityAssessmentV1
    clinical_results: Optional[ClinicalResultsV1] = None
    artifacts: ArtifactsV1
    triage_action: str = Field(..., description="ROUTINE_12MO_SCREENING | REFER_TO_SPECIALIST | URGENT_PDR_REFERRAL")


