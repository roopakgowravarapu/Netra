"""Unit tests for Confidence Calibration & Uncertainty Estimation module."""

import sys
from pathlib import Path
import numpy as np
import torch
import pytest

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.evaluation.calibration import compute_ece, TemperatureScaler, compute_uncertainty


def test_ece_computation():
    """Verify ECE and MCE metrics calculation."""
    probs = np.array([
        [0.8, 0.1, 0.1, 0.0, 0.0],
        [0.2, 0.7, 0.1, 0.0, 0.0],
        [0.1, 0.2, 0.6, 0.1, 0.0],
    ])
    labels = np.array([0, 1, 2])

    ece, mce, bin_data = compute_ece(probs, labels, n_bins=5)
    assert 0.0 <= ece <= 1.0
    assert 0.0 <= mce <= 1.0
    assert "bins" in bin_data


def test_temperature_scaling_fitting():
    """Verify that TemperatureScaler fits strictly on input logits."""
    scaler = TemperatureScaler(initial_temperature=1.0)
    val_logits = torch.tensor([
        [3.0, 1.0, 0.2, 0.1, 0.0],
        [0.5, 4.0, 0.5, 0.2, 0.1],
        [0.1, 0.3, 3.5, 0.2, 0.1],
    ], dtype=torch.float32)
    val_labels = torch.tensor([0, 1, 2], dtype=torch.long)

    scaler.fit(val_logits, val_labels)
    t_val = scaler.get_temperature()

    assert t_val > 0.0
    assert not np.isnan(t_val)
    assert not np.isinf(t_val)


def test_uncertainty_metrics():
    """Verify calculation of Shannon entropy and confidence margin."""
    probs = np.array([0.9, 0.05, 0.03, 0.01, 0.01])
    unc = compute_uncertainty(probs)

    assert "entropy" in unc
    assert "margin" in unc
    assert pytest.approx(unc["margin"], 0.01) == 0.85
    assert 0.0 <= unc["normalized_entropy"] <= 1.0
