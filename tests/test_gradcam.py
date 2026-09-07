"""Unit tests for Grad-CAM explainability module."""

import sys
from pathlib import Path
import cv2
import numpy as np
import torch
import pytest

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.training.model import get_model
from src.explainability.gradcam import GradCAM, overlay_heatmap_on_image


def test_gradcam_execution_and_dimensions():
    """Verify Grad-CAM forward/backward passes and output dimensions."""
    model = get_model(num_classes=5, pretrained=False)
    gradcam = GradCAM(model)

    dummy_input = torch.randn(1, 3, 224, 224, requires_grad=True)
    heatmap, pred_class, probs = gradcam.generate_heatmap(dummy_input)

    assert heatmap.shape == (224, 224)
    assert 0 <= pred_class <= 4
    assert len(probs) == 5
    assert np.min(heatmap) >= 0.0
    assert np.max(heatmap) <= 1.0

    gradcam.remove_hooks()


def test_overlay_creation():
    """Verify heatmap overlay on original image."""
    dummy_img = np.random.randint(0, 256, (224, 224, 3), dtype=np.uint8)
    dummy_heatmap = np.random.rand(224, 224)

    overlay = overlay_heatmap_on_image(dummy_img, dummy_heatmap)
    assert overlay.shape == (224, 224, 3)
    assert overlay.dtype == np.uint8


def test_gradcam_prediction_consistency():
    """Verify that Grad-CAM prediction matches pure model prediction."""
    model = get_model(num_classes=5, pretrained=False)
    model.eval()
    gradcam = GradCAM(model)

    dummy_input = torch.randn(1, 3, 224, 224, requires_grad=True)
    with torch.no_grad():
        pure_out = model(dummy_input)
        pure_pred = int(torch.argmax(pure_out, dim=1).item())

    heatmap, gradcam_pred, _ = gradcam.generate_heatmap(dummy_input)
    assert gradcam_pred == pure_pred

    gradcam.remove_hooks()
