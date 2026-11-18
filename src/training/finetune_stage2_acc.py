"""
Stage-2 full-network fine-tuning of EfficientNet-B0 on APTOS 2019 + DDR.

Starts from the Stage-1 checkpoint (copied to models/best_model_aptos_ddr_stage1.pth
for preservation), unfreezes all layers (including early blocks features.0..3),
relaxes heavy class weights to gentle power=0.20 + ordinal MSE regularization,
and saves the improved high-accuracy checkpoint to models/best_model_aptos_ddr.pth.
"""

import json
import shutil
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.training.dataset import FundusDataset
from src.training.model import count_parameters, get_model
from src.training.train_aptos_ddr import (
    build_transforms,
    compute_epoch_metrics,
    compute_smoothed_class_weights,
    save_training_curves,
    set_seed,
)


class HybridOrdinalCrossEntropyLoss(nn.Module):
    """Cross-entropy with gentle class weights plus expected-grade ordinal MSE."""

    def __init__(
        self,
        class_weights: torch.Tensor,
        label_smoothing: float = 0.02,
        ordinal_weight: float = 0.15,
    ) -> None:
        super().__init__()
        self.ce = nn.CrossEntropyLoss(weight=class_weights, label_smoothing=label_smoothing)
        self.ordinal_weight = ordinal_weight
        self.register_buffer("grades", torch.arange(5, dtype=torch.float32))

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        ce_val = self.ce(logits, targets)
        probs = F.softmax(logits, dim=1)
        expected_grade = (probs * self.grades.unsqueeze(0)).sum(dim=1)
        ord_mse = F.mse_loss(expected_grade, targets.float())
        return ce_val + self.ordinal_weight * ord_mse


def train_one_epoch_stage2(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    epoch_idx: int,
    total_epochs: int,
) -> Tuple[float, Dict[str, float]]:
    """Run one Stage-2 training epoch across all unfrozen layers."""
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
                f"  Stage2 Epoch {epoch_idx}/{total_epochs} | Batch {b_idx}/{n_batches} | "
                f"Loss: {avg_loss:.4f} | Elapsed: {elapsed:.1f}s | ETA: {eta:.1f}s"
            )

    metrics = compute_epoch_metrics(y_true, y_pred)
    return running_loss / max(total_samples, 1), metrics


@torch.no_grad()
def validate_stage2(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> Tuple[float, Dict[str, float]]:
    """Evaluate Stage-2 model on validation dataloader."""
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


def main() -> None:
    set_seed(42)
    cpu_threads = 12
    torch.set_num_threads(cpu_threads)
    device = torch.device("cpu")

    data_dir = ROOT_DIR / "data" / "processed_combined"
    train_csv = data_dir / "train.csv"
    val_csv = data_dir / "validation.csv"

    out_dir = ROOT_DIR / "outputs" / "training_aptos_ddr_stage2"
    out_dir.mkdir(parents=True, exist_ok=True)

    main_ckpt = ROOT_DIR / "models" / "best_model_aptos_ddr.pth"
    stage1_backup = ROOT_DIR / "models" / "best_model_aptos_ddr_stage1.pth"
    if not stage1_backup.exists():
        shutil.copy2(main_ckpt, stage1_backup)
        print(f"Preserved Stage-1 checkpoint at {stage1_backup}")

    batch_size = 64
    epochs = 4
    early_stopping_patience = 2

    train_tf, val_tf = build_transforms(image_size=224)
    train_ds = FundusDataset(train_csv, is_training=True, transform=train_tf)
    val_ds = FundusDataset(val_csv, is_training=False, transform=val_tf)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=0)

    class_weights, train_counts = compute_smoothed_class_weights(train_csv, num_classes=5, power=0.20)
    criterion = HybridOrdinalCrossEntropyLoss(
        class_weights=class_weights.to(device),
        label_smoothing=0.02,
        ordinal_weight=0.15,
    ).to(device)

    model = get_model(num_classes=5, pretrained=False)
    ckpt = torch.load(stage1_backup, map_location=device, weights_only=False)
    model.load_state_dict(ckpt["model_state_dict"])
    for param in model.parameters():
        param.requires_grad = True
    model.to(device)

    total_params, trainable_params = count_parameters(model)
    optimizer = AdamW(
        [
            {"params": model.features[:4].parameters(), "lr": 1.0e-4},
            {"params": model.features[4:].parameters(), "lr": 1.5e-4},
            {"params": model.classifier.parameters(), "lr": 3.0e-4},
        ],
        weight_decay=1e-4,
    )
    scheduler = CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)

    stage1_val_loss, stage1_val_m = validate_stage2(model, val_loader, criterion, device)
    print(
        f"Stage-1 baseline on validation: Acc={stage1_val_m['accuracy']*100:.2f}% "
        f"MacroF1={stage1_val_m['macro_f1']:.4f} RefSens={stage1_val_m['referable_sensitivity']:.4f} "
        f"RefSpec={stage1_val_m['referable_specificity']:.4f}"
    )

    config_summary = {
        "stage": "stage2_full_unfreeze_accuracy_finetune",
        "init_checkpoint": "models/best_model_aptos_ddr_stage1.pth",
        "output_checkpoint": "models/best_model_aptos_ddr.pth",
        "total_parameters": total_params,
        "trainable_parameters": trainable_params,
        "batch_size": batch_size,
        "epochs_max": epochs,
        "optimizer": "AdamW(differential lr: features[:4]=1e-4, features[4:]=1.5e-4, classifier=3e-4)",
        "scheduler": "CosineAnnealingLR(eta_min=1e-5)",
        "loss": "CrossEntropyLoss(power_0.20_weights, ls=0.02) + 0.15 * OrdinalExpectedMSE",
        "class_weights": [round(float(w), 4) for w in class_weights.tolist()],
        "selection_metric": "val_accuracy (breaking ties by val_macro_f1)",
        "stage1_val_accuracy": round(stage1_val_m["accuracy"], 4),
        "stage1_val_macro_f1": round(stage1_val_m["macro_f1"], 4),
    }
    with open(out_dir / "training_config.json", "w", encoding="utf-8") as f:
        json.dump(config_summary, f, indent=2)

    history: List[Dict[str, Any]] = []
    best_val_acc = stage1_val_m["accuracy"]
    best_epoch = 0
    no_improve = 0
    total_start = time.time()

    for epoch in range(1, epochs + 1):
        ep_start = time.time()
        print(f"\n--- Stage-2 Epoch {epoch}/{epochs} (LR backbone={optimizer.param_groups[1]['lr']:.6f}) ---")
        train_loss, train_m = train_one_epoch_stage2(
            model, train_loader, criterion, optimizer, device, epoch, epochs
        )
        val_loss, val_m = validate_stage2(model, val_loader, criterion, device)
        scheduler.step()

        ep_duration = time.time() - ep_start
        record = {
            "epoch": epoch,
            "lr_mid": float(optimizer.param_groups[1]["lr"]),
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
        with open(out_dir / "training_history.json", "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)

        print(
            f"[Stage-2 Epoch {epoch} | {ep_duration:.1f}s] "
            f"Train Acc: {train_m['accuracy']*100:.2f}% F1: {train_m['macro_f1']:.4f} | "
            f"Val Acc: {val_m['accuracy']*100:.2f}% F1: {val_m['macro_f1']:.4f} "
            f"RefSens: {val_m['referable_sensitivity']:.4f} RefSpec: {val_m['referable_specificity']:.4f}"
        )

        if val_m["accuracy"] > best_val_acc:
            best_val_acc = val_m["accuracy"]
            best_epoch = epoch
            no_improve = 0
            torch.save(
                {
                    "epoch": f"stage2_ep{epoch}",
                    "model_state_dict": model.state_dict(),
                    "val_accuracy": float(val_m["accuracy"]),
                    "val_macro_f1": float(val_m["macro_f1"]),
                    "val_loss": float(val_loss),
                    "config": config_summary,
                },
                main_ckpt,
            )
            print(f"  -> Promoted new best checkpoint (val_accuracy={best_val_acc*100:.2f}%)")
        else:
            no_improve += 1
            print(f"  -> No val_accuracy improvement over {best_val_acc*100:.2f}% ({no_improve}/{early_stopping_patience})")
            if no_improve >= early_stopping_patience:
                print(f"Early stopping Stage 2 at epoch {epoch}.")
                break

    total_duration = time.time() - total_start
    save_training_curves(history, out_dir / "training_curves.png")
    summary = {
        "best_stage2_epoch": best_epoch,
        "best_val_accuracy": round(best_val_acc, 4),
        "stage1_val_accuracy": round(stage1_val_m["accuracy"], 4),
        "epochs_completed": len(history),
        "total_duration_minutes": round(total_duration / 60.0, 2),
    }
    with open(out_dir / "training_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\n=== Stage-2 Complete in {total_duration/60.0:.2f} min ===")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

