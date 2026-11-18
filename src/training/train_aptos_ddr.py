"""
Train a new EfficientNet-B0 model on the integrated APTOS 2019 + DDR dataset.

Preserves models/best_model.pth and all prior artifacts under outputs/training/.
Saves the new checkpoint exclusively to models/best_model_aptos_ddr.pth and
training logs/plots to outputs/training_aptos_ddr/.
"""

import json
import random
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import f1_score, recall_score
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader
from torchvision import transforms

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.training.dataset import FundusDataset
from src.training.model import count_parameters, get_model


def set_seed(seed: int = 42) -> None:
    """Set deterministic seeds across Python, NumPy, and PyTorch."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def compute_smoothed_class_weights(
    csv_path: Path,
    num_classes: int = 5,
    power: float = 0.65,
) -> Tuple[torch.Tensor, Dict[int, int]]:
    """Compute power-smoothed inverse class frequency weights normalized to mean 1."""
    df = pd.read_csv(csv_path)
    counts_dict = df["label"].value_counts().sort_index().to_dict()
    total = len(df)

    raw_weights = []
    for c in range(num_classes):
        cnt = max(int(counts_dict.get(c, 1)), 1)
        w = (total / (num_classes * cnt)) ** power
        raw_weights.append(w)

    weights = np.array(raw_weights, dtype=np.float32)
    weights = weights / weights.mean()
    return torch.tensor(weights, dtype=torch.float32), {
        int(k): int(v) for k, v in counts_dict.items()
    }


def build_transforms(image_size: int = 224) -> Tuple[transforms.Compose, transforms.Compose]:
    """Build ImageNet-normalized training augmentation and validation transforms."""
    mean = [0.485, 0.456, 0.406]
    std = [0.229, 0.224, 0.225]

    train_tf = transforms.Compose(
        [
            transforms.ToPILImage(),
            transforms.RandomResizedCrop(image_size, scale=(0.85, 1.0), ratio=(0.95, 1.05)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomVerticalFlip(p=0.5),
            transforms.RandomRotation(degrees=25),
            transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.10),
            transforms.ToTensor(),
            transforms.Normalize(mean=mean, std=std),
        ]
    )
    val_tf = transforms.Compose(
        [
            transforms.ToPILImage(),
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=mean, std=std),
        ]
    )
    return train_tf, val_tf


def compute_epoch_metrics(y_true: List[int], y_pred: List[int]) -> Dict[str, float]:
    """Compute accuracy, macro F1, and referable DR (grade >= 2) sensitivity."""
    yt = np.array(y_true, dtype=np.int64)
    yp = np.array(y_pred, dtype=np.int64)
    acc = float((yt == yp).mean())
    macro_f1 = float(f1_score(yt, yp, average="macro", zero_division=0))

    ref_true = (yt >= 2).astype(np.int64)
    ref_pred = (yp >= 2).astype(np.int64)
    ref_sens = float(recall_score(ref_true, ref_pred, pos_label=1, zero_division=0))
    ref_spec = float(recall_score(ref_true, ref_pred, pos_label=0, zero_division=0))
    return {
        "accuracy": acc,
        "macro_f1": macro_f1,
        "referable_sensitivity": ref_sens,
        "referable_specificity": ref_spec,
    }


def train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    epoch_idx: int,
    total_epochs: int,
) -> Tuple[float, Dict[str, float]]:
    """Run one training epoch with progress logging."""
    model.train()
    running_loss = 0.0
    total_samples = 0
    y_true: List[int] = []
    y_pred: List[int] = []

    t_start = time.time()
    n_batches = len(loader)
    for b_idx, (images, labels) in enumerate(loader, start=1):
        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=2.0)
        optimizer.step()

        bs = images.size(0)
        running_loss += float(loss.item()) * bs
        total_samples += bs

        preds = torch.argmax(outputs, dim=1)
        y_true.extend(labels.cpu().tolist())
        y_pred.extend(preds.cpu().tolist())

        if b_idx % 25 == 0 or b_idx == n_batches:
            elapsed = time.time() - t_start
            eta = (elapsed / b_idx) * (n_batches - b_idx)
            avg_loss = running_loss / max(total_samples, 1)
            print(
                f"  Epoch {epoch_idx}/{total_epochs} | Batch {b_idx}/{n_batches} | "
                f"Loss: {avg_loss:.4f} | Elapsed: {elapsed:.1f}s | ETA: {eta:.1f}s"
            )

    metrics = compute_epoch_metrics(y_true, y_pred)
    return running_loss / max(total_samples, 1), metrics


@torch.no_grad()
def validate_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> Tuple[float, Dict[str, float]]:
    """Evaluate model on the validation dataloader."""
    model.eval()
    running_loss = 0.0
    total_samples = 0
    y_true: List[int] = []
    y_pred: List[int] = []

    for images, labels in loader:
        images = images.to(device)
        labels = labels.to(device)
        outputs = model(images)
        loss = criterion(outputs, labels)

        bs = images.size(0)
        running_loss += float(loss.item()) * bs
        total_samples += bs
        preds = torch.argmax(outputs, dim=1)
        y_true.extend(labels.cpu().tolist())
        y_pred.extend(preds.cpu().tolist())

    metrics = compute_epoch_metrics(y_true, y_pred)
    return running_loss / max(total_samples, 1), metrics


def save_training_curves(history: List[Dict[str, Any]], out_path: Path) -> None:
    """Plot and save loss, accuracy, and macro-F1 curves across epochs."""
    epochs = [h["epoch"] for h in history]
    train_loss = [h["train_loss"] for h in history]
    val_loss = [h["val_loss"] for h in history]
    train_acc = [h["train_accuracy"] * 100.0 for h in history]
    val_acc = [h["val_accuracy"] * 100.0 for h in history]
    train_f1 = [h["train_macro_f1"] for h in history]
    val_f1 = [h["val_macro_f1"] for h in history]

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))

    axes[0].plot(epochs, train_loss, marker="o", label="Train")
    axes[0].plot(epochs, val_loss, marker="s", label="Val")
    axes[0].set_title("Cross-Entropy Loss")
    axes[0].set_xlabel("Epoch")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(epochs, train_acc, marker="o", label="Train")
    axes[1].plot(epochs, val_acc, marker="s", label="Val")
    axes[1].set_title("Accuracy (%)")
    axes[1].set_xlabel("Epoch")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(epochs, train_f1, marker="o", label="Train")
    axes[2].plot(epochs, val_f1, marker="s", label="Val")
    axes[2].set_title("Macro F1-Score")
    axes[2].set_xlabel("Epoch")
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close(fig)


def main() -> None:
    set_seed(42)
    cpu_threads = 12
    torch.set_num_threads(cpu_threads)
    device = torch.device("cpu")

    data_dir = ROOT_DIR / "data" / "processed_combined"
    train_csv = data_dir / "train.csv"
    val_csv = data_dir / "validation.csv"

    out_dir = ROOT_DIR / "outputs" / "training_aptos_ddr"
    out_dir.mkdir(parents=True, exist_ok=True)
    ckpt_path = ROOT_DIR / "models" / "best_model_aptos_ddr.pth"
    ckpt_path.parent.mkdir(parents=True, exist_ok=True)

    batch_size = 64
    epochs = 6
    learning_rate = 5e-4
    weight_decay = 1e-4
    early_stopping_patience = 3
    freeze_until_block = 4  # Freeze features.0..3; train features.4..8 (incl. Grad-CAM target) + classifier

    train_tf, val_tf = build_transforms(image_size=224)
    train_ds = FundusDataset(train_csv, is_training=True, transform=train_tf)
    val_ds = FundusDataset(val_csv, is_training=False, transform=val_tf)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=0)

    class_weights, train_counts = compute_smoothed_class_weights(train_csv, num_classes=5, power=0.65)
    criterion = nn.CrossEntropyLoss(weight=class_weights.to(device), label_smoothing=0.03)

    model = get_model(num_classes=5, pretrained=True)
    for idx in range(freeze_until_block):
        for param in model.features[idx].parameters():
            param.requires_grad = False
    model.to(device)

    total_params, trainable_params = count_parameters(model)
    optimizer = AdamW(
        [p for p in model.parameters() if p.requires_grad],
        lr=learning_rate,
        weight_decay=weight_decay,
    )
    scheduler = CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)

    config_summary = {
        "model_name": "efficientnet_b0",
        "pretrained": True,
        "device": str(device),
        "cpu_threads": cpu_threads,
        "freeze_until_feature_block": freeze_until_block,
        "total_parameters": total_params,
        "trainable_parameters": trainable_params,
        "batch_size": batch_size,
        "epochs_max": epochs,
        "early_stopping_patience": early_stopping_patience,
        "optimizer": "AdamW",
        "learning_rate": learning_rate,
        "weight_decay": weight_decay,
        "scheduler": "CosineAnnealingLR(eta_min=1e-5)",
        "loss": "CrossEntropyLoss(power_0.65_class_weights, label_smoothing=0.03)",
        "class_weights": [round(float(w), 4) for w in class_weights.tolist()],
        "train_samples": len(train_ds),
        "validation_samples": len(val_ds),
        "train_class_counts": train_counts,
        "selection_metric": "val_macro_f1",
        "random_seed": 42,
        "checkpoint_path": str(ckpt_path.relative_to(ROOT_DIR)).replace("\\", "/"),
    }
    with open(out_dir / "training_config.json", "w", encoding="utf-8") as f:
        json.dump(config_summary, f, indent=2)

    print("=== Training Configuration ===")
    print(json.dumps(config_summary, indent=2))

    history: List[Dict[str, Any]] = []
    best_val_f1 = -1.0
    best_epoch = -1
    no_improve_epochs = 0
    total_start = time.time()

    for epoch in range(1, epochs + 1):
        ep_start = time.time()
        current_lr = optimizer.param_groups[0]["lr"]
        print(f"\n--- Epoch {epoch}/{epochs} (LR: {current_lr:.6f}) ---")

        train_loss, train_m = train_one_epoch(
            model, train_loader, criterion, optimizer, device, epoch, epochs
        )
        val_loss, val_m = validate_one_epoch(model, val_loader, criterion, device)
        scheduler.step()

        ep_duration = time.time() - ep_start
        record = {
            "epoch": epoch,
            "lr": float(current_lr),
            "duration_seconds": round(ep_duration, 2),
            "train_loss": round(train_loss, 4),
            "train_accuracy": round(train_m["accuracy"], 4),
            "train_macro_f1": round(train_m["macro_f1"], 4),
            "val_loss": round(val_loss, 4),
            "val_accuracy": round(val_m["accuracy"], 4),
            "val_macro_f1": round(val_m["macro_f1"], 4),
            "val_referable_sensitivity": round(val_m["referable_sensitivity"], 4),
            "val_referable_specificity": round(val_m["referable_specificity"], 4),
        }
        history.append(record)

        print(
            f"[Epoch {epoch} Summary | {ep_duration:.1f}s] "
            f"Train Loss: {train_loss:.4f} Acc: {train_m['accuracy']*100:.2f}% F1: {train_m['macro_f1']:.4f} | "
            f"Val Loss: {val_loss:.4f} Acc: {val_m['accuracy']*100:.2f}% F1: {val_m['macro_f1']:.4f} "
            f"RefSens: {val_m['referable_sensitivity']:.4f} RefSpec: {val_m['referable_specificity']:.4f}"
        )

        # Save incremental history after every epoch
        with open(out_dir / "training_history.json", "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)

        if val_m["macro_f1"] > best_val_f1:
            best_val_f1 = val_m["macro_f1"]
            best_epoch = epoch
            no_improve_epochs = 0
            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "val_macro_f1": float(val_m["macro_f1"]),
                    "val_accuracy": float(val_m["accuracy"]),
                    "val_loss": float(val_loss),
                    "config": config_summary,
                },
                ckpt_path,
            )
            print(f"  -> Saved new best checkpoint ({ckpt_path.name}, val_macro_f1={best_val_f1:.4f})")
        else:
            no_improve_epochs += 1
            print(f"  -> No val_macro_f1 improvement ({no_improve_epochs}/{early_stopping_patience})")
            if no_improve_epochs >= early_stopping_patience:
                print(f"Early stopping triggered at epoch {epoch}.")
                break

    total_duration = time.time() - total_start
    save_training_curves(history, out_dir / "training_curves.png")

    summary = {
        "best_epoch": best_epoch,
        "best_val_macro_f1": round(best_val_f1, 4),
        "epochs_completed": len(history),
        "total_duration_seconds": round(total_duration, 2),
        "total_duration_minutes": round(total_duration / 60.0, 2),
    }
    with open(out_dir / "training_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\n=== Training Complete in {total_duration/60.0:.2f} min ===")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

