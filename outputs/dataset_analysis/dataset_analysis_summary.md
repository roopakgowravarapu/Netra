# APTOS 2019 Exploratory Dataset Analysis & Split Report

- **Random Seed**: `42` (Fixed for 100% reproducibility)
- **Split Ratios**: 70% Train / 15% Validation / 15% Test
- **Verification Status**: **PASSED**

## 1. Class Distribution Across Stratified Splits

| DR Level | Diagnosis | Total Samples | Train (70%) | Validation (15%) | Test (15%) | Proportion |
| --- | --- | --- | --- | --- | --- | --- |
| Level 0 | No DR | 1805 | 1263 | 271 | 271 | 49.29% |
| Level 1 | Mild | 370 | 259 | 55 | 56 | 10.1% |
| Level 2 | Moderate | 999 | 699 | 150 | 150 | 27.28% |
| Level 3 | Severe | 193 | 135 | 29 | 29 | 5.27% |
| Level 4 | Proliferative DR | 295 | 207 | 44 | 44 | 8.06% |
| **Total** | **All Classes** | **3662** | **2563** | **549** | **550** | **100.0%** |

## 2. Image Quality & Dimension Metrics

- **Dimension Range**: `1050x1050` to `3216x2136`
- **Mean Width x Height**: `2361.0 x 1766.2` (Aspect Ratio: `1.28`)
- **Mean Grayscale Brightness**: `84.89 ± 19.95`
- **Mean Grayscale Contrast**: `44.92 ± 10.12`
- **Visually Unusual Outlier Samples**: `0` samples identified

## 3. Split Verification Checklist

- [x] **Zero Overlap**: `0` shared images between splits
- [x] **All 5 Classes Represented**: `True`
- [x] **Exact 70/15/15 Target Counts**: Train=2563, Val=549, Test=550
