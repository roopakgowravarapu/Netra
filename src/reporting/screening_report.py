"""Screening Result Generation Module for Netra Platform.

Integrates:
1. Image Quality Assessment (IQA)
2. DR Classification (Level 0-4)
3. Temperature-Calibrated Confidence & Uncertainty
4. Grad-CAM Visual Explanation Generator
5. Automated Specialist Referral Engine
"""

import json
import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
import torch
import torch.nn.functional as F
from torchvision import transforms

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.evaluation.calibration import TemperatureScaler, compute_uncertainty
from src.explainability.gradcam import GradCAM, overlay_heatmap_on_image
from src.quality.image_quality import QualityConfig, QualityResult, assess_image_quality
from src.training.model import get_model

CLASS_LABELS = {
    0: "No DR",
    1: "Mild DR",
    2: "Moderate DR",
    3: "Severe DR",
    4: "Proliferative DR",
}

RECOMMENDATIONS = {
    0: "No Diabetic Retinopathy detected. Routine annual eye screening recommended.",
    1: "Mild Diabetic Retinopathy detected. Schedule follow-up screening in 6-12 months.",
    2: "Moderate Diabetic Retinopathy detected. Referral to Ophthalmologist for evaluation within 4-6 weeks.",
    3: "Severe Diabetic Retinopathy detected. Urgent referral to Retina Specialist within 1-2 weeks.",
    4: "Proliferative Diabetic Retinopathy detected. IMMEDIATE referral to Retina Specialist for urgent treatment.",
}

UNGRADABLE_RECOMMENDATION = (
    "Image quality insufficient for automated DR evaluation. Please clean lens, adjust lighting/focus, and RECAPTURE fundus image."
)


class ScreeningPipeline:
    """End-to-End screening pipeline orchestrator."""

    def __init__(
        self,
        model_path: Optional[Path] = None,
        calib_params_path: Optional[Path] = None,
        device: Optional[torch.device] = None,
    ):
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = device

        self.model = get_model(num_classes=5, pretrained=False)
        if model_path is None:
            model_path = ROOT_DIR / "models" / "best_model.pth"

        if model_path.exists():
            checkpoint = torch.load(model_path, map_location=self.device)
            state_dict = checkpoint.get("model_state_dict", checkpoint)
            self.model.load_state_dict(state_dict)

        self.model.to(self.device)
        self.model.eval()

        self.quality_config = QualityConfig()
        self.gradcam = GradCAM(self.model)

        # Load temperature scaling calibration parameter
        self.temperature = 1.0
        if calib_params_path is None:
            calib_params_path = ROOT_DIR / "outputs" / "confidence" / "calibration_parameters.json"
        if calib_params_path.exists():
            try:
                with open(calib_params_path, "r", encoding="utf-8") as f:
                    params = json.load(f)
                    self.temperature = params.get("optimal_temperature", 1.0)
            except Exception:
                self.temperature = 1.0

        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def process_image(
        self, image_bgr: np.ndarray, save_explanation_dir: Optional[Path] = None, sample_id: str = "sample"
    ) -> Dict[str, Any]:
        """Runs screening process for input image and returns structured JSON dictionary."""
        # 1. Step 7: Image Quality Assessment
        quality_res = assess_image_quality(image_bgr, self.quality_config)

        # Save original image if save_dir is specified
        original_rel_path = None
        if save_explanation_dir is not None:
            save_explanation_dir.mkdir(parents=True, exist_ok=True)
            original_filename = f"original_{sample_id}.png"
            original_path = save_explanation_dir / original_filename
            cv2.imwrite(str(original_path), image_bgr)
            original_rel_path = str(original_path)

        # Safeguard: If image is ungradable, return ungradable report WITHOUT DR diagnosis
        if quality_res.status == "ungradable":
            return {
                "sample_id": sample_id,
                "original_image_path": original_rel_path,
                "image_quality": {
                    "score": round(quality_res.score, 4),
                    "status": "ungradable",
                    "issues": quality_res.issues,
                    "rejection_reason": quality_res.rejection_reason,
                    "metrics": quality_res.metrics,
                },
                "dr_prediction": None,
                "explanation": None,
                "recommendation": UNGRADABLE_RECOMMENDATION,
                "disclaimer": "Netra is an AI-assisted screening tool. Output is not a definitive medical diagnosis.",
            }

        # 2. Step 8 & 9: Model inference, temperature scaling, & Grad-CAM
        h, w = image_bgr.shape[:2]
        img_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

        # Resize to model standard input dimensions (224x224) if needed
        if (w, h) != (224, 224):
            img_rgb_input = cv2.resize(img_rgb, (224, 224))
            img_bgr_input = cv2.resize(image_bgr, (224, 224))
        else:
            img_rgb_input = img_rgb
            img_bgr_input = image_bgr

        tensor_img = self.transform(img_rgb_input).unsqueeze(0).to(self.device)

        # Logits & Temperature Scaled Calibrated Softmax
        with torch.no_grad():
            raw_logits = self.model(tensor_img)
            calibrated_logits = raw_logits / self.temperature
            calibrated_probs = F.softmax(calibrated_logits, dim=1).squeeze(0).cpu().numpy()

        pred_grade = int(np.argmax(calibrated_probs))
        pred_label = CLASS_LABELS[pred_grade]
        calibrated_confidence = float(calibrated_probs[pred_grade])

        # Compute uncertainty metrics
        unc_metrics = compute_uncertainty(calibrated_probs)

        # Grad-CAM heatmap & overlay
        heatmap, _, _ = self.gradcam.generate_heatmap(tensor_img, target_class=pred_grade)
        overlay_bgr = overlay_heatmap_on_image(img_bgr_input, heatmap)

        gradcam_rel_path = None
        if save_explanation_dir is not None:
            save_explanation_dir.mkdir(parents=True, exist_ok=True)
            overlay_filename = f"gradcam_{sample_id}.png"
            overlay_path = save_explanation_dir / overlay_filename
            cv2.imwrite(str(overlay_path), overlay_bgr)
            gradcam_rel_path = str(overlay_path)

        prob_dict = {CLASS_LABELS[i]: round(float(calibrated_probs[i]), 4) for i in range(5)}

        return {
            "sample_id": sample_id,
            "original_image_path": original_rel_path,
            "image_quality": {
                "score": round(quality_res.score, 4),
                "status": "gradable",
                "issues": [],
                "metrics": quality_res.metrics,
            },
            "dr_prediction": {
                "grade": pred_grade,
                "label": pred_label,
                "confidence": round(calibrated_confidence, 4),
                "probabilities": prob_dict,
                "uncertainty": {
                    "entropy": round(unc_metrics["entropy"], 4),
                    "margin": round(unc_metrics["margin"], 4),
                },
            },
            "explanation": {
                "gradcam_path": gradcam_rel_path,
                "original_image_path": original_rel_path,
                "target_class": pred_grade,
            },
            "recommendation": RECOMMENDATIONS[pred_grade],
            "disclaimer": "Netra is an AI-assisted screening tool. Output is not a definitive medical diagnosis.",
        }


def generate_example_screening_reports():
    output_dir = ROOT_DIR / "outputs" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    pipeline = ScreeningPipeline()

    # Case 1: Gradable Good Fundus Image
    good_img = np.zeros((300, 300, 3), dtype=np.uint8)
    cv2.circle(good_img, (150, 150), 120, (30, 70, 200), -1)
    cv2.line(good_img, (50, 150), (250, 150), (10, 200, 220), 2)
    report_good = pipeline.process_image(good_img, save_explanation_dir=output_dir, sample_id="good_sample")

    with open(output_dir / "sample_report_gradable.json", "w", encoding="utf-8") as f:
        json.dump(report_good, f, indent=2)

    # Case 2: Ungradable Dark/Blurry Image
    bad_img = np.zeros((300, 300, 3), dtype=np.uint8)
    report_bad = pipeline.process_image(bad_img, save_explanation_dir=output_dir, sample_id="ungradable_sample")

    with open(output_dir / "sample_report_ungradable.json", "w", encoding="utf-8") as f:
        json.dump(report_bad, f, indent=2)

    print("Sample screening reports generated successfully.")


if __name__ == "__main__":
    generate_example_screening_reports()
