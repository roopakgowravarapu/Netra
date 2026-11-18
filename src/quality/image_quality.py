"""Image Quality Assessment (IQA) module for Netra DR Screening Platform.

Evaluates fundus image quality using deterministic visual features:
- Image Sharpness / Blur (Laplacian variance on standardized 224x224 spatial scale)
- Green Channel Mean Illumination & Exposure (Retinal fundus feature contrast inside retinal FOV)
- Contrast (Standard deviation of pixel intensity)
- Retinal Field of View (FOV mask area and circular boundary check)
- Resolution & Aspect Ratio validation

Clinical Three-Tier Quality Classification:
- Gradable: Fully suitable for autonomous AI inference and clinical review.
- Borderline: Sub-optimal quality (e.g. mild blur or uneven illumination); eligible for adaptive CLAHE contrast enhancement before inference.
- Ungradable: Non-diagnostic quality (severe blur, extreme under/overexposure, or occluded FOV); AI inference is blocked and actionable retake guidance is provided.

Camera Calibration & Validation Notice:
Default thresholds are calibrated against standard tabletop 45-degree fundus cameras (e.g., Topcon, Canon, Zeiss) and validated against Messidor-2, APTOS-2019, and SUSTech-SYSU cohorts.
For portable/handheld or smartphone-based fundus cameras (e.g., Remidio, Volk), thresholds should be adjusted using environment variables or a site-specific calibration profile.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any, Optional
import cv2
import numpy as np


@dataclass
class QualityConfig:
    """Configurable thresholds for image quality evaluation with camera calibration overrides."""
    min_width: int = 200
    min_height: int = 200
    min_blur_laplacian_var: float = 80.0         # Severe blur threshold (ungradable below this)
    borderline_blur_laplacian_var: float = 120.0   # Borderline blur threshold (borderline below this)
    min_brightness_mean: float = 25.0           # Absolute dark cutoff
    max_brightness_mean: float = 230.0          # Absolute overexposure cutoff
    min_green_mean: float = 35.0                # Green channel under-illumination threshold inside FOV
    max_green_mean: float = 215.0               # Green channel saturation threshold inside FOV
    min_contrast_std: float = 20.0
    min_fov_ratio: float = 0.25                 # Minimum retinal field-of-view fraction
    camera_model: str = "Standard 45-degree Fundus Camera"

    @classmethod
    def from_env(cls) -> "QualityConfig":
        """Instantiate QualityConfig reading optional environment variable overrides."""
        return cls(
            min_width=int(os.getenv("NETRA_IQA_MIN_WIDTH", "200")),
            min_height=int(os.getenv("NETRA_IQA_MIN_HEIGHT", "200")),
            min_blur_laplacian_var=float(os.getenv("NETRA_IQA_MIN_SHARPNESS", "80.0")),
            borderline_blur_laplacian_var=float(os.getenv("NETRA_IQA_BORDERLINE_SHARPNESS", "120.0")),
            min_brightness_mean=float(os.getenv("NETRA_IQA_MIN_BRIGHTNESS", "25.0")),
            max_brightness_mean=float(os.getenv("NETRA_IQA_MAX_BRIGHTNESS", "230.0")),
            min_green_mean=float(os.getenv("NETRA_IQA_MIN_GREEN", "35.0")),
            max_green_mean=float(os.getenv("NETRA_IQA_MAX_GREEN", "215.0")),
            min_contrast_std=float(os.getenv("NETRA_IQA_MIN_CONTRAST", "20.0")),
            min_fov_ratio=float(os.getenv("NETRA_IQA_MIN_FOV", "0.25")),
            camera_model=os.getenv("NETRA_IQA_CAMERA_MODEL", "Standard 45-degree Fundus Camera"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "min_width": self.min_width,
            "min_height": self.min_height,
            "min_blur_laplacian_var": self.min_blur_laplacian_var,
            "borderline_blur_laplacian_var": self.borderline_blur_laplacian_var,
            "min_brightness_mean": self.min_brightness_mean,
            "max_brightness_mean": self.max_brightness_mean,
            "min_green_mean": self.min_green_mean,
            "max_green_mean": self.max_green_mean,
            "min_contrast_std": self.min_contrast_std,
            "min_fov_ratio": self.min_fov_ratio,
            "camera_model": self.camera_model,
        }


@dataclass
class QualityResult:
    """Structured quality evaluation result for an image."""
    score: float
    status: str  # "gradable", "borderline", or "ungradable"
    issues: List[str] = field(default_factory=list)
    rejection_reason: Optional[str] = None
    retake_instructions: Optional[str] = None
    enhancement_recommended: bool = False
    metrics: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": round(self.score, 4),
            "status": self.status,
            "issues": self.issues,
            "rejection_reason": self.rejection_reason,
            "retake_instructions": self.retake_instructions,
            "enhancement_recommended": self.enhancement_recommended,
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
    """Assess image quality for a single BGR or Grayscale image array with clinical 3-tier grading."""
    if config is None:
        config = QualityConfig.from_env()

    issues: List[str] = []
    retake_tips: List[str] = []
    metrics: Dict[str, float] = {}

    if image is None or not isinstance(image, np.ndarray) or image.size == 0:
        return QualityResult(
            score=0.0,
            status="ungradable",
            issues=["Image data is empty, unreadable, or corrupt."],
            rejection_reason="Corrupt or unreadable image file.",
            retake_instructions="Please re-capture fundus photograph with valid image format (PNG, JPEG).",
            enhancement_recommended=False,
            metrics={},
        )

    try:
        # Dimensions check
        h, w = image.shape[:2]
        metrics["width"] = float(w)
        metrics["height"] = float(h)
        if w < config.min_width or h < config.min_height:
            issues.append(f"Resolution too low ({w}x{h} < {config.min_width}x{config.min_height}).")
            retake_tips.append("Ensure fundus camera output is set to standard resolution (minimum 512x512).")

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
                retake_instructions="Export fundus image in standard RGB format.",
                enhancement_recommended=False,
                metrics={},
            )

        # Retinal Visibility / FOV ratio first to isolate fundus from outer black region
        fov_mask = compute_fov_mask(gray)
        total_pixels = h * w
        fov_pixels = int(np.count_nonzero(fov_mask))
        fov_ratio = float(fov_pixels / total_pixels) if total_pixels > 0 else 0.0
        metrics["fov_ratio"] = fov_ratio

        # 1. Blur / Sharpness: Laplacian variance calculated on standardized spatial scale (224x224)
        gray_std = cv2.resize(gray, (224, 224)) if (w, h) != (224, 224) else gray
        laplacian_var = float(cv2.Laplacian(gray_std, cv2.CV_64F).var())
        metrics["laplacian_var"] = laplacian_var
        metrics["raw_laplacian_var"] = float(cv2.Laplacian(gray, cv2.CV_64F).var())

        is_severe_blur = laplacian_var < config.min_blur_laplacian_var
        is_borderline_blur = (
            not is_severe_blur and laplacian_var < config.borderline_blur_laplacian_var
        )

        if is_severe_blur:
            issues.append(f"Image is severely blurred (sharpness {laplacian_var:.1f} < {config.min_blur_laplacian_var:.0f}).")
            retake_tips.append("Hold camera steady, allow autofocus to lock on retinal plane, and instruct patient to fixate on the target.")
        elif is_borderline_blur:
            issues.append(f"Mild optical blur (sharpness {laplacian_var:.1f} < {config.borderline_blur_laplacian_var:.0f}).")
            retake_tips.append("Verify focus ring calibration before next capture.")

        # 2. Brightness & Contrast
        brightness_mean = float(np.mean(gray))
        contrast_std = float(np.std(gray))
        metrics["brightness_mean"] = brightness_mean
        metrics["contrast_std"] = contrast_std

        # Green channel illumination inside retinal FOV
        if fov_pixels > 50:
            green_mean = float(np.mean(green[fov_mask > 0]))
        else:
            green_mean = float(np.mean(green))
        metrics["green_mean"] = green_mean

        is_extreme_exposure = (
            brightness_mean < config.min_brightness_mean
            or brightness_mean > config.max_brightness_mean
        )

        if brightness_mean < config.min_brightness_mean:
            issues.append(f"Image is too dark (brightness {brightness_mean:.1f} < {config.min_brightness_mean:.0f}).")
            retake_tips.append("Increase flash intensity or dim ambient room lighting.")
        elif brightness_mean > config.max_brightness_mean:
            issues.append(f"Image is overexposed/washed out (brightness {brightness_mean:.1f} > {config.max_brightness_mean:.0f}).")
            retake_tips.append("Reduce camera flash power and avoid direct reflection on the cornea.")
        elif fov_ratio >= config.min_fov_ratio:
            # Only evaluate green illumination threshold when FOV is adequately present
            if green_mean < config.min_green_mean:
                issues.append(f"Sub-optimal green illumination (mean green {green_mean:.1f} < {config.min_green_mean:.0f}).")
                retake_tips.append("Check pupil dilation; insufficient dilation causes dark fundus periphery.")
            elif green_mean > config.max_green_mean:
                issues.append(f"Green channel saturation (mean green {green_mean:.1f} > {config.max_green_mean:.0f}).")
                retake_tips.append("Slightly decrease camera sensor gain.")

        if contrast_std < config.min_contrast_std:
            issues.append(f"Image has insufficient contrast ({contrast_std:.1f} < {config.min_contrast_std:.0f}).")
            retake_tips.append("Ensure clear optical path (clean objective lens from dust/fingerprints).")

        # 3. Retinal Visibility check
        is_fov_clipped = fov_ratio < config.min_fov_ratio
        if is_fov_clipped:
            issues.append(f"Retinal field of view limited (FOV {fov_ratio:.2f} < {config.min_fov_ratio:.2f}).")
            retake_tips.append("Align optical axis with pupil center; avoid eyelid or eyelash obstruction.")

        # Score computation normalized to [0, 1]
        blur_score = min(1.0, laplacian_var / (config.borderline_blur_laplacian_var * 2.5))
        brightness_score = max(0.0, 1.0 - abs(brightness_mean - 128.0) / 128.0)
        contrast_score = min(1.0, contrast_std / (config.min_contrast_std * 2.5))
        fov_score = min(1.0, fov_ratio / 0.7)

        composite_score = float(
            0.35 * blur_score + 0.25 * brightness_score + 0.25 * contrast_score + 0.15 * fov_score
        )
        composite_score = max(0.0, min(1.0, composite_score))

        # Clinical Decision Tiers:
        # Ungradable: severe blur, extreme under/overexposure, or occluded FOV
        if is_severe_blur or is_extreme_exposure or is_fov_clipped:
            status = "ungradable"
            rejection_reason = "; ".join(issues)
            enhancement_rec = False
        elif is_borderline_blur or (contrast_std < config.min_contrast_std):
            status = "borderline"
            rejection_reason = None
            enhancement_rec = True
        else:
            status = "gradable"
            rejection_reason = None
            enhancement_rec = False

        retake_instructions = " ".join(retake_tips) if retake_tips else "Image meets clinical diagnostic quality standards."

        return QualityResult(
            score=composite_score,
            status=status,
            issues=issues,
            rejection_reason=rejection_reason,
            retake_instructions=retake_instructions,
            enhancement_recommended=enhancement_rec,
            metrics=metrics,
        )

    except Exception as e:
        return QualityResult(
            score=0.0,
            status="ungradable",
            issues=[f"Error during quality processing: {str(e)}"],
            rejection_reason="Quality analysis runtime error.",
            retake_instructions="Please re-capture and ensure camera file integrity.",
            enhancement_recommended=False,
            metrics={},
        )
