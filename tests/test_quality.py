"""Unit tests for Image Quality Assessment (IQA) module."""

import sys
from pathlib import Path
import cv2
import numpy as np
import pytest

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.quality.image_quality import QualityConfig, assess_image_quality


def create_synthetic_fundus(
    blur: bool = False,
    dark: bool = False,
    overexposed: bool = False,
    low_res: bool = False,
) -> np.ndarray:
    """Helper to synthesize a fundus-like image for testing."""
    if low_res:
        shape = (100, 100, 3)
    else:
        shape = (300, 300, 3)

    img = np.zeros(shape, dtype=np.uint8)

    if not low_res:
        # Draw circular retina region
        center = (150, 150)
        radius = 120
        cv2.circle(img, center, radius, (20, 60, 180), -1)  # Reddish fundus color

        # Add vessel-like textures for high sharpness/contrast
        for r in range(30, 110, 15):
            cv2.circle(img, center, r, (5, 20, 90), 2)
        cv2.line(img, (50, 150), (250, 150), (10, 200, 220), 2)

    if dark:
        img = (img * 0.1).astype(np.uint8)

    if overexposed:
        img = np.clip(img.astype(np.int16) + 220, 0, 255).astype(np.uint8)

    if blur:
        img = cv2.GaussianBlur(img, (25, 25), 10)

    return img


def test_valid_image_quality():
    """Verify that a high quality synthetic image passes as gradable."""
    img = create_synthetic_fundus()
    res = assess_image_quality(img)
    assert res.status == "gradable"
    assert res.score > 0.4
    assert len(res.issues) == 0
    assert res.rejection_reason is None


def test_blurry_image_quality():
    """Verify that severe blur triggers an ungradable status."""
    img = create_synthetic_fundus(blur=True)
    res = assess_image_quality(img)
    assert res.status == "ungradable"
    assert any("blurred" in issue.lower() for issue in res.issues)


def test_dark_image_quality():
    """Verify that dark image triggers an ungradable status."""
    img = create_synthetic_fundus(dark=True)
    res = assess_image_quality(img)
    assert res.status == "ungradable"
    assert any("dark" in issue.lower() for issue in res.issues)


def test_overexposed_image_quality():
    """Verify that overexposed image triggers ungradable status."""
    img = create_synthetic_fundus(overexposed=True)
    res = assess_image_quality(img)
    assert res.status == "ungradable"
    assert any("overexposed" in issue.lower() for issue in res.issues)


def test_low_resolution_image():
    """Verify low resolution input produces ungradable status."""
    img = create_synthetic_fundus(low_res=True)
    res = assess_image_quality(img)
    assert res.status == "ungradable"
    assert any("resolution" in issue.lower() for issue in res.issues)


def test_corrupt_or_empty_image():
    """Verify robust handling for empty or None inputs."""
    res_none = assess_image_quality(None)
    assert res_none.status == "ungradable"
    assert res_none.score == 0.0

    res_empty = assess_image_quality(np.array([]))
    assert res_empty.status == "ungradable"
    assert res_empty.score == 0.0
