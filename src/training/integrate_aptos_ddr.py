"""
Integrate APTOS 2019 and DDR DR_grading datasets into a deduplicated,
leakage-free combined training pipeline, and prepare the SUSTech-SYSU
external validation manifest.

Preserves all original raw datasets under data/raw/ and existing synthetic
artifacts under data/processed/. Writes processed 224x224 RGB PNGs and
split manifests to data/processed_combined/.
"""

import hashlib
import json
import re
import shutil
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.preprocessing.config import DEFAULT_CONFIG
from src.preprocessing.preprocess import preprocess_single_image

APTOS_FOLDER_MAP = {
    0: "No_DR",
    1: "Mild",
    2: "Moderate",
    3: "Severe",
    4: "Proliferate_DR",
}

TIMESTAMP_RE = re.compile(r"^(\d{14})(\d{3})\.[a-zA-Z]+$")
_POPCOUNT_LUT = np.array([bin(i).count("1") for i in range(256)], dtype=np.uint8)


class UnionFind:
    """Disjoint-set data structure for clustering duplicate and same-visit images."""

    def __init__(self, n: int) -> None:
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1


def compute_file_sha256_and_dhash256(img_path: Path) -> Tuple[str, np.ndarray]:
    """Compute byte-level SHA-256 hex digest and 256-bit center-crop dHash (4 x uint64)."""
    data = img_path.read_bytes()
    sha256 = hashlib.sha256(data).hexdigest()

    arr = np.frombuffer(data, dtype=np.uint8)
    gray = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
    if gray is None:
        raise ValueError(f"Failed to decode image for dHash: {img_path}")
    h, w = gray.shape
    crop = gray[int(0.22 * h) : int(0.78 * h), int(0.22 * w) : int(0.78 * w)]
    resized = cv2.resize(crop, (17, 16), interpolation=cv2.INTER_AREA)
    diff = (resized[:, 1:] > resized[:, :-1]).flatten()
    words = np.packbits(diff).view(np.uint64).copy()
    return sha256, words


def dhash256_hex(words: np.ndarray) -> str:
    """Format 4 x uint64 dHash words as a 64-char hex string."""
    return words.tobytes().hex()


def pairwise_hamming_256(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Compute (len(a), len(b)) Hamming distance matrix for 256-bit dHashes."""
    xor = np.bitwise_xor(a[:, None, :], b[None, :, :])
    return _POPCOUNT_LUT[xor.view(np.uint8)].reshape(len(a), len(b), 32).sum(axis=2)


def load_raw_records() -> List[Dict[str, Any]]:
    """Load APTOS 2019 and DDR DR_grading metadata records."""
    records: List[Dict[str, Any]] = []

    aptos_csv = ROOT_DIR / "data" / "raw" / "aptos" / "train.csv"
    aptos_df = pd.read_csv(aptos_csv)
    for _, row in aptos_df.iterrows():
        label = int(row["diagnosis"])
        id_code = str(row["id_code"]).strip()
        folder = APTOS_FOLDER_MAP[label]
        img_path = ROOT_DIR / "data" / "raw" / "aptos" / "colored_images" / folder / f"{id_code}.png"
        if not img_path.exists():
            raise FileNotFoundError(f"Missing APTOS image: {img_path}")
        records.append(
            {
                "source_dataset": "APTOS_2019",
                "sample_id": id_code,
                "label": label,
                "rel_path": str(img_path.relative_to(ROOT_DIR)).replace("\\", "/"),
                "abs_path": img_path,
                "ddr_timestamp_sec": None,
            }
        )

    ddr_csv = ROOT_DIR / "data" / "raw" / "DR_grading.csv"
    ddr_df = pd.read_csv(ddr_csv)
    for _, row in ddr_df.iterrows():
        label = int(row["diagnosis"])
        id_code = str(row["id_code"]).strip()
        img_path = ROOT_DIR / "data" / "raw" / "DR_grading" / "DR_grading" / id_code
        if not img_path.exists():
            raise FileNotFoundError(f"Missing DDR image: {img_path}")

        ts_sec: Optional[float] = None
        match = TIMESTAMP_RE.match(id_code)
        if match:
            dt = datetime.strptime(match.group(1), "%Y%m%d%H%M%S")
            ms = int(match.group(2))
            ts_sec = dt.timestamp() + ms / 1000.0

        records.append(
            {
                "source_dataset": "DDR",
                "sample_id": Path(id_code).stem,
                "label": label,
                "rel_path": str(img_path.relative_to(ROOT_DIR)).replace("\\", "/"),
                "abs_path": img_path,
                "ddr_timestamp_sec": ts_sec,
            }
        )

    return records


def deduplicate_exact_sha256(
    records: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Drop exact-byte duplicate groups that carry conflicting labels, and
    collapse non-conflicting exact duplicates to one canonical representative.
    """
    by_hash: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for rec in records:
        by_hash[rec["sha256"]].append(rec)

    kept: List[Dict[str, Any]] = []
    conflicting_groups = 0
    conflicting_images_dropped = 0
    consistent_dup_groups = 0
    consistent_dup_images_removed = 0
    cross_dataset_exact_dups = 0

    for sha, group in by_hash.items():
        sources = {g["source_dataset"] for g in group}
        if len(sources) > 1:
            cross_dataset_exact_dups += 1

        labels = {g["label"] for g in group}
        if len(labels) > 1:
            conflicting_groups += 1
            conflicting_images_dropped += len(group)
            continue

        if len(group) > 1:
            consistent_dup_groups += 1
            consistent_dup_images_removed += len(group) - 1

        group_sorted = sorted(group, key=lambda r: (r["source_dataset"], r["rel_path"]))
        kept.append(group_sorted[0])

    kept.sort(key=lambda r: (r["source_dataset"], r["rel_path"]))

    stats = {
        "total_raw_images": len(records),
        "unique_sha256_hashes": len(by_hash),
        "cross_dataset_exact_sha256_groups": cross_dataset_exact_dups,
        "conflicting_label_sha256_groups_dropped": conflicting_groups,
        "conflicting_label_images_dropped": conflicting_images_dropped,
        "consistent_duplicate_groups_collapsed": consistent_dup_groups,
        "consistent_duplicate_images_removed": consistent_dup_images_removed,
        "images_after_exact_dedup": len(kept),
    }
    return kept, stats


def build_leakage_clusters(
    records: List[Dict[str, Any]],
    dhash_threshold: int = 16,
    ddr_visit_window_sec: float = 15.0,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Cluster near-duplicate images (256-bit center-crop dHash Hamming <= dhash_threshold)
    and DDR consecutive timestamp pairs (<= ddr_visit_window_sec apart) into groups.
    """
    n = len(records)
    uf = UnionFind(n)

    dhashes = np.vstack([r["dhash"] for r in records])  # (N, 4) uint64
    near_dup_edges = 0
    cross_dataset_near_dups = 0

    chunk_size = 128
    for start in range(0, n, chunk_size):
        end = min(start + chunk_size, n)
        dists = pairwise_hamming_256(dhashes[start:end], dhashes)
        rows = np.arange(start, end)[:, None]
        cols = np.arange(n)[None, :]
        hit = (cols > rows) & (dists <= dhash_threshold)
        if hit.any():
            hi, hj = np.nonzero(hit)
            for r_off, col_j in zip(hi.tolist(), hj.tolist()):
                i = start + r_off
                uf.union(i, col_j)
                near_dup_edges += 1
                if records[i]["source_dataset"] != records[col_j]["source_dataset"]:
                    cross_dataset_near_dups += 1

    ddr_ts_indices = [
        (rec["ddr_timestamp_sec"], idx)
        for idx, rec in enumerate(records)
        if rec["source_dataset"] == "DDR" and rec["ddr_timestamp_sec"] is not None
    ]
    ddr_ts_indices.sort(key=lambda x: x[0])
    ddr_visit_edges = 0
    for k in range(1, len(ddr_ts_indices)):
        prev_ts, prev_idx = ddr_ts_indices[k - 1]
        curr_ts, curr_idx = ddr_ts_indices[k]
        if (curr_ts - prev_ts) <= ddr_visit_window_sec:
            uf.union(prev_idx, curr_idx)
            ddr_visit_edges += 1

    root_to_gid: Dict[int, int] = {}
    group_sizes: Counter = Counter()
    for idx, rec in enumerate(records):
        root = uf.find(idx)
        if root not in root_to_gid:
            root_to_gid[root] = len(root_to_gid)
        gid = root_to_gid[root]
        rec["group_id"] = gid
        group_sizes[gid] += 1

    cluster_stats = {
        "dhash_bits": 256,
        "dhash_hamming_threshold": dhash_threshold,
        "ddr_visit_window_seconds": ddr_visit_window_sec,
        "near_duplicate_pairs_linked": near_dup_edges,
        "cross_dataset_near_duplicate_pairs": cross_dataset_near_dups,
        "ddr_visit_pairs_linked": ddr_visit_edges,
        "total_independent_groups": len(root_to_gid),
        "multi_image_groups": sum(1 for sz in group_sizes.values() if sz > 1),
        "max_group_size": max(group_sizes.values()) if group_sizes else 0,
    }
    return records, cluster_stats


def stratified_group_split(
    records: List[Dict[str, Any]],
    ratios: Tuple[float, float, float] = (0.70, 0.15, 0.15),
    seed: int = 42,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Assign whole groups to train/validation/test while matching target
    (source_dataset, label) proportions cleanly.
    """
    split_names = ["train", "validation", "test"]
    rng = np.random.default_rng(seed)

    groups: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    total_strata: Counter = Counter()
    for rec in records:
        groups[rec["group_id"]].append(rec)
        total_strata[(rec["source_dataset"], rec["label"])] += 1

    total_n = len(records)
    target_split_totals = [total_n * r for r in ratios]
    target_strata = {
        s_idx: {k: v * ratios[s_idx] for k, v in total_strata.items()}
        for s_idx in range(3)
    }

    current_split_totals = [0, 0, 0]
    current_strata = [Counter(), Counter(), Counter()]
    group_assignments: Dict[int, str] = {}

    group_items = list(groups.items())
    perm = rng.permutation(len(group_items))
    group_items = [group_items[i] for i in perm]
    group_items.sort(
        key=lambda item: (
            -len(item[1]),
            min(total_strata[(r["source_dataset"], r["label"])] for r in item[1]),
        )
    )

    for gid, grecs in group_items:
        g_strata = Counter((r["source_dataset"], r["label"]) for r in grecs)
        g_len = len(grecs)

        best_s = 0
        best_score = -1e18
        for s_idx in range(3):
            strata_score = 0.0
            for k, cnt in g_strata.items():
                target_k = max(target_strata[s_idx][k], 1.0)
                deficit_ratio = (target_strata[s_idx][k] - current_strata[s_idx][k]) / target_k
                strata_score += cnt * deficit_ratio
            overall_deficit = (
                target_split_totals[s_idx] - current_split_totals[s_idx]
            ) / max(target_split_totals[s_idx], 1.0)
            score = strata_score + 0.5 * g_len * overall_deficit
            if score > best_score:
                best_score = score
                best_s = s_idx

        group_assignments[gid] = split_names[best_s]
        current_split_totals[best_s] += g_len
        for k, cnt in g_strata.items():
            current_strata[best_s][k] += cnt

    splits: Dict[str, List[Dict[str, Any]]] = {name: [] for name in split_names}
    for rec in records:
        splits[group_assignments[rec["group_id"]]].append(rec)
    return splits


def verify_zero_leakage(
    splits: Dict[str, List[Dict[str, Any]]],
    dhash_threshold: int = 16,
) -> Dict[str, Any]:
    """Assert zero group_id, SHA-256, and near-dHash overlap across splits."""
    split_names = ["train", "validation", "test"]
    gids = {s: {r["group_id"] for r in splits[s]} for s in split_names}
    shas = {s: {r["sha256"] for r in splits[s]} for s in split_names}
    dhashes = {
        s: np.vstack([r["dhash"] for r in splits[s]])
        for s in split_names
    }

    gid_overlaps = {}
    sha_overlaps = {}
    near_dhash_overlaps = {}
    for i in range(3):
        for j in range(i + 1, 3):
            a, b = split_names[i], split_names[j]
            pair_key = f"{a}_vs_{b}"
            gid_overlaps[pair_key] = len(gids[a] & gids[b])
            sha_overlaps[pair_key] = len(shas[a] & shas[b])

            cross_near = 0
            da, db = dhashes[a], dhashes[b]
            for start in range(0, len(da), 128):
                dists = pairwise_hamming_256(da[start : min(start + 128, len(da))], db)
                cross_near += int(np.any(dists <= dhash_threshold, axis=1).sum())
            near_dhash_overlaps[pair_key] = cross_near

    all_zero = (
        all(v == 0 for v in gid_overlaps.values())
        and all(v == 0 for v in sha_overlaps.values())
        and all(v == 0 for v in near_dhash_overlaps.values())
    )
    if not all_zero:
        raise RuntimeError(
            f"Data leakage detected! gid={gid_overlaps}, sha={sha_overlaps}, dhash={near_dhash_overlaps}"
        )

    return {
        "leakage_free": True,
        "group_id_overlaps": gid_overlaps,
        "sha256_overlaps": sha_overlaps,
        "near_dhash256_overlaps": near_dhash_overlaps,
    }


def preprocess_and_save_splits(
    splits: Dict[str, List[Dict[str, Any]]],
    out_dir: Path,
    max_workers: int = 10,
) -> Dict[str, Dict[str, Any]]:
    """Preprocess all split images to 224x224 CLAHE PNGs and write CSV manifests."""
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    split_summaries: Dict[str, Dict[str, Any]] = {}

    def _process_one(task: Tuple[Dict[str, Any], Path]) -> str:
        rec, dst_path = task
        rgb = preprocess_single_image(rec["abs_path"], config=DEFAULT_CONFIG)
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        ok = cv2.imwrite(str(dst_path), bgr)
        if not ok:
            raise IOError(f"Failed to write preprocessed image: {dst_path}")
        return str(dst_path.relative_to(ROOT_DIR)).replace("\\", "/")

    for split_name, items in splits.items():
        split_img_dir = out_dir / split_name
        split_img_dir.mkdir(parents=True, exist_ok=True)

        tasks: List[Tuple[Dict[str, Any], Path]] = []
        seen_names: Counter = Counter()
        for rec in items:
            base = f"{rec['source_dataset'].lower()}_{rec['sample_id']}"
            seen_names[base] += 1
            suffix = f"_{seen_names[base]}" if seen_names[base] > 1 else ""
            dst_path = split_img_dir / f"{base}{suffix}.png"
            tasks.append((rec, dst_path))

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            processed_paths = list(pool.map(_process_one, tasks))

        rows = []
        for rec, proc_rel in zip(items, processed_paths):
            rows.append(
                {
                    "image_path": rec["rel_path"],
                    "processed_image_path": proc_rel,
                    "label": rec["label"],
                    "source_dataset": rec["source_dataset"],
                    "sample_id": rec["sample_id"],
                    "group_id": rec["group_id"],
                    "sha256": rec["sha256"],
                    "dhash256": dhash256_hex(rec["dhash"]),
                }
            )

        df = pd.DataFrame(rows)
        df.to_csv(out_dir / f"{split_name}.csv", index=False)

        split_summaries[split_name] = {
            "total": len(df),
            "by_source": df["source_dataset"].value_counts().to_dict(),
            "by_label": {
                str(k): int(v) for k, v in df["label"].value_counts().sort_index().items()
            },
            "by_source_and_label": {
                src: {
                    str(k): int(v)
                    for k, v in sub["label"].value_counts().sort_index().items()
                }
                for src, sub in df.groupby("source_dataset")
            },
        }
        print(
            f"[Split: {split_name}] {len(df)} images | sources={split_summaries[split_name]['by_source']} "
            f"| labels={split_summaries[split_name]['by_label']}"
        )

    return split_summaries


def build_sustech_external_manifest(
    internal_records: List[Dict[str, Any]],
    dhash_threshold: int = 16,
) -> Dict[str, Any]:
    """
    Build SUSTech-SYSU external validation CSV (1,219 images, ICDR 0-4) and
    verify zero SHA-256 / 256-bit dHash overlap against internal APTOS + DDR records.
    """
    ext_root = ROOT_DIR / "data" / "raw" / "sustech_external" / "originalImages"
    dr_df = pd.read_csv(ext_root / "drLabels.csv")
    c5_df = pd.read_csv(ext_root / "c5_DR_reclassified.csv")

    c5_map = {
        str(r["Fundus_images"]).strip(): int(
            r["DR_grade(International_Clinical_DR_Severity_Scale)"]
        )
        for _, r in c5_df.iterrows()
    }

    internal_shas = {r["sha256"] for r in internal_records}
    internal_dhashes = np.vstack([r["dhash"] for r in internal_records])

    ext_paths: List[Path] = []
    ext_labels: List[int] = []
    c5_reclassified_count = 0

    for _, row in dr_df.iterrows():
        fname = str(row["Fundus_images"]).strip()
        icdr = int(row["DR_grade(International_Clinical_DR_Severity_Scale)"])
        if icdr == 5:
            if fname not in c5_map:
                raise KeyError(f"Missing category-5 reclassification for {fname}")
            icdr = c5_map[fname]
            c5_reclassified_count += 1
        if icdr not in (0, 1, 2, 3, 4):
            raise ValueError(f"Unexpected ICDR label {icdr} for {fname}")
        img_path = ext_root / fname
        if not img_path.exists():
            raise FileNotFoundError(f"Missing SUSTech-SYSU image: {img_path}")
        ext_paths.append(img_path)
        ext_labels.append(icdr)

    with ThreadPoolExecutor(max_workers=10) as pool:
        hashes = list(pool.map(compute_file_sha256_and_dhash256, ext_paths))

    sha_overlap = 0
    ext_dhash_mat = np.vstack([h[1] for h in hashes])
    near_overlap = 0
    for start in range(0, len(ext_dhash_mat), 128):
        dists = pairwise_hamming_256(
            ext_dhash_mat[start : min(start + 128, len(ext_dhash_mat))], internal_dhashes
        )
        near_overlap += int(np.any(dists <= dhash_threshold, axis=1).sum())

    rows = []
    for img_path, label, (sha, dhash) in zip(ext_paths, ext_labels, hashes):
        if sha in internal_shas:
            sha_overlap += 1
        rel_path = str(img_path.relative_to(ROOT_DIR)).replace("\\", "/")
        rows.append(
            {
                "image_path": rel_path,
                "label": label,
                "sample_id": img_path.stem,
                "source_dataset": "SUSTech_SYSU",
                "sha256": sha,
                "dhash256": dhash256_hex(dhash),
            }
        )

    out_csv = ROOT_DIR / "data" / "raw" / "sustech_external" / "external_manifest.csv"
    ext_out_df = pd.DataFrame(rows)
    ext_out_df.to_csv(out_csv, index=False)

    return {
        "manifest_path": str(out_csv.relative_to(ROOT_DIR)).replace("\\", "/"),
        "total_images": len(ext_out_df),
        "category5_reclassified_to_icdr": c5_reclassified_count,
        "by_label": {
            str(k): int(v)
            for k, v in ext_out_df["label"].value_counts().sort_index().items()
        },
        "sha256_overlap_with_internal": sha_overlap,
        "near_dhash256_overlap_with_internal": near_overlap,
    }


def main() -> None:
    t0 = time.time()
    print("=== Step 1: Loading raw APTOS 2019 & DDR records ===")
    raw_records = load_raw_records()
    print(f"Loaded {len(raw_records)} raw image records.")

    print("=== Step 2: Computing SHA-256 and 256-bit center-crop dHash ===")
    paths = [r["abs_path"] for r in raw_records]
    with ThreadPoolExecutor(max_workers=12) as pool:
        hashes = list(pool.map(compute_file_sha256_and_dhash256, paths))
    for rec, (sha, dhash) in zip(raw_records, hashes):
        rec["sha256"] = sha
        rec["dhash"] = dhash

    print("=== Step 3: Exact SHA-256 deduplication & conflict removal ===")
    dedup_records, dedup_stats = deduplicate_exact_sha256(raw_records)
    print(json.dumps(dedup_stats, indent=2))

    print("=== Step 4: Near-duplicate & DDR visit clustering ===")
    clustered_records, cluster_stats = build_leakage_clusters(
        dedup_records, dhash_threshold=16, ddr_visit_window_sec=15.0
    )
    print(json.dumps(cluster_stats, indent=2))

    print("=== Step 5: Patient/cluster-independent stratified 70/15/15 split ===")
    splits = stratified_group_split(clustered_records, ratios=(0.70, 0.15, 0.15), seed=42)
    leakage_report = verify_zero_leakage(splits, dhash_threshold=16)
    print("Leakage check:", json.dumps(leakage_report))

    print("=== Step 6: Preprocessing & writing data/processed_combined/ ===")
    out_dir = ROOT_DIR / "data" / "processed_combined"
    split_summaries = preprocess_and_save_splits(splits, out_dir=out_dir, max_workers=10)

    print("=== Step 7: Building SUSTech-SYSU external manifest & overlap check ===")
    ext_report = build_sustech_external_manifest(clustered_records, dhash_threshold=16)
    print(json.dumps(ext_report, indent=2))

    elapsed = round(time.time() - t0, 2)
    report = {
        "elapsed_seconds": elapsed,
        "preprocessing_config": {
            "target_size": list(DEFAULT_CONFIG.target_size),
            "crop_black_borders": DEFAULT_CONFIG.crop_black_borders,
            "border_threshold": DEFAULT_CONFIG.border_threshold,
            "crop_safety_margin": DEFAULT_CONFIG.crop_safety_margin,
            "clahe_enabled": DEFAULT_CONFIG.clahe_enabled,
            "clahe_clip_limit": DEFAULT_CONFIG.clahe_clip_limit,
            "clahe_tile_grid_size": list(DEFAULT_CONFIG.clahe_tile_grid_size),
            "denoising_enabled": DEFAULT_CONFIG.denoising_enabled,
        },
        "deduplication_stats": dedup_stats,
        "clustering_stats": cluster_stats,
        "leakage_verification": leakage_report,
        "splits": split_summaries,
        "external_dataset_sustech_sysu": ext_report,
    }
    report_path = out_dir / "dataset_integration_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Integration complete in {elapsed:.1f}s -> {report_path}")


if __name__ == "__main__":
    main()
