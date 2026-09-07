"""Automated API tests for Netra FastAPI backend."""

import io
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test GET /health returns 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_predict_unsupported_file_type():
    """Test POST /predict rejects non-image files."""
    files = {"file": ("test.txt", b"Hello world text content", "text/plain")}
    response = client.post("/predict", files=files)
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_predict_invalid_corrupt_file():
    """Test POST /predict handles corrupted image files safely."""
    files = {"file": ("corrupt.jpg", b"NOT_AN_IMAGE_DATA_12345", "image/jpeg")}
    response = client.post("/predict", files=files)
    assert response.status_code == 400
    assert "Failed to decode image" in response.json()["detail"]


def test_predict_oversized_file():
    """Test POST /predict rejects files exceeding 15MB."""
    oversized_data = b"0" * (16 * 1024 * 1024)
    files = {"file": ("huge.jpg", oversized_data, "image/jpeg")}
    response = client.post("/predict", files=files)
    assert response.status_code == 413
    assert "exceeds maximum allowed limit" in response.json()["detail"]


def test_predict_valid_gradable_image():
    """Test POST /predict with a valid fundus image."""
    # Create valid synthetic fundus image JPEG
    img = np.zeros((300, 300, 3), dtype=np.uint8)
    cv2.circle(img, (150, 150), 120, (30, 70, 200), -1)
    cv2.line(img, (50, 150), (250, 150), (10, 200, 220), 2)
    _, encoded = cv2.imencode(".jpg", img)

    files = {"file": ("valid.jpg", encoded.tobytes(), "image/jpeg")}
    response = client.post("/predict", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["image_quality"]["status"] == "gradable"
    assert data["dr_prediction"] is not None
    assert 0 <= data["dr_prediction"]["grade"] <= 4
    assert 0.0 <= data["dr_prediction"]["confidence"] <= 1.0


def test_predict_ungradable_image():
    """Test POST /predict with a dark ungradable image."""
    dark_img = np.zeros((300, 300, 3), dtype=np.uint8)
    _, encoded = cv2.imencode(".jpg", dark_img)

    files = {"file": ("dark.jpg", encoded.tobytes(), "image/jpeg")}
    response = client.post("/predict", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["image_quality"]["status"] == "ungradable"
    assert data["dr_prediction"] is None
    assert "RECAPTURE" in data["recommendation"]
