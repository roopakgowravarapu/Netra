"""Automated unit & API tests for Telemedicine Workflow."""

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


def test_create_and_list_screening_case():
    """Verify case creation and listing."""
    img = np.zeros((300, 300, 3), dtype=np.uint8)
    cv2.circle(img, (150, 150), 120, (30, 70, 200), -1)
    _, encoded = cv2.imencode(".jpg", img)
    files = {"file": ("case_test.jpg", encoded.tobytes(), "image/jpeg")}

    res = client.post("/api/cases", files=files)
    assert res.status_code == 200
    case_data = res.json()
    assert "case_id" in case_data
    assert case_data["status"] == "REQUIRES_SPECIALIST_REVIEW"

    # List cases
    list_res = client.get("/api/cases")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1


def test_specialist_review_submission():
    """Verify remote specialist review submission."""
    img = np.zeros((300, 300, 3), dtype=np.uint8)
    cv2.circle(img, (150, 150), 120, (30, 70, 200), -1)
    _, encoded = cv2.imencode(".jpg", img)
    files = {"file": ("case_review.jpg", encoded.tobytes(), "image/jpeg")}

    res = client.post("/api/cases", files=files)
    case_id = res.json()["case_id"]

    # Submit Specialist Review (Confirm AI result)
    review_payload = {
        "decision": "confirm",
        "specialist_notes": "AI diagnosis verified. Patient referred to local clinic.",
        "specialist_id": "dr_smith_eyecare",
    }
    rev_res = client.post(f"/api/cases/{case_id}/review", json=review_payload)
    assert rev_res.status_code == 200
    data = rev_res.json()
    assert data["status"] == "SPECIALIST_REVIEWED"
    assert data["specialist_decision"] == "confirm"


def test_invalid_specialist_review_payload():
    """Verify invalid decision strings trigger 400 Bad Request."""
    img = np.zeros((300, 300, 3), dtype=np.uint8)
    cv2.circle(img, (150, 150), 120, (30, 70, 200), -1)
    _, encoded = cv2.imencode(".jpg", img)
    files = {"file": ("case_bad.jpg", encoded.tobytes(), "image/jpeg")}

    res = client.post("/api/cases", files=files)
    case_id = res.json()["case_id"]

    bad_payload = {"decision": "invalid_action_name"}
    rev_res = client.post(f"/api/cases/{case_id}/review", json=bad_payload)
    assert rev_res.status_code == 400
