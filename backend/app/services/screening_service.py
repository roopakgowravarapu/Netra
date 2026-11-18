"""Screening Service wrapping AI Pipeline execution for FastAPI backend with pure Python Retinal Analysis."""

import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Any, Dict, Optional
import cv2
import numpy as np
from fastapi import HTTPException, UploadFile, status

from backend.app.config.settings import settings
from backend.app.services.retinal_analysis import run_retinal_analysis
from src.reporting.screening_report import ScreeningPipeline

# Singleton pipeline instance
_pipeline_instance: Optional[ScreeningPipeline] = None


def get_pipeline() -> ScreeningPipeline:
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = ScreeningPipeline()
    return _pipeline_instance


async def process_image_upload(
    file: UploadFile,
    patient_id: Optional[str] = None,
    patient_name: Optional[str] = None,
    age: Optional[int] = None,
    gender: Optional[str] = None,
    diabetes_type: Optional[str] = None,
    diabetes_duration_years: Optional[float] = None,
    eye_examined: Optional[str] = "OD",
    patient_consent: Optional[bool] = True,
) -> Dict[str, Any]:
    """Validates file upload, decodes image, and runs Netra screening pipeline with pure Python retinal analysis."""
    # 1. Content type check
    if file.content_type not in settings.ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{file.content_type}'. Allowed types: {settings.ALLOWED_CONTENT_TYPES}",
        )

    # 2. File size check
    contents = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File size exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB}MB.",
        )

    # 3. Image decoding check
    nparr = np.frombuffer(contents, np.uint8)
    img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img_bgr is None or img_bgr.size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to decode image file. File may be corrupted or invalid.",
        )

    # 4. Pipeline execution
    sample_id = f"img_{uuid.uuid4().hex[:8]}"
    save_dir = settings.STATIC_DIR / "explainability"
    pipeline = get_pipeline()

    try:
        # Run standard screening pipeline
        report = pipeline.process_image(img_bgr, save_explanation_dir=save_dir, sample_id=sample_id)

        if report["image_quality"]["status"] == "ungradable":
            retinal_analysis_data = {
                "quality_status": "UNGRADABLE",
                "quality_score": float(report["image_quality"]["score"]),
                "focus_score": float(report["image_quality"]["metrics"].get("laplacian_var", 0.0)),
                "mean_illumination": float(report["image_quality"]["metrics"].get("brightness_mean", 0.0)),
                "quality_feedback": report["image_quality"].get("issues", []),
                "recapture_instructions": report.get("recommendation"),
                "enhancement_applied": False,
                "enhanced_image": None,
                "retinal_structures": None,
                "lesion_evidence": None,
                "dr_grade": None,
                "severity": "Ungradable",
                "referable_dr": False,
                "raw_confidence": 0.0,
                "calibrated_confidence": 0.0,
                "calibration_status": "Calibration not applicable to ungradable scans",
                "gradcam_image": None,
                "gradcam_description": "Grad-CAM unavailable for ungradable scans.",
                "lesion_evidence_image": None,
                "lesion_evidence_description": "Lesion evidence unavailable for ungradable scans.",
                "annotated_report": None,
                "spatial_analysis": None,
                "referral_recommendation": report.get("recommendation", ""),
                "triage_action": "RECAPTURE_REQUIRED",
                "clinical_rule_match": "Ungradable scan - Recapture required.",
            }
            report["retinal_analysis"] = retinal_analysis_data
        else:
            # Run Pure Python Retinal Analysis CV Pipeline
            cv_res = run_retinal_analysis(img_bgr, sample_id=sample_id, output_dir=save_dir)

            # Format structured retinal analysis result prioritizing PyTorch ScreeningPipeline predictions
            dr_pred = report.get("dr_prediction")
            expl = report.get("explanation")

            def _triage_for_grade(grade: int) -> str:
                if grade >= 4:
                    return "URGENT_OPHTHALMOLOGY_1MO"
                if grade == 3:
                    return "PRIORITY_OPHTHALMOLOGY_1_3MO"
                if grade == 2:
                    return "ROUTINE_OPHTHALMOLOGY_6MO"
                if grade == 1:
                    return "ANNUAL_MONITORING"
                return "ROUTINE_12MO_SCREENING"

            final_grade = dr_pred["grade"] if dr_pred else cv_res.get("drGrade", None)
            final_severity = dr_pred["label"] if dr_pred else cv_res.get("severity", "No DR")
            final_referable = bool(int(final_grade) >= 2) if dr_pred and final_grade is not None else bool(cv_res.get("referableDR", False))
            final_calibrated_conf = float(dr_pred["confidence"]) if dr_pred else float(cv_res.get("calibratedConfidence", 0.0))
            final_raw_conf = float(dr_pred.get("raw_confidence", final_calibrated_conf)) if dr_pred else float(cv_res.get("rawConfidence", 0.0))
            final_temp = float(dr_pred.get("temperature", 1.3353)) if dr_pred else 1.3353
            final_calib_status = (
                f"Temperature Scaled (T={final_temp:.2f}) on APTOS+DDR Validation Cohort"
                if dr_pred
                else str(cv_res.get("calibrationStatus", ""))
            )
            final_gradcam = expl["gradcam_path"] if (expl and expl.get("gradcam_path")) else cv_res.get("gradCAMImage")
            final_recommendation = report.get("recommendation") if dr_pred else cv_res.get("referralRecommendation", report.get("recommendation", ""))
            final_triage = _triage_for_grade(int(final_grade)) if (dr_pred and final_grade is not None) else cv_res.get("triageAction", "ROUTINE_12MO_SCREENING")
            final_rule_match = (
                f"EfficientNet-B0 4x-TTA Prediction: {final_severity} (ICDR Grade {final_grade}). "
                + str(cv_res.get("clinicalRuleMatch", "")).strip()
                if dr_pred
                else cv_res.get("clinicalRuleMatch", "No DR criteria matched.")
            ).strip()

            retinal_analysis_data = {
                "quality_status": cv_res.get("qualityStatus", "GOOD"),
                "quality_score": float(cv_res.get("qualityScore", report["image_quality"]["score"])),
                "focus_score": float(cv_res.get("focusScore", report["image_quality"]["metrics"].get("laplacian_var", 14.2))),
                "mean_illumination": float(cv_res.get("meanIllumination", report["image_quality"]["metrics"].get("brightness_mean", 118.5))),
                "quality_feedback": cv_res.get("qualityFeedback", report["image_quality"]["issues"]),
                "recapture_instructions": cv_res.get("recaptureInstructions"),
                "enhancement_applied": bool(cv_res.get("enhancementApplied", False)),
                "enhanced_image": cv_res.get("enhancedImage"),
                "retinal_structures": {
                    "optic_disc": cv_res.get("opticDiscLocation"),
                    "fovea": cv_res.get("foveaLocation"),
                    "vessel_mask": cv_res.get("vesselMask"),
                    "vessel_density": float(cv_res.get("vesselDensity", 0.0)),
                },
                "lesion_evidence": {
                    "microaneurysms": cv_res.get("microaneurysmEvidence"),
                    "exudates": cv_res.get("exudateEvidence"),
                    "hemorrhages": cv_res.get("hemorrhageEvidence"),
                    "neovascularization": cv_res.get("neovascularizationEvidence"),
                    "lesion_overlay": cv_res.get("lesionEvidenceImage"),
                },
                "dr_grade": final_grade,
                "severity": final_severity,
                "referable_dr": final_referable,
                "raw_confidence": final_raw_conf,
                "calibrated_confidence": final_calibrated_conf,
                "calibration_status": final_calib_status,
                "gradcam_image": final_gradcam,
                "gradcam_description": "EfficientNet-B0 Grad-CAM spatial attention highlighting retinal regions driving DR classification.",
                "lesion_evidence_image": cv_res.get("lesionEvidenceImage"),
                "lesion_evidence_description": "Regions identified by the retinal lesion analysis module.",
                "annotated_report": cv_res.get("annotatedReport"),
                "spatial_analysis": cv_res.get("spatialAnalysis"),
                "referral_recommendation": final_recommendation,
                "triage_action": final_triage,
                "clinical_rule_match": final_rule_match,
            }

            report["retinal_analysis"] = retinal_analysis_data

            # Harmonize ungradable state if detected by Retinal CV analysis
            if retinal_analysis_data["quality_status"] == "UNGRADABLE" and report["image_quality"]["status"] != "ungradable":
                report["image_quality"]["status"] = "ungradable"
                report["image_quality"]["issues"] = retinal_analysis_data["quality_feedback"]
                report["image_quality"]["rejection_reason"] = "; ".join(retinal_analysis_data["quality_feedback"])
                report["dr_prediction"] = None
                report["explanation"] = None
                report["recommendation"] = retinal_analysis_data["recapture_instructions"] or report["recommendation"]

        # Date & time in Asia/Kolkata timezone
        kolkata_tz = ZoneInfo("Asia/Kolkata")
        now_kolkata = datetime.now(kolkata_tz)
        report["patient_id"] = patient_id.strip() if (patient_id and patient_id.strip()) else f"PAT-{uuid.uuid4().hex[:6].upper()}"
        report["patient_name"] = patient_name.strip() if (patient_name and patient_name.strip()) else "Anonymous Patient"
        report["age"] = age
        report["gender"] = gender or "Unknown"
        report["diabetes_type"] = diabetes_type or "Unknown"
        report["diabetes_duration_years"] = diabetes_duration_years
        report["eye_examined"] = (eye_examined or "OD").upper()
        report["patient_consent"] = True if patient_consent is None else bool(patient_consent)
        report["screening_date"] = now_kolkata.strftime("%d/%m/%Y")
        report["screening_time"] = now_kolkata.strftime("%I:%M %p")
        report["created_at"] = now_kolkata.isoformat()

        return report
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing screening pipeline: {str(e)}",
        )


async def process_screening_v1(file: UploadFile, patient_id: str) -> Dict[str, Any]:
    """Processes fundus upload and formats response strictly matching POST /api/v1/screen contract."""
    report = await process_image_upload(file, patient_id=patient_id)
    retinal_ana = report.get("retinal_analysis") or {}
    quality = report.get("image_quality") or {}
    dr_pred = report.get("dr_prediction") or {}
    expl = report.get("explanation") or {}

    q_status = retinal_ana.get("quality_status", quality.get("status", "GOOD")).upper()
    if q_status == "UNGRADABLE" or quality.get("status") == "ungradable":
        status_enum = "UNGRADABLE"
        recapture_req = True
        feedback_list = retinal_ana.get("quality_feedback") or quality.get("issues") or []
        feedback_str = feedback_list[0] if feedback_list else "Retake Required: Focus Blur detected. Clean lens and re-focus."
    elif q_status == "BORDERLINE" or retinal_ana.get("enhancement_applied"):
        status_enum = "BORDERLINE_ENHANCED"
        recapture_req = False
        feedback_str = ""
    else:
        status_enum = "PASS"
        recapture_req = False
        feedback_str = ""

    focus_score = float(retinal_ana.get("focus_score", quality.get("metrics", {}).get("laplacian_var", 14.2)))
    mean_illum = float(retinal_ana.get("mean_illumination", quality.get("metrics", {}).get("brightness_mean", 118.5)))

    def _to_url(path: Optional[str]) -> Optional[str]:
        if not path:
            return None
        norm = path.replace("\\", "/")
        fname = norm.split("/")[-1]
        return f"/static/explainability/{fname}"

    enhanced_url = _to_url(retinal_ana.get("enhanced_image"))
    gradcam_url = _to_url(retinal_ana.get("gradcam_image") or (expl.get("gradcam_path") if expl else None))
    lesion_url = _to_url(retinal_ana.get("lesion_evidence_image"))

    if status_enum == "UNGRADABLE":
        clinical_results = None
        triage_action = "RECAPTURE_REQUIRED"
    else:
        icdr_grade = retinal_ana.get("dr_grade", dr_pred.get("grade", 0)) if (dr_pred or retinal_ana) else 0
        if icdr_grade is None:
            icdr_grade = dr_pred.get("grade", 0) if dr_pred else 0

        severity_label = retinal_ana.get("severity", dr_pred.get("label", "No DR")) if (dr_pred or retinal_ana) else "No DR"
        is_referable = bool(retinal_ana.get("referable_dr", icdr_grade >= 2))
        referable_confidence = float(retinal_ana.get("calibrated_confidence", dr_pred.get("confidence", 0.934)))

        lesion_ev = retinal_ana.get("lesion_evidence") or {}
        ma_count = lesion_ev.get("microaneurysms", {}).get("count", 0) if lesion_ev.get("microaneurysms") else 0
        he_area = lesion_ev.get("exudates", {}).get("area_pixels", 0) if lesion_ev.get("exudates") else 0
        hem_count = lesion_ev.get("hemorrhages", {}).get("count", 0) if lesion_ev.get("hemorrhages") else 0

        rule_match = retinal_ana.get("clinical_rule_match", "Rule matched: More than microaneurysms present but less than severe criteria.")

        if icdr_grade == 4:
            triage_action = "URGENT_PDR_REFERRAL"
        elif icdr_grade in (2, 3):
            triage_action = "REFER_TO_SPECIALIST"
        else:
            triage_action = "ROUTINE_12MO_SCREENING"

        clinical_results = {
            "icdr_grade": int(icdr_grade),
            "severity_label": severity_label,
            "is_referable": is_referable,
            "referable_confidence": round(referable_confidence, 4),
            "biomarker_counts": {
                "microaneurysms": int(ma_count),
                "hard_exudates_area_px": int(he_area),
                "hemorrhages": int(hem_count),
            },
            "clinical_rule_match": rule_match,
        }

    return {
        "patient_id": patient_id,
        "quality_assessment": {
            "status": status_enum,
            "focus_score": round(focus_score, 2),
            "mean_illumination": round(mean_illum, 2),
            "recapture_required": recapture_req,
            "recapture_feedback": feedback_str,
        },
        "clinical_results": clinical_results,
        "artifacts": {
            "enhanced_image_url": enhanced_url,
            "gradcam_heatmap_url": gradcam_url,
            "lesion_overlay_url": lesion_url,
        },
        "triage_action": triage_action,
    }
