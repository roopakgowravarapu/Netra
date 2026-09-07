"""Unit tests for Screening Report Generation module."""

import sys
from pathlib import Path
import cv2
import numpy as np
import pytest

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.reporting.screening_report import ScreeningPipeline


def test_gradable_image_reporting():
    """Verify screening report output for a valid gradable fundus image."""
    pipeline = ScreeningPipeline()
    img = np.zeros((300, 300, 3), dtype=np.uint8)
    cv2.circle(img, (150, 150), 120, (30, 70, 200), -1)
    cv2.line(img, (50, 150), (250, 150), (10, 200, 220), 2)

    res = pipeline.process_image(img, sample_id="test_gradable")
    assert res["image_quality"]["status"] == "gradable"
    assert res["dr_prediction"] is not None
    assert 0 <= res["dr_prediction"]["grade"] <= 4
    assert 0.0 <= res["dr_prediction"]["confidence"] <= 1.0
    assert len(res["dr_prediction"]["probabilities"]) == 5
    assert "recommendation" in res
    assert "disclaimer" in res


def test_ungradable_image_reporting_safeguard():
    """Verify that ungradable images NEVER output DR predictions."""
    pipeline = ScreeningPipeline()
    dark_img = np.zeros((300, 300, 3), dtype=np.uint8)

    res = pipeline.process_image(dark_img, sample_id="test_ungradable")
    assert res["image_quality"]["status"] == "ungradable"
    assert res["dr_prediction"] is None
    assert res["explanation"] is None
    assert "RECAPTURE" in res["recommendation"]


def test_missing_explanation_and_corrupt_handling():
    """Verify pipeline resilience on corrupt or empty inputs."""
    pipeline = ScreeningPipeline()
    res = pipeline.process_image(np.array([]), sample_id="test_empty")
    assert res["image_quality"]["status"] == "ungradable"
    assert res["dr_prediction"] is None
