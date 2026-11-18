"""
Comprehensive evaluation & comparison of:
  1. Preserved baseline checkpoint: models/best_model.pth
  2. Newly trained combined checkpoint: models/best_model_aptos_ddr.pth

Evaluates both models on:
  - Internal held-out test split (data/processed_combined/test.csv), plus APTOS & DDR subsets
  - External clinical validation dataset (data/raw/sustech_external/external_manifest.csv)
    preprocessed in-memory via preprocess_single_image(..., DEFAULT_CONFIG)

Also fits temperature scaling on validation logits, computes calibration metrics,
verifies Grad-CAM compatibility on models/best_model_aptos_ddr.pth, and saves all
outputs under outputs/evaluation_aptos_ddr/.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    cohen_kappa_score,
    confusion_matrix,
    precision_recall_fscore_support,
    roc_auc_score,
)
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.evaluation.calibration import TemperatureScaler, compute_ece
from src.explainability.gradcam import GradCAM
from src.preprocessing.config import DEFAULT_CONFIG
from src.preprocessing.preprocess import preprocess_single_image
from src.reporting.screening_report import overlay_heatmap_on_image
from src.training.dataset import FundusDataset
from src.training.model import get_model

CLASS_NAMES = ["No DR", "Mild", "Moderate", "Severe", "Proliferative DR"]


class PreprocessedExternalDataset(Dataset):
    """Dataset wrapper that runs Netra's preprocessing pipeline on raw external images."""

    def __init__(self, csv_path: Path, transform: transforms.Compose) -> None:
        self.df = pd.read_csv(csv_path)
        self.transform = transform

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        row = self.df.iloc[idx]
        img_path = ROOT_DIR / str(row["image_path"])
        rgb = preprocess_single_image(img_path, config=DEFAULT_CONFIG)
        pil_img = Image.fromarray(rgb)
        tensor = self.transform(pil_img)
        return tensor, int(row["label"])


def _ensure_pil(img: Any) -> Image.Image:
    """Convert numpy RGB arrays from FundusDataset to PIL Images for torchvision transforms."""
    return Image.fromarray(img) if isinstance(img, np.ndarray) else img


def get_eval_transform(image_size: int = 224) -> transforms.Compose:
    """Return ImageNet evaluation transform matching model training."""
    return transforms.Compose(
        [
            transforms.Lambda(_ensure_pil),
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )


def load_trained_model(checkpoint_path: Path, device: torch.device) -> nn.Module:
    """Load EfficientNet-B0 weights from checkpoint dictionary or raw state_dict."""
    model = get_model(num_classes=5, pretrained=False)
    ckpt = torch.load(checkpoint_path, map_location=device, weights_only=False)
    if isinstance(ckpt, dict) and "model_state_dict" in ckpt:
        model.load_state_dict(ckpt["model_state_dict"])
    else:
        model.load_state_dict(ckpt)
    model.to(device)
    model.eval()
    return model


@torch.no_grad()
def collect_logits_and_labels(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
    use_tta: bool = False,
) -> Tuple[torch.Tensor, Optional[torch.Tensor], np.ndarray]:
    """Run inference over a dataloader and return single-pass logits, optional 4x TTA logits, and labels."""
    logits_list: List[torch.Tensor] = []
    tta_list: List[torch.Tensor] = []
    labels_list: List[np.ndarray] = []
    for images, labels in loader:
        images = images.to(device)
        out0 = model(images)
        logits_list.append(out0.cpu())
        if use_tta:
            out_h = model(torch.flip(images, dims=[3]))
            out_v = model(torch.flip(images, dims=[2]))
            out_hv = model(torch.flip(images, dims=[2, 3]))
            tta_list.append(((out0 + out_h + out_v + out_hv) * 0.25).cpu())
        labels_list.append(labels.numpy() if isinstance(labels, torch.Tensor) else np.array(labels))
    raw_logits = torch.cat(logits_list, dim=0)
    tta_logits = torch.cat(tta_list, dim=0) if use_tta else None
    return raw_logits, tta_logits, np.concatenate(labels_list, axis=0)


def compute_metrics_from_logits(
    logits: torch.Tensor,
    labels: np.ndarray,
    temperature: float = 1.0,
) -> Dict[str, Any]:
    """Compute classification, referable DR, confusion matrix, and calibration metrics."""
    raw_probs = F.softmax(logits, dim=1).numpy()
    cal_probs = F.softmax(logits / temperature, dim=1).numpy()
    preds = np.argmax(cal_probs, axis=1)

    acc = float(accuracy_score(labels, preds))
    macro_p, macro_r, macro_f1, _ = precision_recall_fscore_support(
        labels, preds, average="macro", zero_division=0
    )
    weighted_p, weighted_r, weighted_f1, _ = precision_recall_fscore_support(
        labels, preds, average="weighted", zero_division=0
    )
    qwk = float(cohen_kappa_score(labels, preds, weights="quadratic"))

    p_cls, r_cls, f1_cls, sup_cls = precision_recall_fscore_support(
        labels, preds, labels=[0, 1, 2, 3, 4], average=None, zero_division=0
    )
    per_class = {
        str(c): {
            "name": CLASS_NAMES[c],
            "precision": round(float(p_cls[c]), 4),
            "recall": round(float(r_cls[c]), 4),
            "f1": round(float(f1_cls[c]), 4),
            "support": int(sup_cls[c]),
        }
        for c in range(5)
    }

    cm = confusion_matrix(labels, preds, labels=[0, 1, 2, 3, 4]).tolist()

    # Referable DR: Grade >= 2 vs Grades 0-1
    ref_true = (labels >= 2).astype(np.int64)
    ref_pred = (preds >= 2).astype(np.int64)
    ref_score = cal_probs[:, 2:].sum(axis=1)

    tp = int(np.sum((ref_true == 1) & (ref_pred == 1)))
    fn = int(np.sum((ref_true == 1) & (ref_pred == 0)))
    tn = int(np.sum((ref_true == 0) & (ref_pred == 0)))
    fp = int(np.sum((ref_true == 0) & (ref_pred == 1)))

    ref_sens = float(tp / max(tp + fn, 1))
    ref_spec = float(tn / max(tn + fp, 1))
    ref_prec = float(tp / max(tp + fp, 1))
    ref_f1 = float((2 * tp) / max(2 * tp + fp + fn, 1))
    ref_auc = (
        float(roc_auc_score(ref_true, ref_score))
        if len(np.unique(ref_true)) == 2
        else None
    )

    raw_ece, raw_mce, raw_cal_meta = compute_ece(raw_probs, labels, n_bins=10)
    cal_ece, cal_mce, cal_meta = compute_ece(cal_probs, labels, n_bins=10)

    return {
        "n_samples": int(len(labels)),
        "accuracy": round(acc, 4),
        "macro_precision": round(float(macro_p), 4),
        "macro_recall": round(float(macro_r), 4),
        "macro_f1": round(float(macro_f1), 4),
        "weighted_precision": round(float(weighted_p), 4),
        "weighted_recall": round(float(weighted_r), 4),
        "weighted_f1": round(float(weighted_f1), 4),
        "quadratic_weighted_kappa": round(qwk, 4),
        "per_class": per_class,
        "confusion_matrix": cm,
        "referable_dr": {
            "definition": "Grade >= 2 (Moderate, Severe, Proliferative DR)",
            "sensitivity": round(ref_sens, 4),
            "specificity": round(ref_spec, 4),
            "precision": round(ref_prec, 4),
            "f1": round(ref_f1, 4),
            "roc_auc": round(ref_auc, 4) if ref_auc is not None else None,
            "tp": tp,
            "tn": tn,
            "fp": fp,
            "fn": fn,
        },
        "calibration": {
            "temperature": round(float(temperature), 4),
            "raw_ece": round(float(raw_ece), 4),
            "raw_mce": round(float(raw_mce), 4),
            "calibrated_ece": round(float(cal_ece), 4),
            "calibrated_mce": round(float(cal_mce), 4),
            "calibrated_bins": cal_meta,
        },
    }


def save_confusion_matrix_comparison(
    old_cm: List[List[int]],
    new_cm: List[List[int]],
    title_prefix: str,
    out_path: Path,
) -> None:
    """Plot side-by-side row-normalized confusion matrices for old vs new models."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.2))
    short_names = ["No DR", "Mild", "Mod", "Sev", "PDR"]

    for ax, cm_list, label in [
        (axes[0], old_cm, "Baseline (models/best_model.pth)"),
        (axes[1], new_cm, "APTOS + DDR (models/best_model_aptos_ddr.pth)"),
    ]:
        cm = np.array(cm_list, dtype=np.float32)
        row_sums = cm.sum(axis=1, keepdims=True)
        norm_cm = np.divide(cm, np.maximum(row_sums, 1.0))

        im = ax.imshow(norm_cm, interpolation="nearest", cmap=plt.cm.Blues, vmin=0.0, vmax=1.0)
        ax.set_title(f"{title_prefix}\n{label}", fontsize=10)
        ax.set_xticks(range(5))
        ax.set_yticks(range(5))
        ax.set_xticklabels(short_names, rotation=30, ha="right")
        ax.set_yticklabels(short_names)
        ax.set_ylabel("True Grade")
        ax.set_xlabel("Predicted Grade")

        for i in range(5):
            for j in range(5):
                color = "white" if norm_cm[i, j] > 0.5 else "black"
                ax.text(
                    j,
                    i,
                    f"{int(cm[i, j])}\n({norm_cm[i, j]*100:.0f}%)",
                    ha="center",
                    va="center",
                    color=color,
                    fontsize=8,
                )

    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close(fig)


def verify_gradcam_compatibility(
    model: nn.Module,
    test_csv: Path,
    ext_csv: Path,
    eval_tf: transforms.Compose,
    device: torch.device,
    out_dir: Path,
) -> Dict[str, Any]:
    """Verify Grad-CAM works cleanly on new model across all grades and external images."""
    out_dir.mkdir(parents=True, exist_ok=True)
    gradcam = GradCAM(model)  # Defaults to model.features[-1]

    test_df = pd.read_csv(test_csv)
    ext_df = pd.read_csv(ext_csv)

    samples: List[Tuple[str, Path, int]] = []
    for grade in range(5):
        sub = test_df[test_df["label"] == grade]
        if len(sub) > 0:
            row = sub.iloc[0]
            rel = str(row.get("processed_image_path", row["image_path"]))
            samples.append((f"internal_grade_{grade}", ROOT_DIR / rel, int(row["label"])))

    for grade in [0, 3]:
        sub = ext_df[ext_df["label"] == grade]
        if len(sub) > 0:
            row = sub.iloc[0]
            samples.append((f"external_grade_{grade}", ROOT_DIR / str(row["image_path"]), int(row["label"])))

    checks = []
    for tag, img_path, true_label in samples:
        if "external_" in tag:
            rgb = preprocess_single_image(img_path, config=DEFAULT_CONFIG)
        else:
            bgr = cv2.imread(str(img_path))
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

        pil_img = Image.fromarray(rgb)
        inp = eval_tf(pil_img).unsqueeze(0).to(device)
        inp.requires_grad_(True)

        heatmap, pred_class, probs = gradcam.generate_heatmap(inp)
        valid = bool(
            heatmap.shape == (224, 224)
            and not np.isnan(heatmap).any()
            and not np.isinf(heatmap).any()
            and float(heatmap.std()) > 0.0
        )

        orig_bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        overlay_bgr = overlay_heatmap_on_image(orig_bgr, heatmap, alpha=0.45)
        combined = np.hstack([orig_bgr, overlay_bgr])
        save_path = out_dir / f"{tag}.png"
        cv2.imwrite(str(save_path), combined)

        checks.append(
            {
                "sample": tag,
                "true_label": true_label,
                "pred_label": int(pred_class),
                "pred_confidence": round(float(probs[pred_class]), 4),
                "heatmap_shape": list(heatmap.shape),
                "heatmap_min": round(float(heatmap.min()), 4),
                "heatmap_max": round(float(heatmap.max()), 4),
                "heatmap_std": round(float(heatmap.std()), 4),
                "valid": valid,
                "overlay_path": str(save_path.relative_to(ROOT_DIR)).replace("\\", "/"),
            }
        )

    return {
        "target_layer": "model.features[-1]",
        "all_checks_passed": all(c["valid"] for c in checks),
        "num_samples_tested": len(checks),
        "samples": checks,
    }


def main() -> None:
    torch.set_num_threads(12)
    device = torch.device("cpu")
    eval_tf = get_eval_transform(224)

    data_dir = ROOT_DIR / "data" / "processed_combined"
    val_csv = data_dir / "validation.csv"
    test_csv = data_dir / "test.csv"
    ext_csv = ROOT_DIR / "data" / "raw" / "sustech_external" / "external_manifest.csv"

    out_dir = ROOT_DIR / "outputs" / "evaluation_aptos_ddr"
    out_dir.mkdir(parents=True, exist_ok=True)

    old_ckpt = ROOT_DIR / "models" / "best_model.pth"
    new_ckpt = ROOT_DIR / "models" / "best_model_aptos_ddr.pth"

    print("Loading datasets...")
    val_loader = DataLoader(FundusDataset(val_csv, False, eval_tf), batch_size=64, shuffle=False, num_workers=0)
    test_df = pd.read_csv(test_csv)
    test_loader = DataLoader(FundusDataset(test_csv, False, eval_tf), batch_size=64, shuffle=False, num_workers=0)
    ext_loader = DataLoader(PreprocessedExternalDataset(ext_csv, eval_tf), batch_size=64, shuffle=False, num_workers=0)

    print("Loading models...")
    old_model = load_trained_model(old_ckpt, device)
    new_model = load_trained_model(new_ckpt, device)

    # Fit Temperature Scaler for new model on internal validation split
    print("Fitting temperature scaler on validation logits for new APTOS+DDR model...")
    val_logits_new, _, val_labels = collect_logits_and_labels(new_model, val_loader, device, use_tta=False)
    scaler = TemperatureScaler(initial_temperature=1.5)
    scaler.fit(val_logits_new, torch.tensor(val_labels, dtype=torch.long))
    new_temp = float(scaler.get_temperature())
    val_cal_metrics = compute_metrics_from_logits(val_logits_new, val_labels, temperature=new_temp)
    with open(out_dir / "calibration_parameters.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "optimal_temperature": round(new_temp, 4),
                "validation_raw_ece": val_cal_metrics["calibration"]["raw_ece"],
                "validation_raw_mce": val_cal_metrics["calibration"]["raw_mce"],
                "validation_calibrated_ece": val_cal_metrics["calibration"]["calibrated_ece"],
                "validation_calibrated_mce": val_cal_metrics["calibration"]["calibrated_mce"],
            },
            f,
            indent=2,
        )
    print(f"Optimal temperature (new model): {new_temp:.4f}")

    # Load preserved baseline temperature if present
    old_cal_file = ROOT_DIR / "outputs" / "confidence" / "calibration_parameters.json"
    old_temp = 1.07
    if old_cal_file.exists():
        with open(old_cal_file, "r", encoding="utf-8") as f:
            old_temp = float(json.load(f).get("optimal_temperature", 1.07))

    # Collect internal test logits (plus 4x TTA on new model)
    print("Evaluating both models on internal held-out test set...")
    old_test_logits, _, test_labels = collect_logits_and_labels(old_model, test_loader, device, use_tta=False)
    new_test_logits, new_test_tta_logits, _ = collect_logits_and_labels(new_model, test_loader, device, use_tta=True)

    old_internal = compute_metrics_from_logits(old_test_logits, test_labels, temperature=old_temp)
    new_internal = compute_metrics_from_logits(new_test_logits, test_labels, temperature=new_temp)
    new_internal_tta = compute_metrics_from_logits(new_test_tta_logits, test_labels, temperature=new_temp)

    # Dataset subsets inside internal test (APTOS vs DDR)
    aptos_mask = (test_df["source_dataset"] == "APTOS_2019").to_numpy()
    ddr_mask = (test_df["source_dataset"] == "DDR").to_numpy()

    new_internal_aptos = compute_metrics_from_logits(
        new_test_logits[aptos_mask], test_labels[aptos_mask], temperature=new_temp
    )
    new_internal_aptos_tta = compute_metrics_from_logits(
        new_test_tta_logits[aptos_mask], test_labels[aptos_mask], temperature=new_temp
    )
    new_internal_ddr = compute_metrics_from_logits(
        new_test_logits[ddr_mask], test_labels[ddr_mask], temperature=new_temp
    )
    new_internal_ddr_tta = compute_metrics_from_logits(
        new_test_tta_logits[ddr_mask], test_labels[ddr_mask], temperature=new_temp
    )
    old_internal_aptos = compute_metrics_from_logits(
        old_test_logits[aptos_mask], test_labels[aptos_mask], temperature=old_temp
    )
    old_internal_ddr = compute_metrics_from_logits(
        old_test_logits[ddr_mask], test_labels[ddr_mask], temperature=old_temp
    )

    # Collect external SUSTech-SYSU logits
    print("Evaluating both models on external SUSTech-SYSU dataset (1,219 images)...")
    old_ext_logits, _, ext_labels = collect_logits_and_labels(old_model, ext_loader, device, use_tta=False)
    new_ext_logits, new_ext_tta_logits, _ = collect_logits_and_labels(new_model, ext_loader, device, use_tta=True)

    old_external = compute_metrics_from_logits(old_ext_logits, ext_labels, temperature=old_temp)
    new_external = compute_metrics_from_logits(new_ext_logits, ext_labels, temperature=new_temp)
    new_external_tta = compute_metrics_from_logits(new_ext_tta_logits, ext_labels, temperature=new_temp)

    # Confusion matrix figures
    save_confusion_matrix_comparison(
        old_internal["confusion_matrix"],
        new_internal_tta["confusion_matrix"],
        "Internal Held-Out Test (APTOS + DDR)",
        out_dir / "confusion_matrix_internal.png",
    )
    save_confusion_matrix_comparison(
        old_external["confusion_matrix"],
        new_external_tta["confusion_matrix"],
        "External Clinical Validation (SUSTech-SYSU)",
        out_dir / "confusion_matrix_external.png",
    )

    # Grad-CAM compatibility
    print("Verifying Grad-CAM compatibility on new APTOS+DDR model...")
    gradcam_report = verify_gradcam_compatibility(
        new_model, test_csv, ext_csv, eval_tf, device, out_dir / "gradcam_samples"
    )

    # Read preserved baseline old-test record for full transparency
    old_synthetic_path = ROOT_DIR / "outputs" / "full_system_audit" / "model_evaluation_metrics.json"
    old_synthetic_summary = None
    if old_synthetic_path.exists():
        with open(old_synthetic_path, "r", encoding="utf-8") as f:
            old_synthetic_summary = json.load(f)

    report = {
        "old_model_checkpoint": "models/best_model.pth",
        "new_model_checkpoint": "models/best_model_aptos_ddr.pth",
        "idrid_external_status": (
            "Unavailable locally without authentication: IEEE DataPort requires user login "
            "(https://ieee-dataport.org/open-access/indian-diabetic-retinopathy-image-dataset-idrid). "
            "SUSTech-SYSU (1,219 real clinical fundus photos with ICDR 0-4 grading) used for external clinical validation."
        ),
        "internal_test_overall": {
            "old_baseline": old_internal,
            "new_aptos_ddr_single": new_internal,
            "new_aptos_ddr_tta4": new_internal_tta,
        },
        "internal_test_by_source": {
            "APTOS_2019": {
                "old_baseline": old_internal_aptos,
                "new_aptos_ddr_single": new_internal_aptos,
                "new_aptos_ddr_tta4": new_internal_aptos_tta,
            },
            "DDR": {
                "old_baseline": old_internal_ddr,
                "new_aptos_ddr_single": new_internal_ddr,
                "new_aptos_ddr_tta4": new_internal_ddr_tta,
            },
        },
        "external_validation_sustech_sysu": {
            "old_baseline": old_external,
            "new_aptos_ddr_single": new_external,
            "new_aptos_ddr_tta4": new_external_tta,
        },
        "gradcam_compatibility": gradcam_report,
        "preserved_old_synthetic_test_record": old_synthetic_summary,
    }

    report_path = out_dir / "comparison_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\nEvaluation complete! Report saved to {report_path}")
    print(
        f"Internal Test | Old Acc={old_internal['accuracy']*100:.2f}% F1={old_internal['macro_f1']:.4f} | "
        f"New Single Acc={new_internal['accuracy']*100:.2f}% F1={new_internal['macro_f1']:.4f} | "
        f"New TTA4 Acc={new_internal_tta['accuracy']*100:.2f}% F1={new_internal_tta['macro_f1']:.4f} "
        f"QWK={new_internal_tta['quadratic_weighted_kappa']:.4f} "
        f"RefSens={new_internal_tta['referable_dr']['sensitivity']:.4f} RefSpec={new_internal_tta['referable_dr']['specificity']:.4f}"
    )
    print(
        f"External SUSTech-SYSU | Old Acc={old_external['accuracy']*100:.2f}% F1={old_external['macro_f1']:.4f} | "
        f"New Single Acc={new_external['accuracy']*100:.2f}% | "
        f"New TTA4 Acc={new_external_tta['accuracy']*100:.2f}% F1={new_external_tta['macro_f1']:.4f} "
        f"QWK={new_external_tta['quadratic_weighted_kappa']:.4f} "
        f"RefSens={new_external_tta['referable_dr']['sensitivity']:.4f} RefSpec={new_external_tta['referable_dr']['specificity']:.4f}"
    )


if __name__ == "__main__":
    main()

