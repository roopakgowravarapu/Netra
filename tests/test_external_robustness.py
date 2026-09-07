"""Unit tests for External Validation and Robustness Testing module."""

import sys
from pathlib import Path
import cv2
import numpy as np
import pytest
import torch

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.evaluation.external_validation import evaluate_external_dataset
from src.evaluation.robustness import (
    apply_brightness_change,
    apply_contrast_change,
    apply_gaussian_blur,
    apply_gaussian_noise,
    apply_resolution_downscaling,
    evaluate_model_robustness,
)
from src.training.model import get_model


def test_perturbation_generators():
    """Verify that all image perturbations run and preserve image shapes."""
    img = np.random.randint(0, 256, (224, 224, 3), dtype=np.uint8)

    b_img = apply_brightness_change(img, 1.2)
    assert b_img.shape == (224, 224, 3)

    c_img = apply_contrast_change(img, 1.2)
    assert c_img.shape == (224, 224, 3)

    blur_img = apply_gaussian_blur(img, 5)
    assert blur_img.shape == (224, 224, 3)

    noise_img = apply_gaussian_noise(img, 15.0)
    assert noise_img.shape == (224, 224, 3)

    down_img = apply_resolution_downscaling(img, 112)
    assert down_img.shape == (224, 224, 3)


def test_robustness_execution():
    """Verify robustness testing runner on dummy model."""
    model = get_model(num_classes=5, pretrained=False)
    device = torch.device("cpu")
    dummy_imgs = [np.random.randint(0, 256, (224, 224, 3), dtype=np.uint8) for _ in range(2)]

    results = evaluate_model_robustness(model, dummy_imgs, device)
    assert "brightness_high" in results
    assert "gaussian_blur" in results
    assert "prediction_stability" in results["brightness_high"]
    assert 0.0 <= results["brightness_high"]["prediction_stability"] <= 1.0


def test_external_validation_missing_file():
    """Verify graceful handling when external CSV manifest is missing."""
    model = get_model(num_classes=5, pretrained=False)
    device = torch.device("cpu")
    res = evaluate_external_dataset(model, Path("non_existent.csv"), device)
    assert res["status"] == "NOT_AVAILABLE"
