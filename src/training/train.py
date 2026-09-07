"""
Netra Baseline Model Training Script
Trains EfficientNet-B0 on processed Diabetic Retinopathy training split with weighted CrossEntropy loss,
early stopping based on validation performance, and saves models/best_model.pth.
"""

import json
import os
import random
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR

# Import project modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.training.config import TrainingConfig, DEFAULT_TRAINING_CONFIG
from src.training.dataset import FundusDataset, calculate_class_weights, get_dataloaders
from src.training.model import get_model, count_parameters

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
PROCESSED_DATA_DIR = ROOT_DIR / "data" / "processed"
MODEL_SAVE_DIR = ROOT_DIR / "models"
OUTPUT_TRAIN_DIR = ROOT_DIR / "outputs" / "training"

DR_CLASSES = {
    0: "No DR",
    1: "Mild",
    2: "Moderate",
    3: "Severe",
    4: "Proliferative DR",
}


def set_reproducible_seed(seed: int = 42):
    """Ensures 100% reproducible training execution across PyTorch, NumPy, and Python random."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def train_one_epoch(
    model: nn.Module,
    dataloader: torch.utils.data.DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device
) -> Tuple[float, float]:
    """Executes single training epoch."""
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for inputs, labels in dataloader:
        inputs, labels = inputs.to(device), labels.to(device)

        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)

        # Check for NaN loss
        if torch.isnan(loss):
            raise ValueError("Fatal Training Error: Encountered NaN Loss!")

        loss.backward()
        optimizer.step()

        running_loss += loss.item() * inputs.size(0)
        _, preds = torch.max(outputs, 1)
        correct += torch.sum(preds == labels.data).item()
        total += inputs.size(0)

    epoch_loss = running_loss / total
    epoch_acc = (correct / total) * 100.0
    return epoch_loss, epoch_acc


def validate_one_epoch(
    model: nn.Module,
    dataloader: torch.utils.data.DataLoader,
    criterion: nn.Module,
    device: torch.device
) -> Tuple[float, float]:
    """Executes single validation epoch."""
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for inputs, labels in dataloader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            loss = criterion(outputs, labels)

            running_loss += loss.item() * inputs.size(0)
            _, preds = torch.max(outputs, 1)
            correct += torch.sum(preds == labels.data).item()
            total += inputs.size(0)

    epoch_loss = running_loss / total
    epoch_acc = (correct / total) * 100.0
    return epoch_loss, epoch_acc


def train_pipeline(config: TrainingConfig = DEFAULT_TRAINING_CONFIG) -> Dict[str, Any]:
    """Full baseline training execution with early stopping and artifact generation."""
    print("=" * 65)
    print(f"Netra AI - Step 5: Training Baseline Model ({config.model_name})")
    print("=" * 65)

    set_reproducible_seed(config.random_seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[*] Compute Device: {device}")

    # Output and Model Save Directories
    MODEL_SAVE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_TRAIN_DIR.mkdir(parents=True, exist_ok=True)

    config.save_json(OUTPUT_TRAIN_DIR / "training_config.json")

    # Data Paths
    train_csv = PROCESSED_DATA_DIR / "train.csv"
    val_csv = PROCESSED_DATA_DIR / "validation.csv"

    # Datasets and Loaders
    train_loader, val_loader = get_dataloaders(
        train_csv=train_csv,
        val_csv=val_csv,
        batch_size=config.batch_size
    )

    train_df = pd.read_csv(train_csv)
    val_df = pd.read_csv(val_csv)

    print(f"[*] Training Samples: {len(train_df)} | Validation Samples: {len(val_df)}")

    # Class Weighting
    class_weights = calculate_class_weights(train_csv, num_classes=config.num_classes).to(device)
    class_weights_dict = {f"Level_{i}": float(np.round(class_weights[i].item(), 4)) for i in range(5)}
    print(f"[*] Class Weights (from Training Split): {class_weights_dict}")

    # Model & Parameter Count
    model = get_model(num_classes=config.num_classes, pretrained=config.pretrained).to(device)
    total_params, trainable_params = count_parameters(model)
    print(f"[*] Total Parameters: {total_params:,} | Trainable Parameters: {trainable_params:,}")

    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = AdamW(model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay)
    scheduler = CosineAnnealingLR(optimizer, T_max=config.epochs)

    history = {
        "train_loss": [],
        "val_loss": [],
        "train_acc": [],
        "val_acc": [],
    }

    best_val_loss = float("inf")
    best_val_acc = 0.0
    best_epoch = 0
    patience_counter = 0
    early_stopped = False
    best_model_path = MODEL_SAVE_DIR / "best_model.pth"

    print("\n[*] Starting Training Loop...")
    for epoch in range(1, config.epochs + 1):
        tr_loss, tr_acc = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc = validate_one_epoch(model, val_loader, criterion, device)

        scheduler.step()

        history["train_loss"].append(round(tr_loss, 4))
        history["val_loss"].append(round(val_loss, 4))
        history["train_acc"].append(round(tr_acc, 2))
        history["val_acc"].append(round(val_acc, 2))

        print(f"Epoch {epoch:02d}/{config.epochs:02d} - Train Loss: {tr_loss:.4f} | Train Acc: {tr_acc:.2f}% | Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.2f}%")

        # Save Best Model Based on Validation Performance
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_val_acc = val_acc
            best_epoch = epoch
            patience_counter = 0

            # Save state dict
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_loss": val_loss,
                "val_acc": val_acc,
                "config": config.to_dict()
            }, best_model_path)
            print(f"   [+] Saved new best model checkpoint -> {best_model_path.name}")
        else:
            patience_counter += 1
            if patience_counter >= config.early_stopping_patience:
                print(f"\n[!] Early stopping triggered at Epoch {epoch} (No improvement for {config.early_stopping_patience} epochs).")
                early_stopped = True
                break

    # Save History & Plots
    save_training_artifacts(config, history, best_epoch, best_val_loss, best_val_acc, total_params, trainable_params, class_weights_dict, len(train_df), len(val_df), early_stopped)

    results = {
        "model_name": config.model_name,
        "total_parameters": total_params,
        "trainable_parameters": trainable_params,
        "train_samples": len(train_df),
        "val_samples": len(val_df),
        "class_counts_train": train_df["label"].value_counts().to_dict(),
        "class_weights": class_weights_dict,
        "best_epoch": best_epoch,
        "best_val_loss": round(best_val_loss, 4),
        "best_val_accuracy": round(best_val_acc, 2),
        "early_stopping_occurred": early_stopped,
        "saved_model_location": str(best_model_path),
    }

    return results


def save_training_artifacts(
    config: TrainingConfig,
    history: Dict[str, List[float]],
    best_epoch: int,
    best_val_loss: float,
    best_val_acc: float,
    total_params: int,
    trainable_params: int,
    class_weights_dict: Dict[str, float],
    train_count: int,
    val_count: int,
    early_stopped: bool
):
    """Generates training plots and outputs training_summary.md and training_report.json."""
    
    # 1. Save History JSON
    with open(OUTPUT_TRAIN_DIR / "training_history.json", "w") as f:
        json.dump(history, f, indent=2)

    # 2. Loss Curve Plot
    plt.figure(figsize=(7, 5))
    epochs = range(1, len(history["train_loss"]) + 1)
    plt.plot(epochs, history["train_loss"], "o-", label="Train Loss", color="#06b6d4", linewidth=2)
    plt.plot(epochs, history["val_loss"], "s-", label="Validation Loss", color="#f59e0b", linewidth=2)
    plt.axvline(x=best_epoch, color="#10b981", linestyle="--", label=f"Best Epoch ({best_epoch})")
    plt.title("EfficientNet-B0 - Training & Validation Loss Curve", fontsize=12, fontweight="bold")
    plt.xlabel("Epoch")
    plt.ylabel("Weighted CrossEntropy Loss")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.tight_layout()
    plt.savefig(OUTPUT_TRAIN_DIR / "loss_curve.png", dpi=300)
    plt.close()

    # 3. Accuracy Curve Plot
    plt.figure(figsize=(7, 5))
    plt.plot(epochs, history["train_acc"], "o-", label="Train Accuracy", color="#06b6d4", linewidth=2)
    plt.plot(epochs, history["val_acc"], "s-", label="Validation Accuracy", color="#10b981", linewidth=2)
    plt.axvline(x=best_epoch, color="#f59e0b", linestyle="--", label=f"Best Epoch ({best_epoch})")
    plt.title("EfficientNet-B0 - Training & Validation Accuracy Curve", fontsize=12, fontweight="bold")
    plt.xlabel("Epoch")
    plt.ylabel("Accuracy (%)")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.tight_layout()
    plt.savefig(OUTPUT_TRAIN_DIR / "accuracy_curve.png", dpi=300)
    plt.close()

    # 4. Summary Markdown Report
    md_path = OUTPUT_TRAIN_DIR / "training_summary.md"
    with open(md_path, "w") as f:
        f.write("# EfficientNet-B0 Baseline Model Training Report\n\n")
        f.write(f"- **Architecture**: `EfficientNet-B0` (Pretrained Transfer Learning)\n")
        f.write(f"- **Total Parameters**: `{total_params:,}`\n")
        f.write(f"- **Trainable Parameters**: `{trainable_params:,}`\n")
        f.write(f"- **Best Epoch**: `{best_epoch}`\n")
        f.write(f"- **Best Validation Loss**: `{best_val_loss:.4f}`\n")
        f.write(f"- **Best Validation Accuracy**: `{best_val_acc:.2f}%`\n")
        f.write(f"- **Early Stopping Triggered**: `{'Yes' if early_stopped else 'No'}`\n")
        f.write(f"- **Saved Model Weights**: `models/best_model.pth`\n\n")

        f.write("## Hyperparameters & Configuration\n\n")
        f.write(f"- **Optimizer**: `AdamW` (lr={config.learning_rate}, weight_decay={config.weight_decay})\n")
        f.write(f"- **Scheduler**: `CosineAnnealingLR`\n")
        f.write(f"- **Batch Size**: `{config.batch_size}`\n")
        f.write(f"- **Random Seed**: `{config.random_seed}`\n")
        f.write(f"- **Input Image Dimensions**: `{config.image_size[0]}x{config.image_size[1]}x3`\n\n")

        f.write("## Training Set Class Weights\n\n")
        f.write("| Level | DR Diagnosis | Weight |\n| --- | --- | --- |\n")
        for k, name in DR_CLASSES.items():
            f.write(f"| Level {k} | {name} | {class_weights_dict[f'Level_{k}']} |\n")

    print(f"[+] Saved Training Artifacts & Plots to {OUTPUT_TRAIN_DIR}")


if __name__ == "__main__":
    train_pipeline()
