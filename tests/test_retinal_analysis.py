"""Automated Integration Tests for Pure Python Retinal Analysis Pipeline in Netra."""

import sys
from pathlib import Path
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.main import app

client = TestClient(app)


def test_retinal_analysis_pipeline_gradable_image():
    """Verify that a valid fundus image produces full retinal structures, lesion analysis, and DR grading."""
    # Synthesize valid circular fundus image
    img = np.zeros((300, 300, 3), dtype=np.uint8)
    cv2.circle(img, (150, 150), 120, (30, 70, 200), -1)  # orange-red retina
    cv2.circle(img, (110, 150), 20, (50, 180, 230), -1)  # optic disc candidate
    cv2.line(img, (60, 150), (240, 150), (10, 190, 220), 2)  # main vessel
    cv2.circle(img, (180, 150), 4, (15, 20, 120), -1)   # microaneurysm candidate

    _, encoded = cv2.imencode(".png", img)
    files = {"file": ("test_retina.png", encoded.tobytes(), "image/png")}
    data_form = {
        "patient_id": "PAT-TEST01",
        "patient_name": "Test Patient",
        "age": "52",
        "gender": "Female",
        "diabetes_type": "Type 2",
        "diabetes_duration_years": "8.5",
        "eye_examined": "OD",
    }
    response = client.post("/predict", files=files, data=data_form)

    assert response.status_code == 200
    data = response.json()

    # 1. Base response fields
    assert "retinal_analysis" in data
    r_data = data["retinal_analysis"]

    # 2. Quality assessment
    assert r_data["quality_status"] in ["GOOD", "BORDERLINE"]
    assert 0.0 <= r_data["quality_score"] <= 1.0

    # 3. Retinal structures
    assert "retinal_structures" in r_data
    structures = r_data["retinal_structures"]
    assert structures["optic_disc"] is not None
    assert "x" in structures["optic_disc"]
    assert "y" in structures["optic_disc"]
    assert structures["fovea"] is not None
    assert "x" in structures["fovea"]
    assert "vessel_density" in structures

    # 4. Lesions
    assert "lesion_evidence" in r_data
    lesions = r_data["lesion_evidence"]
    assert "microaneurysms" in lesions
    assert "exudates" in lesions
    assert "hemorrhages" in lesions
    assert "neovascularization" in lesions

    # 5. DR Grading & Referable DR
    assert r_data["dr_grade"] in [0, 1, 2, 3, 4]
    assert isinstance(r_data["referable_dr"], bool)
    assert 0.0 <= r_data["raw_confidence"] <= 1.0
    assert 0.0 <= r_data["calibrated_confidence"] <= 1.0

    # 6. Patient demographics stored
    assert data["patient_id"] == "PAT-TEST01"
    assert data["patient_name"] == "Test Patient"
    assert data["age"] == 52
    assert data["gender"] == "Female"
    assert data["eye_examined"] == "OD"


def test_retinal_analysis_pipeline_ungradable_image():
    """Verify that a dark blurry image is flagged as UNGRADABLE with recapture guidance."""
    dark_img = np.zeros((300, 300, 3), dtype=np.uint8)
    _, encoded = cv2.imencode(".png", dark_img)
    files = {"file": ("test_dark.png", encoded.tobytes(), "image/png")}
    response = client.post("/predict", files=files)

    assert response.status_code == 200
    data = response.json()
    r_data = data["retinal_analysis"]

    assert r_data["quality_status"] == "UNGRADABLE"
    assert r_data["dr_grade"] is None
    assert r_data["referable_dr"] is False
    assert "recapture_instructions" in r_data
    assert r_data["recapture_instructions"] is not None


def test_patient_management_api():
    """Verify Patient Management API listing, creation, and longitudinal history endpoints."""
    # Register / update patient
    create_payload = {
        "patient_id": "PAT-TEST02",
        "name": "Ramesh Kumar",
        "age": 58,
        "gender": "Male",
        "diabetes_type": "Type 2",
        "diabetes_duration_years": 10.0,
    }
    res = client.post("/api/patients", json=create_payload)
    assert res.status_code == 201
    p_data = res.json()
    assert p_data["patient_id"] == "PAT-TEST02"
    assert p_data["name"] == "Ramesh Kumar"

    # Query patient by ID
    res = client.get("/api/patients/PAT-TEST02")
    assert res.status_code == 200
    assert res.json()["name"] == "Ramesh Kumar"

    # Search patients
    res = client.get("/api/patients?query=Ramesh")
    assert res.status_code == 200
    results = res.json()
    assert any(p["patient_id"] == "PAT-TEST02" for p in results)

    # Progression endpoint
    res = client.get("/api/patients/PAT-TEST02/progression")
    assert res.status_code == 200
    prog = res.json()
    assert "disclaimer" in prog
    assert prog["patient_id"] == "PAT-TEST02"
