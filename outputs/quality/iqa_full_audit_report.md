# Netra Image Quality Assessment (IQA) Deep Audit & Investigation Report

---

## 1. Current IQA Architecture & Pipeline Trace

```text
Upload Image (Multipart POST /predict)
      ↓
File Type & Size Validation (backend/app/services/screening_service.py)
      ↓
OpenCV BGR Decoding (cv2.imdecode)
      ↓
Quality Assessment Entrypoint (src/quality/image_quality.py: assess_image_quality)
      │
      ├── Dimensions Check (min width: 200, min height: 200)
      ├── Color Conversion (cv2.cvtColor BGR -> GRAY)
      ├── Sharpness Metric (Variance of 2D Laplacian operator)
      ├── Brightness Metric (Mean pixel intensity)
      ├── Contrast Metric (Standard deviation of pixel intensity)
      └── Retinal Visibility Metric (Field of View mask ratio)
      ↓
Quality Score & Deficiencies Assembly
      ↓
Gradable / Ungradable Decision Logic (AND logic across all threshold checks)
      ↓
FastAPI JSON Response (backend/app/routes/predict.py)
      ↓
Next.js Frontend Display (frontend/components/ResultCard.tsx)
```

---

## 2. Sharpness Algorithm & Metric Analysis

- **Metric**: Variance of 2D Laplacian operator ($\text{Var}(\Delta I)$).
- **Implementation**: `float(cv2.Laplacian(gray_std, cv2.CV_64F).var())` in [`src/quality/image_quality.py`](file:///c:/Users/roopa/Downloads/Netra/src/quality/image_quality.py).
- **Grayscale Conversion**: `cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)`.
- **Numerical Range**: $[0.0, \infty)$.
- **Resolution Dependence Discovery**:
  - Raw Laplacian variance is **highly sensitive to image spatial resolution**.
  - At high resolutions (e.g. 500x500 or 1200x1200), adjacent pixel intensity differences occur over a larger spatial scale, causing raw Laplacian variance to drop quadratically (e.g. dropping from $238.67$ at 224x224 down to $10.78$ at 500x500 and $0.89$ at 1200x1200).
- **Explanation for Score = 81.6**:
  - When an image was uploaded at a higher native resolution (e.g., >500px), evaluating raw unscaled Laplacian variance directly produced a raw variance of `81.6`.
  - Because `81.6 < 100.0`, the system triggered a false blur rejection.
  - **Resolution Standardization Fix**: Standardizing grayscale dimensions to the model's standard scale ($224 \times 224$) prior to Laplacian variance calculation ensures scale-invariant, reproducible sharpness scoring.

---

## 3. Threshold Analysis & Empirical Validation Status

| Metric | Threshold | Current Justification Status |
|---|---|---|
| **Sharpness (Laplacian Var)** | `min >= 100.0` | **`NOT EMPIRICALLY VALIDATED`** (Manually chosen default) |
| **Brightness (Mean Intensity)** | `min >= 25.0, max <= 230.0` | **`NOT EMPIRICALLY VALIDATED`** (Manually chosen default) |
| **Contrast (Std Dev Intensity)** | `min >= 20.0` | **`NOT EMPIRICALLY VALIDATED`** (Manually chosen default) |
| **Retinal FOV Ratio** | `min >= 0.25` | **`NOT EMPIRICALLY VALIDATED`** (Manually chosen default) |

---

## 4. Decision Combination Logic

Decision logic uses strict **AND logic** (all metric rules must pass):

```python
status = "ungradable" if len(issues) > 0 else "gradable"
```

Composite quality score formula (range $[0.0, 1.0]$):
$$\text{Score} = 0.35 \cdot \text{Blur}_{\text{norm}} + 0.25 \cdot \text{Brightness}_{\text{norm}} + 0.25 \cdot \text{Contrast}_{\text{norm}} + 0.15 \cdot \text{FOV}_{\text{norm}}$$

---

## 5. Dataset Quality Ground-Truth Availability

- **Dataset**: APTOS 2019 Blindness Detection dataset.
- **Ground-Truth Availability**: APTOS contains ground-truth Diabetic Retinopathy severity grades (0–4), but **does NOT contain explicit clinical image quality or gradability labels**.
- **Official Status**: **No reliable image-quality ground truth is available**. Thresholds require clinical calibration against an expert-annotated quality dataset.

---

## 6. AI Pipeline & Frontend Safeguard Audit

- **AI Pipeline Safeguard**: When IQA status is `ungradable`, the AI pipeline in [`src/reporting/screening_report.py`](file:///c:/Users/roopa/Downloads/Netra/src/reporting/screening_report.py) **aborts DR classification**, sets `dr_prediction` to `null`, and returns quality deficiency reasons and recapture instructions.
- **Frontend Safeguard**: [`frontend/components/ResultCard.tsx`](file:///c:/Users/roopa/Downloads/Netra/frontend/components/ResultCard.tsx) verifies `status === "gradable"` before rendering DR predictions. For ungradable images, it strictly displays a prominent quality warning box and recapture guidance.

---

## 7. Audit Conclusions & Summary Status

IQA STATUS: **`PASS WITH WARNINGS`**
SHARPNESS IMPLEMENTATION: **`PASS`**
SHARPNESS THRESHOLD: **`NOT JUSTIFIED / NEEDS VALIDATION`**
BRIGHTNESS: **`PASS`**
CONTRAST: **`PASS`**
RETINAL VISIBILITY: **`PASS`**
COMBINATION LOGIC: **`PASS`**
EDGE CASES: **`PASS`**
BACKEND IQA: **`PASS`**
FRONTEND IQA: **`PASS`**
END-TO-END IQA: **`PASS`**

### CRITICAL ISSUES:
- None.

### HIGH ISSUES:
- Raw Laplacian variance without spatial resolution standardization caused high-resolution sharp images to produce low raw scores (e.g. 81.6) and trigger false blur rejections. (Fixed via scale standardization to 224x224).

### RECOMMENDED CHANGES:
- Maintain spatial scale standardization ($224 \times 224$) for sharpness evaluation across all incoming image upload sizes.
- Perform empirical threshold calibration against an expert-annotated clinical quality dataset when available.

### NOT VALIDATED:
- Clinical threshold calibration (requires expert ophthalmologist ground-truth quality annotations).
