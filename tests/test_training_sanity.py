import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import torch
import torch.nn as nn
from src.training.config import DEFAULT_TRAINING_CONFIG
from src.training.dataset import FundusDataset, get_dataloaders, calculate_class_weights
from src.training.model import get_model, count_parameters

ROOT_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DATA_DIR = ROOT_DIR / "data" / "processed"
SPLITS_DIR = ROOT_DIR / "data" / "processed" / "splits"


def test_dataset_classes_and_label_validity():
    """Verify all five DR classes are present and labels are valid in [0, 4]."""
    train_csv = PROCESSED_DATA_DIR / "train.csv"
    val_csv = PROCESSED_DATA_DIR / "validation.csv"

    for csv_path, name in [(train_csv, "train"), (val_csv, "validation")]:
        df = pd.read_csv(csv_path)
        labels = set(df["label"].unique())
        assert labels == {0, 1, 2, 3, 4}, f"Class mismatch in {name} split."
        assert df["label"].isin([0, 1, 2, 3, 4]).all(), f"Invalid label values in {name} split."


def test_no_test_set_leakage_in_training_dataloader():
    """Verify no test images are loaded by training or validation dataloaders."""
    test_csv = PROCESSED_DATA_DIR / "test.csv"
    test_df = pd.read_csv(test_csv)
    test_paths = set(test_df["processed_image_path"])

    train_ds = FundusDataset(PROCESSED_DATA_DIR / "train.csv")
    val_ds = FundusDataset(PROCESSED_DATA_DIR / "validation.csv")

    train_paths = set(train_ds.df["processed_image_path"])
    val_paths = set(val_ds.df["processed_image_path"])

    assert len(train_paths.intersection(test_paths)) == 0, "Test set leakage detected in train dataset!"
    assert len(val_paths.intersection(test_paths)) == 0, "Test set leakage detected in validation dataset!"


def test_model_output_shape_and_classes():
    """Verify EfficientNet-B0 outputs exactly 5 logits for arbitrary batch sizes."""
    model = get_model(num_classes=5, pretrained=False)
    model.eval()

    dummy_batch = torch.randn(4, 3, 224, 224)
    with torch.no_grad():
        output = model(dummy_batch)

    assert output.shape == (4, 5), f"Model output shape mismatch: {output.shape}"
    assert not torch.isnan(output).any(), "NaN values found in model output logits."


def test_batch_shapes_and_weighted_loss_computation():
    """Verify batch shape from dataloader and test weighted CrossEntropy loss calculation."""
    train_loader, _ = get_dataloaders(batch_size=8)
    images, labels = next(iter(train_loader))

    assert images.shape == (8, 3, 224, 224), f"Batch shape mismatch: {images.shape}"
    assert labels.shape == (8,), f"Labels shape mismatch: {labels.shape}"

    weights = calculate_class_weights(PROCESSED_DATA_DIR / "train.csv", num_classes=5)
    criterion = nn.CrossEntropyLoss(weight=weights)

    model = get_model(num_classes=5, pretrained=False)
    outputs = model(images)
    loss = criterion(outputs, labels)

    assert not torch.isnan(loss).item(), "NaN loss encountered in weighted loss computation!"
    assert loss.item() > 0, "Loss should be strictly positive."
