"""Benchmark script to measure exact execution timings of the Netra AI Pipeline."""

import time
import cv2
import numpy as np
import torch
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
import sys
sys.path.insert(0, str(ROOT_DIR))

from src.reporting.screening_report import ScreeningPipeline

def benchmark():
    img_good = np.zeros((300, 300, 3), dtype=np.uint8)
    cv2.circle(img_good, (150, 150), 120, (30, 70, 200), -1)
    cv2.line(img_good, (50, 150), (250, 150), (10, 200, 220), 2)

    # Instantiate pipeline
    t0 = time.perf_counter()
    pipeline = ScreeningPipeline()
    t_init = (time.perf_counter() - t0) * 1000.0

    # Measure single image execution
    t1 = time.perf_counter()
    report = pipeline.process_image(img_good, sample_id="bench_01")
    t_exec = (time.perf_counter() - t1) * 1000.0

    print(f"Pipeline Initialization Time: {t_init:.2f} ms")
    print(f"Pipeline Total Processing Time: {t_exec:.2f} ms")
    print("Report sample_id:", report["sample_id"])
    print("Report quality status:", report["image_quality"]["status"])
    print("Report DR grade:", report["dr_prediction"]["grade"] if report["dr_prediction"] else "None")

if __name__ == "__main__":
    benchmark()
