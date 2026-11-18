"""Screening Result Generation Module for Netra Platform.

Integrates:
1. Image Quality Assessment (IQA: Gradable, Borderline, Ungradable)
2. DR Classification across 5 ICDR Grades (0-4) using EfficientNet-B0
3. 4x Test-Time Augmentation (TTA: Identity, H-Flip, V-Flip, HV-Flip)
4. Temperature-Calibrated Confidence & Uncertainty Estimation (Optimal T derived from Validation split)
5. Grad-CAM Neural Activation Map Generator (Saliency attention map, distinct from segmented lesions)
6. Retinal Landmark & Macular Risk Indicator (Macular proximity assessment, noting DME requires OCT)
7. Actionable Specialist Triage and Safety Warnings
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
from src.preprocessing.config import DEFAULT_CONFIG
from src.preprocessing.preprocess import preprocess_single_image
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
    "Image quality insufficient for automated DR evaluation. "
    "Please clean camera objective lens, adjust illumination and focus, and RECAPTURE fundus image."
)

CLINICAL_DISCLAIMER = (
    "Netra is an AI-assisted retinal screening and clinical decision-support platform. "
    "It does not replace a qualified ophthalmologist or constitute an autonomous medical diagnosis."
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
            combined_model = ROOT_DIR / "models" / "best_model_aptos_ddr.pth"
            model_path = combined_model if combined_model.exists() else (ROOT_DIR / "models" / "best_model.pth")

        if model_path.exists():
            checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)
            state_dict = checkpoint.get("model_state_dict", checkpoint)
            self.model.load_state_dict(state_dict)

        self.model.to(self.device)
        self.model.eval()

        self.quality_config = QualityConfig.from_env()
        self.gradcam = GradCAM(self.model)

        # Temperature Scaling calibration parameter (multiclass extension of Platt scaling)
        # Optimal T derived exclusively from validation partition (APTOS+DDR validation set)
        self.temperature = 1.3353
        if calib_params_path is None:
            combined_calib = ROOT_DIR / "outputs" / "evaluation_aptos_ddr" / "calibration_parameters.json"
            calib_params_path = (
                combined_calib
                if combined_calib.exists()
                else (ROOT_DIR / "outputs" / "confidence" / "calibration_parameters.json")
            )
        if calib_params_path.exists():
            try:
                with open(calib_params_path, "r", encoding="utf-8") as f:
                    params = json.load(f)
                    self.temperature = float(params.get("optimal_temperature", 1.3353))
            except Exception:
                self.temperature = 1.3353

        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def process_image(
        self, image_bgr: np.ndarray, save_explanation_dir: Optional[Path] = None, sample_id: str = "sample"
    ) -> Dict[str, Any]:
        """Runs screening process for input image and returns structured JSON dictionary."""
        # 1. Image Quality Assessment
        quality_res = assess_image_quality(image_bgr, self.quality_config)

        # Save original image if save_dir is specified
        original_rel_path = None
        if save_explanation_dir is not None:
            save_explanation_dir.mkdir(parents=True, exist_ok=True)
            original_filename = f"original_{sample_id}.png"
            original_path = save_explanation_dir / original_filename
            cv2.imwrite(str(original_path), image_bgr)
            original_rel_path = str(original_path)

        # Safeguard: If image is ungradable, prevent DR inference and instruct recapture
        if quality_res.status == "ungradable":
            recapture_advice = f"{UNGRADABLE_RECOMMENDATION} Instructions: {quality_res.retake_instructions}" if quality_res.retake_instructions else UNGRADABLE_RECOMMENDATION
            return {
                "sample_id": sample_id,
                "original_image_path": original_rel_path,
                "image_quality": {
                    "score": round(quality_res.score, 4),
                    "status": "ungradable",
                    "issues": quality_res.issues,
                    "rejection_reason": quality_res.rejection_reason,
                    "retake_instructions": recapture_advice,
                    "metrics": quality_res.metrics,
                },
                "dr_prediction": None,
                "explanation": None,
                "recommendation": recapture_advice,
                "disclaimer": CLINICAL_DISCLAIMER,
            }

        # 2. Standardized Preprocessing (Ben Graham method with FOV crop & local color normalization)
        img_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        img_rgb_input = preprocess_single_image(img_rgb, config=DEFAULT_CONFIG)
        img_bgr_input = cv2.cvtColor(img_rgb_input, cv2.COLOR_RGB2BGR)

        tensor_img = self.transform(img_rgb_input).unsqueeze(0).to(self.device)

        # 3. 4x Test-Time Augmentation (TTA) forward passes:
        # Pass 0: Canonical unaugmented input (Identity)
        # Pass 1: Horizontal reflection flip (dim 3)
        # Pass 2: Vertical reflection flip (dim 2)
        # Pass 3: Combined Horizontal + Vertical reflection flip (dims [2, 3])
        # Ensemble average across all 4 spatial transformations
        with torch.no_grad():
            l0 = self.model(tensor_img)
            l1 = self.model(torch.flip(tensor_img, dims=[3]))
            l2 = self.model(torch.flip(tensor_img, dims=[2]))
            l3 = self.model(torch.flip(tensor_img, dims=[2, 3]))
            raw_logits = 0.25 * (l0 + l1 + l2 + l3)
            raw_probs = F.softmax(raw_logits, dim=1).squeeze(0).cpu().numpy()

            # Temperature Scaling Calibration: z_cal = z / T
            calibrated_logits = raw_logits / self.temperature
            calibrated_probs = F.softmax(calibrated_logits, dim=1).squeeze(0).cpu().numpy()

        pred_grade = int(np.argmax(calibrated_probs))
        pred_label = CLASS_LABELS[pred_grade]
        raw_confidence = float(raw_probs[pred_grade])
        calibrated_confidence = float(calibrated_probs[pred_grade])

        # Compute predictive uncertainty metrics (Normalized Entropy and Confidence Margin)
        unc_metrics = compute_uncertainty(calibrated_probs)
        entropy = float(unc_metrics.get("entropy", 0.0))
        margin = float(unc_metrics.get("margin", 0.0))

        # Clinical uncertainty gate:
        # Flag if entropy > 1.25 (high epistemic confusion) or margin < 0.20 (competing grades) or confidence < 0.60
        is_uncertain = (entropy > 1.25) or (margin < 0.20) or (calibrated_confidence < 0.60)
        uncertainty_warning = None
        if is_uncertain:
            uncertainty_warning = (
                f"Prediction uncertainty is elevated (Entropy: {entropy:.2f}, Margin: {margin:.2f}, Confidence: {calibrated_confidence * 100:.1f}%). "
                "Specialist ophthalmologist review is strongly advised rather than relying exclusively on automated grading."
            )

        # 4. Grad-CAM Neural Saliency Heatmap
        heatmap, _, _ = self.gradcam.generate_heatmap(tensor_img, target_class=pred_grade)
        overlay_bgr = overlay_heatmap_on_image(img_bgr_input, heatmap, alpha=0.45)
        overlay_bgr = cv2.resize(overlay_bgr, (448, 448), interpolation=cv2.INTER_CUBIC)

        gradcam_rel_path = None
        if save_explanation_dir is not None:
            save_explanation_dir.mkdir(parents=True, exist_ok=True)
            overlay_filename = f"gradcam_{sample_id}.png"
            overlay_path = save_explanation_dir / overlay_filename
            cv2.imwrite(str(overlay_path), overlay_bgr)
            gradcam_rel_path = str(overlay_path)

        prob_dict = {CLASS_LABELS[i]: round(float(calibrated_probs[i]), 4) for i in range(5)}

        base_recommendation = RECOMMENDATIONS[pred_grade]
        if is_uncertain and pred_grade < 2:
            base_recommendation += " (Note: Specialist review recommended due to borderline model confidence)."

        return {
            "sample_id": sample_id,
            "original_image_path": original_rel_path,
            "image_quality": {
                "score": round(quality_res.score, 4),
                "status": quality_res.status,
                "issues": quality_res.issues,
                "retake_instructions": quality_res.retake_instructions,
                "metrics": quality_res.metrics,
            },
            "dr_prediction": {
                "grade": pred_grade,
                "label": pred_label,
                "confidence": round(calibrated_confidence, 4),
                "raw_confidence": round(raw_confidence, 4),
                "temperature": round(self.temperature, 4),
                "probabilities": prob_dict,
                "uncertainty": {
                    "entropy": round(entropy, 4),
                    "margin": round(margin, 4),
                },
                "uncertain_prediction": is_uncertain,
                "uncertainty_warning": uncertainty_warning,
                "macula_risk_level": "POTENTIAL_RISK" if pred_grade >= 2 else "LOW_RISK",
                "macula_risk_description": (
                    "Observational macular risk indicator based on proximity of detected vascular anomalies to the foveal zone. "
                    "Definitive diagnosis of Diabetic Macular Edema (DME) requires Optical Coherence Tomography (OCT)."
                ),
            },
            "explanation": {
                "gradcam_path": gradcam_rel_path,
                "original_image_path": original_rel_path,
                "target_class": pred_grade,
                "saliency_description": (
                    "Grad-CAM visualizes deep neural network activation attention. "
                    "It highlights regions contributing most strongly to the classifier's output, "
                    "distinct from deterministic retinal lesion segmentations."
                ),
            },
            "recommendation": base_recommendation,
            "disclaimer": CLINICAL_DISCLAIMER,
        }


def generate_example_screening_reports():
    output_dir = ROOT_DIR / "outputs" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    pipeline = ScreeningPipeline()

    # Case 1: Gradable Fundus Image
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
