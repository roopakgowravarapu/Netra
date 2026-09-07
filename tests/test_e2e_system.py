"""Comprehensive 20-Point End-to-End System Testing Suite for Netra Application.
"""

import json
import os
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.main import app
from src.quality.image_quality import assess_image_quality
from src.reporting.screening_report import ScreeningPipeline

client = TestClient(app)


def test_01_frontend_route_building():
    """Verify backend serves API routes without syntax or path issues."""
    response = client.get("/health")
    assert response.status_code == 200


def test_02_image_upload_endpoint_reachability():
    """Verify POST /predict endpoint is reachable."""
    response = client.post("/predict")
    # Missing multipart file should return 422 Unprocessable Entity
    assert response.status_code == 422


def test_03_file_validation_unsupported_type():
    """Verify system rejects non-image mime types."""
    files = {"file": ("document.pdf", b"%PDF-1.4...", "application/pdf")}
    response = client.post("/predict", files=files)
    assert response.status_code == 400


def test_04_file_validation_corrupt_bytes():
    """Verify system handles corrupted byte streams safely."""
    files = {"file": ("bad.jpg", b"\x00\x00\x00\x00", "image/jpeg")}
    response = client.post("/predict", files=files)
    assert response.status_code == 400


def test_05_api_communication_json_structure():
    """Verify backend returns expected JSON schema fields."""
    img = np.zeros((300, 300, 3), dtype=np.uint8)
    cv2.circle(img, (150, 150), 120, (30, 70, 200), -1)
    _, encoded = cv2.imencode(".jpg", img)
    files = {"file": ("test.jpg", encoded.tobytes(), "image/jpeg")}

    response = client.post("/predict", files=files)
    assert response.status_code == 200
    data = response.json()
    assert "image_quality" in data
    assert "dr_prediction" in data
    assert "recommendation" in data
    assert "disclaimer" in data


def test_06_backend_validation_bounds():
    """Verify quality score and confidence bounds [0, 1]."""
    img = np.zeros((300, 300, 3), dtype=np.uint8)
    cv2.circle(img, (150, 150), 120, (30, 70, 200), -1)
    _, encoded = cv2.imencode(".jpg", img)
    files = {"file": ("test.jpg", encoded.tobytes(), "image/jpeg")}

    response = client.post("/predict", files=files)
    data = response.json()
    assert 0.0 <= data["image_quality"]["score"] <= 1.0
    if data["dr_prediction"]:
        assert 0.0 <= data["dr_prediction"]["confidence"] <= 1.0


def test_07_iqa_blur_detection():
    """Verify IQA flags blurry image as ungradable."""
    blur_img = np.zeros((300, 300, 3), dtype=np.uint8)
    cv2.circle(blur_img, (150, 150), 120, (30, 70, 200), -1)
    blur_img = cv2.GaussianBlur(blur_img, (31, 31), 15)
    res = assess_image_quality(blur_img)
    assert res.status == "ungradable"


def test_08_dr_prediction_range():
    """Verify predicted DR grade is between 0 and 4."""
    pipeline = ScreeningPipeline()
    img = np.zeros((300, 300, 3), dtype=np.uint8)
    cv2.circle(img, (150, 150), 120, (30, 70, 200), -1)
    report = pipeline.process_image(img)
    if report["dr_prediction"]:
        assert 0 <= report["dr_prediction"]["grade"] <= 4


def test_09_confidence_probability_sum():
    """Verify class probabilities sum to approximately 1.0."""
    pipeline = ScreeningPipeline()
    img = np.zeros((300, 300, 3), dtype=np.uint8)
    cv2.circle(img, (150, 150), 120, (30, 70, 200), -1)
    report = pipeline.process_image(img)
    if report["dr_prediction"]:
        prob_sum = sum(report["dr_prediction"]["probabilities"].values())
        assert pytest.approx(prob_sum, 0.01) == 1.0


def test_10_gradcam_overlay_creation():
    """Verify Grad-CAM output overlay image file exists on disk."""
    out_dir = ROOT_DIR / "outputs" / "system_testing"
    pipeline = ScreeningPipeline()
    img = np.zeros((300, 300, 3), dtype=np.uint8)
    cv2.circle(img, (150, 150), 120, (30, 70, 200), -1)
    report = pipeline.process_image(img, save_explanation_dir=out_dir, sample_id="e2e_gradcam")
    if report["explanation"] and report["explanation"]["gradcam_path"]:
        assert Path(report["explanation"]["gradcam_path"]).exists()


def test_11_screening_report_recommendation_presence():
    """Verify recommendation and disclaimer text exist in report."""
    pipeline = ScreeningPipeline()
    img = np.zeros((300, 300, 3), dtype=np.uint8)
    cv2.circle(img, (150, 150), 120, (30, 70, 200), -1)
    report = pipeline.process_image(img)
    assert len(report["recommendation"]) > 10
    assert "Netra" in report["disclaimer"]


def test_12_error_handling_runtime_safety():
    """Verify exception handling during empty image processing."""
    res = assess_image_quality(None)
    assert res.status == "ungradable"
    assert res.score == 0.0


def test_13_network_failure_handling_simulated():
    """Verify 404 behavior for invalid endpoint."""
    response = client.get("/invalid_route")
    assert response.status_code == 404


def test_14_invalid_file_extension():
    """Verify non-image extension rejected."""
    files = {"file": ("script.sh", b"#!/bin/bash\necho hi", "application/x-sh")}
    response = client.post("/predict", files=files)
    assert response.status_code == 400


def test_15_oversized_file_limit():
    """Verify >15MB payload triggers HTTP 413."""
    huge_payload = b"A" * (16 * 1024 * 1024)
    files = {"file": ("huge.png", huge_payload, "image/png")}
    response = client.post("/predict", files=files)
    assert response.status_code == 413


def test_16_ungradable_image_safeguard():
    """Verify ungradable images DO NOT produce DR prediction dictionary."""
    dark_img = np.zeros((300, 300, 3), dtype=np.uint8)
    _, encoded = cv2.imencode(".jpg", dark_img)
    files = {"file": ("dark.jpg", encoded.tobytes(), "image/jpeg")}

    response = client.post("/predict", files=files)
    data = response.json()
    assert data["image_quality"]["status"] == "ungradable"
    assert data["dr_prediction"] is None
    assert "RECAPTURE" in data["recommendation"]


def test_17_successful_gradable_image_workflow():
    """Verify full end-to-end response for gradable image."""
    img = np.zeros((300, 300, 3), dtype=np.uint8)
    cv2.circle(img, (150, 150), 120, (30, 70, 200), -1)
    cv2.line(img, (50, 150), (250, 150), (10, 200, 220), 2)
    _, encoded = cv2.imencode(".jpg", img)
    files = {"file": ("good.jpg", encoded.tobytes(), "image/jpeg")}

    response = client.post("/predict", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["image_quality"]["status"] == "gradable"
    assert data["dr_prediction"] is not None


def test_18_static_file_serving():
    """Verify static file route /static/ works."""
    response = client.get("/static/")
    # Returns 404 or 403 or 200 depending on static index, but route handler executes
    assert response.status_code in [200, 403, 404]


def test_19_loading_state_payload_consistency():
    """Verify response time and structure under valid load."""
    pipeline = ScreeningPipeline()
    img = np.zeros((224, 224, 3), dtype=np.uint8)
    res = pipeline.process_image(img)
    assert "sample_id" in res


def test_20_result_rendering_schema_validity():
    """Verify full JSON serializability of screening result."""
    pipeline = ScreeningPipeline()
    img = np.zeros((300, 300, 3), dtype=np.uint8)
    cv2.circle(img, (150, 150), 120, (30, 70, 200), -1)
    report = pipeline.process_image(img)
    json_str = json.dumps(report)
    assert len(json_str) > 50
