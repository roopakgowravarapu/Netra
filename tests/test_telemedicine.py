"""Automated unit & API tests for Telemedicine Workflow & Strict State Machine."""

import sys
from pathlib import Path
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.main import app
from backend.app.services.case_service import clear_cases

client = TestClient(app)


def _get_dummy_fundus_file(name="fundus.jpg", gradable=True):
    img = np.zeros((300, 300, 3), dtype=np.uint8)
    if gradable:
        cv2.circle(img, (150, 150), 120, (30, 70, 200), -1)
    _, encoded = cv2.imencode(".jpg", img)
    return {"file": (name, encoded.tobytes(), "image/jpeg")}


def setup_function():
    """Reset case database before each test."""
    clear_cases()


def test_1_confirm_decision():
    """Test 1: Specialist confirms AI result -> status transitions to CONFIRMED."""
    files = _get_dummy_fundus_file("confirm_test.jpg")
    create_res = client.post("/api/cases", files=files)
    assert create_res.status_code == 200
    case_id = create_res.json()["case_id"]

    review_res = client.post(
        f"/api/cases/{case_id}/review",
        json={
            "decision": "CONFIRMED",
            "specialist_notes": "Clinical findings match AI assessment.",
            "specialist_id": "dr_retina_specialist",
        },
    )
    assert review_res.status_code == 200
    data = review_res.json()
    assert data["status"] == "CONFIRMED"
    assert data["specialist_decision"] == "CONFIRMED"
    assert data["specialist_id"] == "dr_retina_specialist"
    assert data["history"][0]["specialist_decision"] == "CONFIRMED"


def test_2_override_decision():
    """Test 2: Specialist overrides grade -> status transitions to OVERRIDDEN with override_grade."""
    files = _get_dummy_fundus_file("override_test.jpg")
    create_res = client.post("/api/cases", files=files)
    assert create_res.status_code == 200
    case_id = create_res.json()["case_id"]

    review_res = client.post(
        f"/api/cases/{case_id}/review",
        json={
            "decision": "OVERRIDDEN",
            "override_grade": 3,
            "specialist_notes": "Macular edema identified; reclassifying to Severe DR.",
            "specialist_id": "dr_retina_specialist",
        },
    )
    assert review_res.status_code == 200
    data = review_res.json()
    assert data["status"] == "OVERRIDDEN"
    assert data["specialist_decision"] == "OVERRIDDEN"
    assert data["override_grade"] == 3
    assert data["history"][0]["override_grade"] == 3


def test_3_request_recapture():
    """Test 3: Specialist requests recapture -> status transitions to RECAPTURE_REQUIRED."""
    files = _get_dummy_fundus_file("recapture_req_test.jpg")
    create_res = client.post("/api/cases", files=files)
    assert create_res.status_code == 200
    case_id = create_res.json()["case_id"]

    review_res = client.post(
        f"/api/cases/{case_id}/review",
        json={
            "decision": "REQUEST_RECAPTURE",
            "specialist_notes": "Media haze and motion blur obscuring fovea. Please recapture.",
            "specialist_id": "dr_retina_specialist",
        },
    )
    assert review_res.status_code == 200
    data = review_res.json()
    assert data["status"] == "RECAPTURE_REQUIRED"
    assert data["specialist_decision"] == "REQUEST_RECAPTURE"
    assert data["history"][0]["specialist_decision"] == "REQUEST_RECAPTURE"


def test_4_recapture_image_reanalysis_and_status_reset():
    """Test 4: Recapture image upload triggers re-analysis, resets review fields, and returns to review queue."""
    # Step A: Create initial case
    files1 = _get_dummy_fundus_file("initial_scan.jpg")
    create_res = client.post("/api/cases", files=files1)
    case_id = create_res.json()["case_id"]

    # Step B: Request recapture
    client.post(
        f"/api/cases/{case_id}/review",
        json={"decision": "REQUEST_RECAPTURE", "specialist_notes": "Needs sharper scan."},
    )

    # Step C: Upload replacement image via recapture endpoint
    files2 = _get_dummy_fundus_file("replacement_scan.jpg")
    recapture_res = client.post(f"/api/cases/{case_id}/recapture", files=files2)
    assert recapture_res.status_code == 200
    recapture_data = recapture_res.json()

    assert recapture_data["status"] in ["REQUIRES_SPECIALIST_REVIEW", "URGENT_SPECIALIST_REVIEW"]
    assert recapture_data["attempt"] == 2
    assert recapture_data["specialist_decision"] is None
    assert recapture_data["specialist_notes"] is None
    assert len(recapture_data["history"]) == 2

    # Step D: Verify specialist can now submit a decision for attempt 2
    second_review_res = client.post(
        f"/api/cases/{case_id}/review",
        json={"decision": "CONFIRMED", "specialist_notes": "Replacement image is clear."},
    )
    assert second_review_res.status_code == 200
    assert second_review_res.json()["status"] == "CONFIRMED"


def test_5_direct_api_double_decision_protection():
    """Test 5: Directly calling review endpoint on an already-decided case triggers HTTP 400."""
    files = _get_dummy_fundus_file("double_decision.jpg")
    create_res = client.post("/api/cases", files=files)
    case_id = create_res.json()["case_id"]

    # First review: Confirm
    first_rev = client.post(
        f"/api/cases/{case_id}/review",
        json={"decision": "CONFIRMED", "specialist_notes": "Approved."},
    )
    assert first_rev.status_code == 200

    # Second review attempt must be rejected with 400
    second_rev = client.post(
        f"/api/cases/{case_id}/review",
        json={"decision": "OVERRIDDEN", "override_grade": 2},
    )
    assert second_rev.status_code == 400
    assert "Case has already been decided." in second_rev.json()["detail"]


def test_6_case_history_preservation():
    """Test 6: Multi-attempt case history preserves all previous attempt records immutably."""
    # Attempt 1: Upload and Request Recapture
    files1 = _get_dummy_fundus_file("attempt1.jpg")
    create_res = client.post("/api/cases", files=files1)
    case_id = create_res.json()["case_id"]

    client.post(
        f"/api/cases/{case_id}/review",
        json={
            "decision": "REQUEST_RECAPTURE",
            "specialist_notes": "Attempt 1 blurry.",
            "specialist_id": "dr_first_reviewer",
        },
    )

    # Attempt 2: Recapture via /predict with case_id Form parameter
    files2 = _get_dummy_fundus_file("attempt2.jpg")
    predict_res = client.post("/predict", files=files2, data={"case_id": case_id})
    assert predict_res.status_code == 200

    # Attempt 2: Specialist Overrides
    client.post(
        f"/api/cases/{case_id}/review",
        json={
            "decision": "OVERRIDDEN",
            "override_grade": 2,
            "specialist_notes": "Attempt 2 shows moderate DR lesions.",
            "specialist_id": "dr_second_reviewer",
        },
    )

    # Retrieve case by ID and inspect complete history
    get_res = client.get(f"/api/cases/{case_id}")
    assert get_res.status_code == 200
    case = get_res.json()

    assert case["attempt"] == 2
    assert len(case["history"]) == 2

    # Verify Attempt 1 record is preserved exactly
    att1 = case["history"][0]
    assert att1["attempt"] == 1
    assert att1["specialist_decision"] == "REQUEST_RECAPTURE"
    assert att1["specialist_notes"] == "Attempt 1 blurry."
    assert att1["specialist_id"] == "dr_first_reviewer"

    # Verify Attempt 2 record
    att2 = case["history"][1]
    assert att2["attempt"] == 2
    assert att2["specialist_decision"] == "OVERRIDDEN"
    assert att2["override_grade"] == 2
    assert att2["specialist_notes"] == "Attempt 2 shows moderate DR lesions."
    assert att2["specialist_id"] == "dr_second_reviewer"


def test_7_delete_case_from_screening_queue():
    """Test 7: Deleting a case removes it from the queue and subsequent lookups return 404."""
    files = _get_dummy_fundus_file("delete_test.jpg")
    create_res = client.post("/api/cases", files=files)
    assert create_res.status_code == 200
    case_id = create_res.json()["case_id"]

    # Verify case exists
    get_res = client.get(f"/api/cases/{case_id}")
    assert get_res.status_code == 200

    # Delete case
    del_res = client.delete(f"/api/cases/{case_id}")
    assert del_res.status_code == 200
    assert del_res.json()["case_id"] == case_id

    # Verify case no longer exists
    get_res2 = client.get(f"/api/cases/{case_id}")
    assert get_res2.status_code == 404

    # Deleting non-existent case returns 404
    del_res2 = client.delete(f"/api/cases/{case_id}")
    assert del_res2.status_code == 404


def test_8_delete_all_cases():
    """Test 8: Bulk deleting all screening cases empties queue."""
    # Ensure at least one case exists
    files = _get_dummy_fundus_file("bulk_delete.jpg")
    client.post("/api/cases", files=files)

    # Delete all cases
    del_all = client.delete("/api/cases")
    assert del_all.status_code == 200
    assert "deleted successfully" in del_all.json()["message"]

    # Queue should now be empty
    list_res = client.get("/api/cases")
    assert list_res.status_code == 200
    assert len(list_res.json()) == 0


def test_9_delete_patients_and_history():
    """Test 9: Clearing patient visit history and deleting patient records."""
    # Register patient with visit
    p_data = {
        "patient_id": "PAT-DELETE-TEST",
        "name": "Jane Deletable",
        "age": 45,
        "gender": "Female",
        "diabetes_type": "Type 2",
        "diabetes_duration_years": 4.0,
    }
    create_p = client.post("/api/patients", json=p_data)
    assert create_p.status_code == 201

    # Add a screening visit via /predict
    files = _get_dummy_fundus_file("patient_visit.png")
    pred_res = client.post(
        "/predict",
        files=files,
        data={"patient_id": "PAT-DELETE-TEST", "patient_name": "Jane Deletable", "eye_examined": "OD"},
    )
    assert pred_res.status_code == 200

    # Verify visit exists
    hist_res = client.get("/api/patients/PAT-DELETE-TEST/history")
    assert hist_res.status_code == 200
    assert len(hist_res.json()) >= 1

    # Clear history for patient
    clear_hist = client.delete("/api/patients/PAT-DELETE-TEST/history")
    assert clear_hist.status_code == 200
    hist_res2 = client.get("/api/patients/PAT-DELETE-TEST/history")
    assert len(hist_res2.json()) == 0

    # Delete single patient
    del_p = client.delete("/api/patients/PAT-DELETE-TEST")
    assert del_p.status_code == 200
    check_p = client.get("/api/patients/PAT-DELETE-TEST")
    assert check_p.status_code == 404

    # Delete all patients
    del_all_p = client.delete("/api/patients")
    assert del_all_p.status_code == 200
    all_p = client.get("/api/patients")
    assert len(all_p.json()) == 0

