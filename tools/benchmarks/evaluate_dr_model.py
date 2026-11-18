"""Script to evaluate the trained EfficientNet-B0 model (models/best_model.pth)
on the real labeled test split (data/processed/test.csv) for Part 5 of the Audit.
Computes real Accuracy, Macro F1, Precision, Recall, Per-Class metrics, and Confusion Matrix.
"""

import json
import os
import sys
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from sklearn.metrics import classification_report, confusion_matrix, precision_recall_fscore_support
from torchvision import transforms

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.training.model import get_model

CLASS_NAMES = ["Level 0: No DR", "Level 1: Mild DR", "Level 2: Moderate DR", "Level 3: Severe DR", "Level 4: Proliferative DR"]


def evaluate_model():
    out_dir = ROOT_DIR / "outputs" / "full_system_audit"
    out_dir.mkdir(parents=True, exist_ok=True)

    model_path = ROOT_DIR / "models" / "best_model.pth"
    test_csv = ROOT_DIR / "data" / "processed" / "test.csv"

    if not model_path.exists():
        print(f"Error: {model_path} not found.")
        return

    if not test_csv.exists():
        print(f"Error: {test_csv} not found.")
        return

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = get_model(num_classes=5, pretrained=False)

    checkpoint = torch.load(model_path, map_location=device)
    state_dict = checkpoint.get("model_state_dict", checkpoint)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()

    df = pd.read_csv(test_csv)
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    y_true = []
    y_pred = []
    confidences = []

    with torch.no_grad():
        for _, row in df.iterrows():
            img_p = ROOT_DIR / str(row["processed_image_path"])
            label = int(row["label"])
            if img_p.exists():
                img_bgr = cv2.imread(str(img_p))
                if img_bgr is not None:
                    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
                    tensor_img = transform(img_rgb).unsqueeze(0).to(device)

                    logits = model(tensor_img)
                    probs = F.softmax(logits, dim=1).squeeze(0).cpu().numpy()
                    pred_class = int(np.argmax(probs))

                    y_true.append(label)
                    y_pred.append(pred_class)
                    confidences.append(float(probs[pred_class]))

    y_true_np = np.array(y_true)
    y_pred_np = np.array(y_pred)

    acc = float(np.mean(y_true_np == y_pred_np))
    p, r, f1, support = precision_recall_fscore_support(y_true_np, y_pred_np, average="macro", zero_division=0)
    p_per, r_per, f1_per, sup_per = precision_recall_fscore_support(y_true_np, y_pred_np, average=None, zero_division=0)

    cm = confusion_matrix(y_true_np, y_pred_np, labels=[0, 1, 2, 3, 4]).tolist()

    per_class_metrics = {}
    for i in range(5):
        per_class_metrics[f"class_{i}"] = {
            "name": CLASS_NAMES[i],
            "precision": round(float(p_per[i]), 4),
            "recall": round(float(r_per[i]), 4),
            "f1_score": round(float(f1_per[i]), 4),
            "support": int(sup_per[i]),
        }

    results = {
        "dataset_evaluated": "data/processed/test.csv",
        "total_test_samples": len(y_true),
        "overall_accuracy": round(acc, 4),
        "macro_precision": round(float(p), 4),
        "macro_recall": round(float(r), 4),
        "macro_f1": round(float(f1), 4),
        "mean_confidence": round(float(np.mean(confidences)), 4),
        "confusion_matrix": cm,
        "per_class_metrics": per_class_metrics,
    }

    with open(out_dir / "model_evaluation_metrics.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("DR Model evaluation completed. Accuracy:", round(acc * 100, 2), "% | Macro F1:", round(f1, 4))


if __name__ == "__main__":
    evaluate_model()
