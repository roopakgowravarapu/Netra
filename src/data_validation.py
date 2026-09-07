"""
Netra - Step 2: Dataset Acquisition & Validation Script
Target: APTOS 2019 Blindness Detection (Diabetic Retinopathy 5-Class Severity Classification)

This script validates raw fundus image data under data/raw/aptos/ without modifying files or training models.
"""

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image

try:
    import cv2
except ImportError:
    cv2 = None

try:
    import imagehash
except ImportError:
    imagehash = None

# Base Directory Paths
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data" / "raw" / "aptos"
OUTPUT_DIR = ROOT_DIR / "outputs" / "dataset_report"

# Supported image file extensions
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}

# DR Class Mapping
DR_CLASSES = {
    0: "No DR",
    1: "Mild",
    2: "Moderate",
    3: "Severe",
    4: "Proliferative DR",
}


def compute_file_md5(file_path: Path) -> str:
    """Compute MD5 checksum for exact file duplicate detection."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def find_dataset_files(data_path: Path) -> Tuple[Path, Path]:
    """
    Locate label CSV file and image directory under data/raw/aptos/.
    Returns (csv_path, image_dir).
    """
    possible_csvs = list(data_path.glob("*.csv"))
    csv_path = possible_csvs[0] if possible_csvs else None

    # Check for train_images directory or images directly in data_path
    if (data_path / "train_images").exists() and (data_path / "train_images").is_dir():
        image_dir = data_path / "train_images"
    elif (data_path / "images").exists() and (data_path / "images").is_dir():
        image_dir = data_path / "images"
    else:
        image_dir = data_path

    return csv_path, image_dir


def validate_dataset() -> Dict[str, Any]:
    """Execute comprehensive 12-point dataset validation."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    report: Dict[str, Any] = {
        "dataset_name": "APTOS 2019 Blindness Detection",
        "dataset_location": str(DATA_DIR),
        "dataset_source": "https://www.kaggle.com/c/aptos2019-blindness-detection/data",
        "validation_passed": False,
        "total_images_on_disk": 0,
        "csv_total_rows": 0,
        "class_counts": {str(k): 0 for k in DR_CLASSES.keys()},
        "missing_images_count": 0,
        "missing_images_list": [],
        "corrupted_images_count": 0,
        "corrupted_images_list": [],
        "unsupported_format_count": 0,
        "unsupported_format_list": [],
        "invalid_labels_count": 0,
        "invalid_labels_list": [],
        "exact_duplicates_count": 0,
        "perceptual_duplicates_count": 0,
        "dimension_stats": {},
        "problems_found": [],
    }

    csv_path, image_dir = find_dataset_files(DATA_DIR)

    # Check if dataset files exist
    if not csv_path or not csv_path.exists():
        msg = f"Label CSV file (e.g. train.csv) not found in {DATA_DIR}."
        print(f"[!] {msg}")
        report["problems_found"].append(msg)
        save_reports_and_visualizations(report, None, {})
        return report

    # 1. Read Label CSV
    print(f"[*] Reading label CSV: {csv_path.name}")
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        msg = f"Failed to parse label CSV {csv_path}: {e}"
        print(f"[!] {msg}")
        report["problems_found"].append(msg)
        return report

    report["csv_total_rows"] = len(df)

    # Determine ID and Diagnosis column names
    id_col = "id_code" if "id_code" in df.columns else df.columns[0]
    diag_col = "diagnosis" if "diagnosis" in df.columns else (df.columns[1] if len(df.columns) > 1 else None)

    if diag_col is None:
        msg = "CSV does not contain a diagnosis label column."
        report["problems_found"].append(msg)
        return report

    # 2. Count images on disk
    all_image_files = [f for f in image_dir.glob("*") if f.is_file() and not f.name.startswith(".")]
    report["total_images_on_disk"] = len(all_image_files)
    print(f"[*] Found {len(all_image_files)} image files in {image_dir}")

    # 3. Detect unsupported image formats
    for f in all_image_files:
        if f.suffix.lower() not in SUPPORTED_EXTENSIONS:
            report["unsupported_format_count"] += 1
            report["unsupported_format_list"].append(f.name)

    if report["unsupported_format_count"] > 0:
        report["problems_found"].append(f"Found {report['unsupported_format_count']} unsupported image file formats.")

    # 4. Check for invalid labels
    for idx, row in df.iterrows():
        label_val = row[diag_col]
        try:
            val_int = int(label_val)
            if val_int not in DR_CLASSES:
                report["invalid_labels_count"] += 1
                report["invalid_labels_list"].append({"row": idx, "id_code": str(row[id_col]), "value": label_val})
            else:
                report["class_counts"][str(val_int)] += 1
        except (ValueError, TypeError):
            report["invalid_labels_count"] += 1
            report["invalid_labels_list"].append({"row": idx, "id_code": str(row[id_col]), "value": label_val})

    if report["invalid_labels_count"] > 0:
        report["problems_found"].append(f"Found {report['invalid_labels_count']} invalid label entries in CSV.")

    # 5. Check missing images and image integrity
    widths: List[int] = []
    heights: List[int] = []
    aspect_ratios: List[float] = []
    channels_list: List[int] = []
    
    md5_hashes: Dict[str, str] = {}
    phashes: Dict[str, str] = {}
    exact_dup_pairs: List[Tuple[str, str]] = []

    print("[*] Validating image accessibility, file integrity, and dimensions...")
    
    valid_samples_per_class: Dict[int, List[Path]] = {c: [] for c in DR_CLASSES.keys()}

    for idx, row in df.iterrows():
        id_code = str(row[id_col]).strip()
        label = row[diag_col]

        # Resolve image path (support with or without extension in CSV)
        img_path = image_dir / id_code
        if not img_path.exists():
            for ext in SUPPORTED_EXTENSIONS:
                if (image_dir / f"{id_code}{ext}").exists():
                    img_path = image_dir / f"{id_code}{ext}"
                    break

        if not img_path.exists():
            report["missing_images_count"] += 1
            report["missing_images_list"].append(id_code)
            continue

        # Check image corruption and extract dimensions
        try:
            with Image.open(img_path) as img:
                img.verify()  # Verify image structure
                
            # Reopen to get size and channels
            with Image.open(img_path) as img:
                w, h = img.size
                mode = img.mode
                c = len(img.getbands())
                widths.append(w)
                heights.append(h)
                aspect_ratios.append(round(w / h, 3))
                channels_list.append(c)

            # Store for sample visualizations
            try:
                lbl_int = int(label)
                if lbl_int in valid_samples_per_class and len(valid_samples_per_class[lbl_int]) < 4:
                    valid_samples_per_class[lbl_int].append(img_path)
            except Exception:
                pass

            # Duplicate detection (MD5)
            file_md5 = compute_file_md5(img_path)
            if file_md5 in md5_hashes:
                report["exact_duplicates_count"] += 1
                exact_dup_pairs.append((img_path.name, md5_hashes[file_md5]))
            else:
                md5_hashes[file_md5] = img_path.name

        except Exception as err:
            report["corrupted_images_count"] += 1
            report["corrupted_images_list"].append({"file": img_path.name, "error": str(err)})

    if report["missing_images_count"] > 0:
        report["problems_found"].append(f"Found {report['missing_images_count']} missing images referenced in CSV.")
    if report["corrupted_images_count"] > 0:
        report["problems_found"].append(f"Found {report['corrupted_images_count']} corrupted/unreadable image files.")

    # 6. Dimension Statistics
    if widths:
        report["dimension_stats"] = {
            "min_width": int(np.min(widths)),
            "max_width": int(np.max(widths)),
            "mean_width": float(np.round(np.mean(widths), 2)),
            "min_height": int(np.min(heights)),
            "max_height": int(np.max(heights)),
            "mean_height": float(np.round(np.mean(heights), 2)),
            "mean_aspect_ratio": float(np.round(np.mean(aspect_ratios), 3)),
            "channels_distribution": pd.Series(channels_list).value_counts().to_dict(),
        }

    # Pass/Fail determination
    if (
        report["missing_images_count"] == 0
        and report["corrupted_images_count"] == 0
        and report["invalid_labels_count"] == 0
        and report["unsupported_format_count"] == 0
        and report["csv_total_rows"] > 0
    ):
        report["validation_passed"] = True

    # 7. Generate Visualizations and Output Reports
    save_reports_and_visualizations(report, df, valid_samples_per_class)

    return report


def save_reports_and_visualizations(
    report: Dict[str, Any],
    df: Any,
    samples_per_class: Dict[int, List[Path]],
):
    """Generate plots and report artifacts under outputs/dataset_report/."""

    # 1. JSON Report
    json_path = OUTPUT_DIR / "dataset_validation_report.json"
    with open(json_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"[+] Saved JSON report: {json_path}")

    # 2. Class Distribution Bar Chart
    plt.figure(figsize=(8, 5))
    classes = [f"Level {k}\n({DR_CLASSES[k]})" for k in DR_CLASSES.keys()]
    counts = [report["class_counts"][str(k)] for k in DR_CLASSES.keys()]
    colors = ["#10b981", "#06b6d4", "#3b82f6", "#f59e0b", "#ef4444"]

    bars = plt.bar(classes, counts, color=colors, edgecolor="black", linewidth=0.8)
    plt.title("APTOS 2019 - Diabetic Retinopathy Class Distribution", fontsize=12, fontweight="bold", pad=12)
    plt.xlabel("DR Severity Level", fontsize=10)
    plt.ylabel("Number of Fundus Images", fontsize=10)
    plt.grid(axis="y", linestyle="--", alpha=0.5)

    for bar, count in zip(bars, counts):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 15, str(count), ha="center", va="bottom", fontsize=9, fontweight="bold")

    plt.tight_layout()
    dist_chart_path = OUTPUT_DIR / "class_distribution.png"
    plt.savefig(dist_chart_path, dpi=300)
    plt.close()
    print(f"[+] Saved class distribution graph: {dist_chart_path}")

    # 3. Sample Images Grid per Class
    if samples_per_class and any(samples_per_class.values()):
        fig, axes = plt.subplots(5, 4, figsize=(12, 14))
        fig.suptitle("APTOS 2019 - Sample Fundus Images per DR Class", fontsize=14, fontweight="bold", y=0.98)

        for row_idx, (class_id, class_name) in enumerate(DR_CLASSES.items()):
            img_paths = samples_per_class.get(class_id, [])
            for col_idx in range(4):
                ax = axes[row_idx, col_idx]
                if col_idx < len(img_paths):
                    try:
                        img = Image.open(img_paths[col_idx])
                        ax.imshow(img)
                        ax.set_title(f"L{class_id} ({img_paths[col_idx].stem})", fontsize=8)
                    except Exception:
                        ax.text(0.5, 0.5, "Error loading", ha="center", va="center")
                else:
                    ax.text(0.5, 0.5, "N/A", ha="center", va="center", color="gray")

                ax.axis("off")

            # Add row title
            axes[row_idx, 0].set_ylabel(f"Level {class_id}\n{class_name}", fontsize=9, fontweight="bold", rotation=0, labelpad=40, ha="right", va="center")

        plt.tight_layout(rect=[0.05, 0, 1, 0.96])
        sample_grid_path = OUTPUT_DIR / "sample_images_per_class.png"
        plt.savefig(sample_grid_path, dpi=200)
        plt.close()
        print(f"[+] Saved sample images grid: {sample_grid_path}")

    # 4. Markdown Summary Report
    md_path = OUTPUT_DIR / "dataset_summary.md"
    with open(md_path, "w") as f:
        f.write("# APTOS 2019 Dataset Validation Summary\n\n")
        f.write(f"- **Source**: `{report['dataset_source']}`\n")
        f.write(f"- **Location**: `{report['dataset_location']}`\n")
        f.write(f"- **Validation Status**: **{'PASSED' if report['validation_passed'] else 'NEEDS ATTENTION'}**\n\n")

        f.write("## Quantitative Breakdown\n\n")
        f.write(f"| Metric | Count |\n| --- | --- |\n")
        f.write(f"| CSV Label Entries | {report['csv_total_rows']} |\n")
        f.write(f"| Images on Disk | {report['total_images_on_disk']} |\n")
        f.write(f"| Missing Images | {report['missing_images_count']} |\n")
        f.write(f"| Corrupted Images | {report['corrupted_images_count']} |\n")
        f.write(f"| Invalid Labels | {report['invalid_labels_count']} |\n")
        f.write(f"| Unsupported Formats | {report['unsupported_format_count']} |\n")
        f.write(f"| Exact Duplicate Files | {report['exact_duplicates_count']} |\n\n")

        f.write("## Class Distribution (DR Severity Levels 0–4)\n\n")
        f.write("| Level | DR Diagnosis | Samples | Percentage |\n| --- | --- | --- | --- |\n")
        tot = report['csv_total_rows'] if report['csv_total_rows'] > 0 else 1
        for k, v in DR_CLASSES.items():
            cnt = report['class_counts'][str(k)]
            pct = round((cnt / tot) * 100, 2)
            f.write(f"| {k} | {v} | {cnt} | {pct}% |\n")

    print(f"[+] Saved Markdown summary: {md_path}")


if __name__ == "__main__":
    print("=" * 60)
    print("Netra AI - Step 2: APTOS 2019 Dataset Validation Pipeline")
    print("=" * 60)
    res = validate_dataset()
    print("=" * 60)
    print(f"Validation Finished! Passed: {res['validation_passed']}")
    print(f"Problems Found: {len(res['problems_found'])}")
    print("=" * 60)
