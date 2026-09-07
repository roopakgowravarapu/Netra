import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2
import numpy as np
import pandas as pd
from PIL import Image
from src.preprocessing.config import DEFAULT_CONFIG
from src.preprocessing.preprocess import preprocess_single_image

ROOT_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DATA_DIR = ROOT_DIR / "data" / "processed"
SPLITS_DIR = ROOT_DIR / "data" / "processed" / "splits"


def test_single_image_preprocessing_pipeline():
    """Test preprocessing on a synthetic test image."""
    dummy_img = np.random.randint(0, 256, (500, 500, 3), dtype=np.uint8)
    processed = preprocess_single_image(dummy_img, DEFAULT_CONFIG)

    # Check expected target dimensions (224, 224, 3)
    target_w, target_h = DEFAULT_CONFIG.target_size
    assert processed.shape == (target_h, target_w, 3)

    # Check pixel value validity and absence of NaN / Inf
    assert not np.isnan(processed).any()
    assert not np.isinf(processed).any()
    assert np.min(processed) >= 0
    assert np.max(processed) <= 255


def test_processed_split_csv_existence_and_counts():
    """Verify processed split CSV manifests and total row counts."""
    split_names = ["train", "validation", "test"]
    expected_counts = {"train": 2563, "validation": 549, "test": 550}

    total_count = 0
    for split in split_names:
        csv_path = PROCESSED_DATA_DIR / f"{split}.csv"
        assert csv_path.exists(), f"Processed CSV for {split} missing."

        df = pd.read_csv(csv_path)
        assert len(df) == expected_counts[split], f"Row count mismatch in {split}."
        assert "processed_image_path" in df.columns
        assert "label" in df.columns
        total_count += len(df)

    assert total_count == 3662, "Total processed count mismatch."


def test_processed_images_file_integrity():
    """Verify that all processed images on disk exist, are uncorrupted, and have valid pixels."""
    split_names = ["train", "validation", "test"]
    target_w, target_h = DEFAULT_CONFIG.target_size

    for split in split_names:
        csv_path = PROCESSED_DATA_DIR / f"{split}.csv"
        df = pd.read_csv(csv_path)

        for _, row in df.iterrows():
            img_rel_path = str(row["processed_image_path"])
            img_full_path = ROOT_DIR / img_rel_path

            assert img_full_path.exists(), f"Processed image file missing: {img_full_path}"

            img_bgr = cv2.imread(str(img_full_path))
            assert img_bgr is not None, f"Corrupted processed image: {img_full_path}"
            assert img_bgr.shape == (target_h, target_w, 3), f"Dimension mismatch in {img_full_path}"
            assert not np.isnan(img_bgr).any()
            assert not np.isinf(img_bgr).any()


def test_label_preservation_and_no_data_leakage():
    """Verify labels match raw splits and no data leakage exists across splits."""
    split_names = ["train", "validation", "test"]
    split_paths = {}

    for split in split_names:
        raw_csv = SPLITS_DIR / f"{split}.csv"
        proc_csv = PROCESSED_DATA_DIR / f"{split}.csv"

        raw_df = pd.read_csv(raw_csv)
        proc_df = pd.read_csv(proc_csv)

        # Label preservation check
        np.testing.assert_array_equal(
            raw_df["label"].values,
            proc_df["label"].values,
            err_msg=f"Labels altered in {split} split!"
        )

        split_paths[split] = set(proc_df["processed_image_path"])

    # Zero data leakage check
    overlap_train_val = len(split_paths["train"].intersection(split_paths["validation"]))
    overlap_train_test = len(split_paths["train"].intersection(split_paths["test"]))
    overlap_val_test = len(split_paths["validation"].intersection(split_paths["test"]))

    assert overlap_train_val == 0, "Data leakage detected between train and validation!"
    assert overlap_train_test == 0, "Data leakage detected between train and test!"
    assert overlap_val_test == 0, "Data leakage detected between validation and test!"
