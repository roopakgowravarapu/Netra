"""
Netra Model Definition Module
Transfer Learning Architecture based on EfficientNet-B0 for 5-Class Diabetic Retinopathy Classification.
"""

from typing import Tuple

import torch
import torch.nn as nn
from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights


def get_model(num_classes: int = 5, pretrained: bool = True) -> nn.Module:
    """
    Instantiates EfficientNet-B0 transfer learning architecture.
    Replaces the final classification layer with 5-class logits output.
    """
    weights = EfficientNet_B0_Weights.DEFAULT if pretrained else None
    model = efficientnet_b0(weights=weights)

    # Replace final classification linear layer (in_features=1280)
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, num_classes)

    return model


def count_parameters(model: nn.Module) -> Tuple[int, int]:
    """Returns total parameter count and trainable parameter count."""
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return total_params, trainable_params
