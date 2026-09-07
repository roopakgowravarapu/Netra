"""Robustness Testing module under controlled image perturbations.
"""

from typing import Dict, List, Tuple, Any
import cv2
import numpy as np
import torch
import torch.nn.functional as F
from torchvision import transforms


def apply_brightness_change(img_bgr: np.ndarray, factor: float = 1.2) -> np.ndarray:
    """Modifies brightness by scaling intensity factor."""
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 2] = np.clip(hsv[:, :, 2] * factor, 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)


def apply_contrast_change(img_bgr: np.ndarray, factor: float = 1.2) -> np.ndarray:
    """Modifies image contrast."""
    mean = np.mean(img_bgr)
    return np.clip((img_bgr.astype(np.float32) - mean) * factor + mean, 0, 255).astype(np.uint8)


def apply_gaussian_blur(img_bgr: np.ndarray, ksize: int = 5) -> np.ndarray:
    """Applies mild Gaussian blur."""
    return cv2.GaussianBlur(img_bgr, (ksize, ksize), 1.5)


def apply_gaussian_noise(img_bgr: np.ndarray, std: float = 15.0) -> np.ndarray:
    """Adds zero-mean Gaussian noise."""
    noise = np.random.normal(0, std, img_bgr.shape)
    return np.clip(img_bgr.astype(np.float32) + noise, 0, 255).astype(np.uint8)


def apply_resolution_downscaling(img_bgr: np.ndarray, target_w: int = 112) -> np.ndarray:
    """Downscales resolution then resizes back up."""
    h, w = img_bgr.shape[:2]
    down = cv2.resize(img_bgr, (target_w, target_w), interpolation=cv2.INTER_AREA)
    return cv2.resize(down, (w, h), interpolation=cv2.INTER_LINEAR)


PERTURBATIONS = {
    "brightness_high": lambda img: apply_brightness_change(img, 1.2),
    "brightness_low": lambda img: apply_brightness_change(img, 0.8),
    "contrast_high": lambda img: apply_contrast_change(img, 1.25),
    "contrast_low": lambda img: apply_contrast_change(img, 0.75),
    "gaussian_blur": lambda img: apply_gaussian_blur(img, 5),
    "gaussian_noise": lambda img: apply_gaussian_noise(img, 15.0),
    "resolution_downscale": lambda img: apply_resolution_downscaling(img, 112),
}


def evaluate_model_robustness(
    model: torch.nn.Module,
    sample_images: List[np.ndarray],
    device: torch.device,
    temperature: float = 1.0,
) -> Dict[str, Any]:
    """Runs perturbation suite on input images and measures prediction stability & confidence change."""
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    results: Dict[str, Any] = {}
    model.eval()

    for p_name, p_fn in PERTURBATIONS.items():
        matched_preds = 0
        total_eval = 0
        original_confs = []
        perturbed_confs = []

        with torch.no_grad():
            for img_bgr in sample_images:
                h, w = img_bgr.shape[:2]
                img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

                # Original forward pass
                t_orig = transform(img_rgb).unsqueeze(0).to(device)
                logits_orig = model(t_orig) / temperature
                probs_orig = F.softmax(logits_orig, dim=1).squeeze(0).cpu().numpy()
                pred_orig = int(np.argmax(probs_orig))
                conf_orig = float(probs_orig[pred_orig])

                # Perturbed forward pass
                img_pert_bgr = p_fn(img_bgr)
                img_pert_rgb = cv2.cvtColor(img_pert_bgr, cv2.COLOR_BGR2RGB)
                t_pert = transform(img_pert_rgb).unsqueeze(0).to(device)
                logits_pert = model(t_pert) / temperature
                probs_pert = F.softmax(logits_pert, dim=1).squeeze(0).cpu().numpy()
                pred_pert = int(np.argmax(probs_pert))
                conf_pert = float(probs_pert[pred_pert])

                total_eval += 1
                if pred_pert == pred_orig:
                    matched_preds += 1

                original_confs.append(conf_orig)
                perturbed_confs.append(conf_pert)

        stability = float(matched_preds / max(1, total_eval))
        avg_orig_conf = float(np.mean(original_confs)) if original_confs else 0.0
        avg_pert_conf = float(np.mean(perturbed_confs)) if perturbed_confs else 0.0

        results[p_name] = {
            "prediction_stability": round(stability, 4),
            "original_mean_confidence": round(avg_orig_conf, 4),
            "perturbed_mean_confidence": round(avg_pert_conf, 4),
            "confidence_delta": round(avg_pert_conf - avg_orig_conf, 4),
        }

    return results
