from typing import Optional
from fastapi import APIRouter, File, Form, UploadFile
from backend.app.schemas.screening import ScreeningReportResponse, ScreeningV1Response
from backend.app.services.case_service import create_screening_case, recapture_case
from backend.app.services.patient_service import record_screening_visit
from backend.app.services.screening_service import process_image_upload, process_screening_v1

router = APIRouter(tags=["Screening"])


@router.post("/predict", response_model=ScreeningReportResponse)
async def predict_dr(
    file: UploadFile = File(...),
    case_id: Optional[str] = Form(None),
    patient_id: Optional[str] = Form(None),
    patient_name: Optional[str] = Form(None),
    age: Optional[int] = Form(None),
    gender: Optional[str] = Form(None),
    diabetes_type: Optional[str] = Form(None),
    diabetes_duration_years: Optional[float] = Form(None),
    eye_examined: Optional[str] = Form("OD"),
    patient_consent: Optional[bool] = Form(True),
):
    """
    Accepts a fundus image upload, performs Image Quality Assessment (IQA),
    and if gradable, generates DR prediction, calibrated confidence, pure Python retinal analysis,
    and Grad-CAM explanation.
    Automatically enqueues the screening case into the Telemedicine consultation network
    and records the patient longitudinal screening visit.
    If case_id is provided, updates an existing case undergoing recapture.
    """
    report = await process_image_upload(
        file,
        patient_id=patient_id,
        patient_name=patient_name,
        age=age,
        gender=gender,
        diabetes_type=diabetes_type,
        diabetes_duration_years=diabetes_duration_years,
        eye_examined=eye_examined,
        patient_consent=patient_consent,
    )

    if case_id and case_id.strip():
        case = recapture_case(case_id.strip(), report)
    else:
        case = create_screening_case(report)
    report["case_id"] = case.case_id

    # Record longitudinal patient screening visit
    try:
        record_screening_visit(
            patient_id=report.get("patient_id") or "PAT-UNKNOWN",
            patient_name=report.get("patient_name") or "Anonymous Patient",
            age=report.get("age"),
            gender=report.get("gender"),
            diabetes_type=report.get("diabetes_type"),
            diabetes_duration_years=report.get("diabetes_duration_years"),
            eye_examined=report.get("eye_examined") or "OD",
            report_dict=report,
            case_id=case.case_id,
        )
    except Exception:
        pass

    return report


@router.post("/api/v1/screen", response_model=ScreeningV1Response)
async def screen_v1(
    image: UploadFile = File(...),
    patient_id: str = Form("PATIENT_001"),
):
    """
    POST /api/v1/screen
    Accepts fundus image upload and patient_id, executes adaptive quality gate & DR grading,
    and returns standardized Netra V1 JSON data contract.
    """
    return await process_screening_v1(image, patient_id)
