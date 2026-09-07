"""Image Quality Assessment (IQA) module for Netra DR Screening Platform.

Evaluates fundus image quality using deterministic visual features:
- Sharpness / Blur (Laplacian variance)
- Brightness (Mean pixel intensity)
- Contrast (Standard deviation of pixel intensity)
- Retinal Visibility / Field of View (FOV mask area and contrast)
- Resolution / Aspect Ratio validation
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any, Optional
import cv2
import numpy as np


@dataclass
class QualityConfig:
    """Configurable thresholds for image quality evaluation."""
    min_width: int = 200
    min_height: int = 200
    min_blur_laplacian_var: float = 100.0
    min_brightness_mean: float = 25.0
    max_brightness_mean: float = 230.0
    min_contrast_std: float = 20.0
    min_fov_ratio: float = 0.25

    def to_dict(self) -> Dict[str, Any]:
        return {
            "min_width": self.min_width,
            "min_height": self.min_height,
            "min_blur_laplacian_var": self.min_blur_laplacian_var,
            "min_brightness_mean": self.min_brightness_mean,
            "max_brightness_mean": self.max_brightness_mean,
            "min_contrast_std": self.min_contrast_std,
            "min_fov_ratio": self.min_fov_ratio,
        }


@dataclass
class QualityResult:
    """Structured quality evaluation result for an image."""
    score: float
    status: str  # "gradable" or "ungradable"
    issues: List[str] = field(default_factory=list)
    rejection_reason: Optional[str] = None
    metrics: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": round(self.score, 4),
            "status": self.status,
            "issues": self.issues,
            "rejection_reason": self.rejection_reason,
            "metrics": {k: round(v, 4) for k, v in self.metrics.items()},
        }


def compute_fov_mask(gray: np.ndarray) -> np.ndarray:
    """Extract approximate mask of circular retinal region from background."""
    _, mask = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    return mask


def assess_image_quality(
    image: np.ndarray, config: Optional[QualityConfig] = None
) -> QualityResult:
    """Assess image quality for a single BGR or Grayscale image array."""
    if config is None:
        config = QualityConfig()

    issues: List[str] = []
    metrics: Dict[str, float] = {}

    if image is None or not isinstance(image, np.ndarray) or image.size == 0:
        return QualityResult(
            score=0.0,
            status="ungradable",
            issues=["Image data is empty, unreadable, or corrupt."],
            rejection_reason="Corrupt or unreadable image file.",
            metrics={},
        )

    try:
        # Dimensions check
        h, w = image.shape[:2]
        metrics["width"] = float(w)
        metrics["height"] = float(h)
        if w < config.min_width or h < config.min_height:
            issues.append(f"Resolution too low ({w}x{h} < {config.min_width}x{config.min_height}).")

        # Color conversion
        if len(image.shape) == 3 and image.shape[2] == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            green = image[:, :, 1]
        elif len(image.shape) == 2:
            gray = image
            green = image
        else:
            return QualityResult(
                score=0.0,
                status="ungradable",
                issues=["Invalid channel structure."],
                rejection_reason="Unsupported image channel format.",
                metrics={},
            )

        # 1. Blur / Sharpness: Laplacian variance calculated on standardized spatial scale (224x224)
        gray_std = cv2.resize(gray, (224, 224)) if (w, h) != (224, 224) else gray
        laplacian_var = float(cv2.Laplacian(gray_std, cv2.CV_64F).var())
        metrics["laplacian_var"] = laplacian_var
        metrics["raw_laplacian_var"] = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        if laplacian_var < config.min_blur_laplacian_var:
            issues.append(f"Image is severely blurred (sharpness score {laplacian_var:.1f} < {config.min_blur_laplacian_var}).")

        # 2. Brightness & Contrast
        brightness_mean = float(np.mean(gray))
        contrast_std = float(np.std(gray))
        metrics["brightness_mean"] = brightness_mean
        metrics["contrast_std"] = contrast_std

        if brightness_mean < config.min_brightness_mean:
            issues.append(f"Image is too dark (brightness {brightness_mean:.1f} < {config.min_brightness_mean}).")
        elif brightness_mean > config.max_brightness_mean:
            issues.append(f"Image is overexposed/washed out (brightness {brightness_mean:.1f} > {config.max_brightness_mean}).")

        if contrast_std < config.min_contrast_std:
            issues.append(f"Image has insufficient contrast ({contrast_std:.1f} < {config.min_contrast_std}).")

        # 3. Retinal Visibility / FOV ratio
        fov_mask = compute_fov_mask(gray)
        total_pixels = h * w
        fov_pixels = int(np.count_nonzero(fov_mask))
        fov_ratio = float(fov_pixels / total_pixels) if total_pixels > 0 else 0.0
        metrics["fov_ratio"] = fov_ratio

        if fov_ratio < config.min_fov_ratio:
            issues.append(f"Retinal field of view limited/obscured (FOV coverage {fov_ratio:.2f} < {config.min_fov_ratio}).")

        # Score computation normalized to [0, 1]
        blur_score = min(1.0, laplacian_var / (config.min_blur_laplacian_var * 3.0))
        brightness_score = max(0.0, 1.0 - abs(brightness_mean - 128.0) / 128.0)
        contrast_score = min(1.0, contrast_std / (config.min_contrast_std * 2.5))
        fov_score = min(1.0, fov_ratio / 0.7)

        composite_score = float(
            0.35 * blur_score + 0.25 * brightness_score + 0.25 * contrast_score + 0.15 * fov_score
        )
        composite_score = max(0.0, min(1.0, composite_score))

        # Overall decision
        status = "ungradable" if len(issues) > 0 else "gradable"
        rejection_reason = "; ".join(issues) if issues else None

        return QualityResult(
            score=composite_score,
            status=status,
            issues=issues,
            rejection_reason=rejection_reason,
            metrics=metrics,
        )

    except Exception as e:
        return QualityResult(
            score=0.0,
            status="ungradable",
            issues=[f"Error during quality processing: {str(e)}"],
            rejection_reason="Quality analysis runtime error.",
            metrics={},
        )
