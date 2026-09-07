"""
Netra PyTorch Dataset & DataLoader Module
Loads processed fundus images, calculates training class weights, and manages DataLoaders.
"""

from pathlib import Path
from typing import Tuple, Dict, Any, Optional

import cv2
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
PROCESSED_DATA_DIR = ROOT_DIR / "data" / "processed"

# Standard ImageNet Normalization Constants
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


class FundusDataset(Dataset):
    """PyTorch Dataset loading processed fundus images and target labels."""

    def __init__(self, csv_path: Path, is_training: bool = False, transform: Optional[Any] = None):
        self.df = pd.read_csv(csv_path)
        self.is_training = is_training
        self.transform = transform

        if self.transform is None:
            if is_training:
                self.transform = transforms.Compose([
                    transforms.ToPILImage(),
                    transforms.RandomRotation(degrees=20),
                    transforms.RandomHorizontalFlip(p=0.5),
                    transforms.RandomVerticalFlip(p=0.5),
                    transforms.ColorJitter(brightness=0.2, contrast=0.2),
                    transforms.ToTensor(),
                    transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
                ])
            else:
                self.transform = transforms.Compose([
                    transforms.ToPILImage(),
                    transforms.ToTensor(),
                    transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
                ])

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        row = self.df.iloc[idx]
        img_rel_path = str(row.get("processed_image_path", row.get("image_path")))
        img_full_path = ROOT_DIR / img_rel_path
        lbl = int(row["label"])

        if img_full_path.exists():
            img_bgr = cv2.imread(str(img_full_path))
            if img_bgr is None:
                img_rgb = np.zeros((224, 224, 3), dtype=np.uint8)
            else:
                img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        else:
            # Fallback for synthetic/missing image during testing
            img_rgb = np.zeros((224, 224, 3), dtype=np.uint8)

        img_tensor = self.transform(img_rgb)
        label_tensor = torch.tensor(lbl, dtype=torch.long)
        return img_tensor, label_tensor


def calculate_class_weights(train_csv_path: Path, num_classes: int = 5) -> torch.Tensor:
    """
    Calculates inverse class weights strictly from the training set:
    W_k = N_train / (num_classes * N_k)
    """
    df = pd.read_csv(train_csv_path)
    total_samples = len(df)
    class_counts = df["label"].value_counts().to_dict()

    weights = []
    for c in range(num_classes):
        count = class_counts.get(c, 1)
        w = total_samples / (num_classes * count)
        weights.append(w)

    weights_tensor = torch.tensor(weights, dtype=torch.float32)
    # Normalize weights so they sum to num_classes
    weights_tensor = weights_tensor / weights_tensor.sum() * num_classes
    return weights_tensor


def get_dataloaders(
    train_csv: Path = PROCESSED_DATA_DIR / "train.csv",
    val_csv: Path = PROCESSED_DATA_DIR / "validation.csv",
    batch_size: int = 32,
    num_workers: int = 0
) -> Tuple[DataLoader, DataLoader]:
    """Instantiates PyTorch DataLoaders for Training and Validation splits."""
    train_dataset = FundusDataset(train_csv, is_training=True)
    val_dataset = FundusDataset(val_csv, is_training=False)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=num_workers)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers)

    return train_loader, val_loader
