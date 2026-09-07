"""External Validation and Dataset Ingestion module for Netra.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import cv2
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from sklearn.metrics import classification_report, confusion_matrix, precision_recall_fscore_support
from torchvision import transforms

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.training.model import get_model


def evaluate_external_dataset(
    model: torch.nn.Module,
    csv_path: Path,
    device: torch.device,
    temperature: float = 1.0,
) -> Dict[str, Any]:
    """
    Evaluates trained DR classifier on an external dataset manifest CSV.
    Expected CSV columns: 'image_path', 'label' (0-4).
    """
    if not csv_path.exists():
        return {
            "status": "NOT_AVAILABLE",
            "message": f"External dataset manifest at {csv_path} not found.",
        }

    df = pd.read_csv(csv_path)
    if "image_path" not in df.columns or "label" not in df.columns:
        return {
            "status": "INVALID_SCHEMA",
            "message": "CSV must contain 'image_path' and 'label' columns.",
        }

    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    y_true = []
    y_pred = []
    y_confs = []

    model.eval()
    with torch.no_grad():
        for _, row in df.iterrows():
            img_path = Path(row["image_path"])
            if not img_path.is_absolute():
                img_path = ROOT_DIR / img_path

            label = int(row["label"])
            if img_path.exists():
                img_bgr = cv2.imread(str(img_path))
                if img_bgr is not None:
                    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
                    tensor_img = transform(img_rgb).unsqueeze(0).to(device)

                    logits = model(tensor_img) / temperature
                    probs = F.softmax(logits, dim=1).squeeze(0).cpu().numpy()
                    pred_class = int(np.argmax(probs))

                    y_true.append(label)
                    y_pred.append(pred_class)
                    y_confs.append(float(probs[pred_class]))

    if not y_true:
        return {
            "status": "EMPTY",
            "message": "No readable images were found in the dataset.",
        }

    acc = float(np.mean(np.array(y_true) == np.array(y_pred)))
    p, r, f1, _ = precision_recall_fscore_support(y_true, y_pred, average="macro", zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1, 2, 3, 4]).tolist()

    return {
        "status": "SUCCESS",
        "samples_evaluated": len(y_true),
        "accuracy": round(acc, 4),
        "macro_precision": round(float(p), 4),
        "macro_recall": round(float(r), 4),
        "macro_f1": round(float(f1), 4),
        "confusion_matrix": cm,
        "mean_confidence": round(float(np.mean(y_confs)), 4),
    }
