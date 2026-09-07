"""Grad-CAM Explainability Module for Netra DR Classifier.

Provides class activation mapping for EfficientNet-B0 PyTorch models.
Automatically locates the target convolutional layer and generates heatmaps & overlays.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Tuple, Optional, Any, List

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.training.model import get_model


class GradCAM:
    """Grad-CAM generator for PyTorch convolutional classification models."""

    def __init__(self, model: nn.Module, target_layer: Optional[nn.Module] = None):
        self.model = model
        self.model.eval()
        self.target_layer = target_layer if target_layer is not None else self._find_target_layer()

        self.activations: Optional[torch.Tensor] = None
        self.gradients: Optional[torch.Tensor] = None

        self.handles = []
        self._register_hooks()

    def _find_target_layer(self) -> nn.Module:
        """Automatically identify the final convolutional layer in the backbone."""
        # For torchvision efficientnet_b0, features is a Sequential block
        if hasattr(self.model, "features"):
            target = self.model.features[-1]
            return target

        # Fallback: search backwards for the last nn.Conv2d module
        last_conv = None
        for module in self.model.modules():
            if isinstance(module, nn.Conv2d):
                last_conv = module
        if last_conv is not None:
            return last_conv

        raise ValueError("Could not automatically locate a Conv2d layer in the model.")

    def _register_hooks(self):
        def forward_hook(module, input, output):
            self.activations = output.detach()

        def backward_hook(module, grad_input, grad_output):
            self.gradients = grad_output[0].detach()

        h1 = self.target_layer.register_forward_hook(forward_hook)
        h2 = self.target_layer.register_full_backward_hook(backward_hook)
        self.handles.extend([h1, h2])

    def generate_heatmap(
        self, input_tensor: torch.Tensor, target_class: Optional[int] = None
    ) -> Tuple[np.ndarray, int, List[float]]:
        """
        Generate Grad-CAM heatmap for a single preprocessed input tensor (1, C, H, W).
        Returns: (heatmap [H, W], predicted_class, class_probabilities)
        """
        self.model.zero_grad()

        # Forward pass
        output = self.model(input_tensor)
        probs = F.softmax(output, dim=1).squeeze(0).tolist()
        pred_class = int(torch.argmax(output, dim=1).item())

        if target_class is None:
            target_class = pred_class

        target_score = output[0, target_class]
        target_score.backward()

        if self.gradients is None or self.activations is None:
            raise RuntimeError("Grad-CAM hooks failed to capture gradients or activations.")

        # Compute importance weights via global average pooling of gradients
        weights = torch.mean(self.gradients, dim=[2, 3], keepdim=True)
        cam = torch.sum(weights * self.activations, dim=1, keepdim=True)
        cam = F.relu(cam)

        # Normalize cam to [0, 1]
        cam = cam.squeeze().cpu().numpy()
        if np.max(cam) != np.min(cam):
            cam = (cam - np.min(cam)) / (np.max(cam) - np.min(cam))
        else:
            cam = np.zeros_like(cam)

        # Resize to input tensor spatial dimensions
        h, w = input_tensor.shape[2:]
        heatmap = cv2.resize(cam, (w, h))

        return heatmap, pred_class, probs

    def remove_hooks(self):
        for h in self.handles:
            h.remove()


def overlay_heatmap_on_image(
    original_img_bgr: np.ndarray, heatmap: np.ndarray, alpha: float = 0.5
) -> np.ndarray:
    """Overlays Grad-CAM heatmap onto the original BGR image."""
    h, w = original_img_bgr.shape[:2]
    heatmap_resized = cv2.resize(heatmap, (w, h))
    heatmap_uint8 = np.uint8(255 * heatmap_resized)
    heatmap_colored = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)

    overlay = cv2.addWeighted(original_img_bgr, 1.0 - alpha, heatmap_colored, alpha, 0)
    return overlay
