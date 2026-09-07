"""
Netra Preprocessing Configuration Module
Allows changing target image size, CLAHE limits, denoising, normalization, and augmentation
without modifying core pipeline logic.
"""

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Tuple, Dict, Any, List


@dataclass
class PreprocessingConfig:
    # Target Image Dimensions (Width, Height)
    target_size: Tuple[int, int] = (224, 224)
    
    # Fundus Boundary Cropping
    crop_black_borders: bool = True
    border_threshold: int = 10
    crop_safety_margin: float = 0.02  # 2% margin around retina
    
    # Contrast Limited Adaptive Histogram Equalization (CLAHE)
    clahe_enabled: bool = True
    clahe_clip_limit: float = 2.0
    clahe_tile_grid_size: Tuple[int, int] = (8, 8)
    
    # Denoising Filter (Configurable Toggle)
    denoising_enabled: bool = False
    denoising_h: float = 10.0
    denoising_template_window: int = 7
    denoising_search_window: int = 21
    
    # Normalization Scheme: 'zero_to_one' [0, 1] or 'z_score' or 'raw_255' [0, 255]
    normalization_method: str = "zero_to_one"
    
    # Training Augmentation Configuration (Runtime only - not saved to disk)
    augmentation: Dict[str, Any] = None

    def __post_init__(self):
        if self.augmentation is None:
            self.augmentation = {
                "rotation_range_deg": 20,
                "horizontal_flip": True,
                "vertical_flip": True,
                "brightness_range": [0.8, 1.2],
                "zoom_range": [0.9, 1.1],
            }

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["target_size"] = list(self.target_size)
        d["clahe_tile_grid_size"] = list(self.clahe_tile_grid_size)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PreprocessingConfig":
        if "target_size" in data:
            data["target_size"] = tuple(data["target_size"])
        if "clahe_tile_grid_size" in data:
            data["clahe_tile_grid_size"] = tuple(data["clahe_tile_grid_size"])
        return cls(**data)

    def save_json(self, file_path: Path):
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_json(cls, file_path: Path) -> "PreprocessingConfig":
        with open(file_path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)


# Default Configuration Instance
DEFAULT_CONFIG = PreprocessingConfig()
