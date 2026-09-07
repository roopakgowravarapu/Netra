"""
Netra Training Configuration Module
Defines hyperparameters for training the baseline EfficientNet-B0 Diabetic Retinopathy classifier.
"""

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Tuple, Dict, Any


@dataclass
class TrainingConfig:
    # Model Architecture
    model_name: str = "efficientnet_b0"
    num_classes: int = 5
    pretrained: bool = True
    
    # Input Dimensions
    image_size: Tuple[int, int] = (224, 224)
    
    # Optimization Hyperparameters
    batch_size: int = 32
    learning_rate: float = 1e-3
    weight_decay: float = 1e-4
    epochs: int = 1
    
    # Early Stopping & Learning Rate Scheduling
    early_stopping_patience: int = 2
    optimizer_name: str = "adamw"
    scheduler_name: str = "cosine"
    
    # Reproducibility
    random_seed: int = 42

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["image_size"] = list(self.image_size)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrainingConfig":
        if "image_size" in data:
            data["image_size"] = tuple(data["image_size"])
        return cls(**data)

    def save_json(self, file_path: Path):
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)


DEFAULT_TRAINING_CONFIG = TrainingConfig()
