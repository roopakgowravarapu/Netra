"""Confidence Calibration & Uncertainty Estimation module for Netra DR Classifier.

Fits Temperature Scaling post-hoc calibration on validation set logits.
Computes Expected Calibration Error (ECE) and Shannon Entropy uncertainty.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Tuple, Optional, Any, List

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))


def compute_ece(
    probs: np.ndarray, labels: np.ndarray, n_bins: int = 10
) -> Tuple[float, float, Dict[str, Any]]:
    """
    Computes Expected Calibration Error (ECE) and Maximum Calibration Error (MCE).
    """
    confidences = np.max(probs, axis=1)
    predictions = np.argmax(probs, axis=1)
    accuracies = (predictions == labels).astype(float)

    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    mce = 0.0
    n_samples = len(labels)

    bin_data = []

    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]

        in_bin = (confidences > bin_lower) & (confidences <= bin_upper)
        prop_in_bin = np.mean(in_bin)

        if prop_in_bin > 0:
            accuracy_in_bin = np.mean(accuracies[in_bin])
            avg_confidence_in_bin = np.mean(confidences[in_bin])
            difference = abs(accuracy_in_bin - avg_confidence_in_bin)

            ece += (np.sum(in_bin) / n_samples) * difference
            mce = max(mce, difference)

            bin_data.append({
                "bin_lower": float(bin_lower),
                "bin_upper": float(bin_upper),
                "accuracy": float(accuracy_in_bin),
                "confidence": float(avg_confidence_in_bin),
                "count": int(np.sum(in_bin)),
            })

    return float(ece), float(mce), {"bins": bin_data}


class TemperatureScaler(nn.Module):
    """
    Learns a single scalar Temperature T > 0 to scale logits prior to softmax.
    Strictly fit on validation set logits.
    """

    def __init__(self, initial_temperature: float = 1.5):
        super().__init__()
        self.temperature = nn.Parameter(torch.tensor([initial_temperature], dtype=torch.float32))

    def forward(self, logits: torch.Tensor) -> torch.Tensor:
        # Scale logits by T
        return logits / self.temperature

    def fit(self, val_logits: torch.Tensor, val_labels: torch.Tensor, max_iter: int = 50):
        """Fit optimal temperature on validation set using Negative Log Likelihood (NLL)."""
        self.to(val_logits.device)
        optimizer = torch.optim.LBFGS([self.temperature], lr=0.01, max_iter=max_iter)
        criterion = nn.CrossEntropyLoss()

        def eval_loss():
            optimizer.zero_grad()
            scaled_logits = self.forward(val_logits)
            loss = criterion(scaled_logits, val_labels)
            loss.backward()
            return loss

        optimizer.step(eval_loss)
        # Ensure temperature remains strictly positive (> 0.05)
        with torch.no_grad():
            self.temperature.clamp_(min=0.05)

    def get_temperature(self) -> float:
        return float(self.temperature.item())


def compute_uncertainty(probs: np.ndarray) -> Dict[str, float]:
    """
    Computes Shannon Entropy and Margin of Confidence uncertainty metrics.
    """
    eps = 1e-12
    probs_clipped = np.clip(probs, eps, 1.0)
    entropy = -np.sum(probs_clipped * np.log(probs_clipped))
    max_entropy = np.log(len(probs))
    normalized_entropy = float(entropy / max_entropy)

    sorted_probs = np.sort(probs)[::-1]
    margin = float(sorted_probs[0] - sorted_probs[1]) if len(sorted_probs) > 1 else float(sorted_probs[0])

    return {
        "entropy": float(entropy),
        "normalized_entropy": normalized_entropy,
        "margin": margin,
        "uncertainty_score": float(1.0 - margin),
    }
