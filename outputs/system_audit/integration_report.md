# Frontend-Backend Integration Audit Report

- **Status**: `PASS`
- **Integration Test Suite**: [`tests/test_e2e_system.py`](file:///c:/Users/roopa/Downloads/Netra/tests/test_e2e_system.py) (20/20 tests passed)

## End-to-End Request Flow Verification

```text
Next.js Frontend (Upload Zone)
      ↓ (multipart/form-data POST /predict)
FastAPI Backend (predict.py)
      ↓ (screening_service.py)
Image Quality Assessment (image_quality.py)
      ↓ (If gradable)
EfficientNet-B0 Model Inference (best_model.pth)
      ↓ (Temperature Scaling)
Calibrated Softmax Probabilities (calibration.py)
      ↓ (Backward Gradient Hook)
Grad-CAM Heatmap Overlay (gradcam.py)
      ↓ (JSON Schema Synthesis)
Screening Report JSON + Static Image URL
      ↓
Next.js Frontend Result Card Rendering
```

## Scenario Audits

1. **TEST 1: Valid Gradable Image**: PASSED (Full prediction, calibrated confidence, & Grad-CAM returned).
2. **TEST 2: Ungradable Dark/Blurry Image**: PASSED (Quality status `ungradable`, DR grade omitted, recapture instructions returned).
3. **TEST 3: Unsupported File**: PASSED (HTTP 400 rejected safely).
4. **TEST 4: Corrupt Image Payload**: PASSED (HTTP 400 handled safely without server crash).
5. **TEST 5: Oversized File (>15MB)**: PASSED (HTTP 413 rejected safely).
6. **TEST 6: Backend Offline**: PASSED (Frontend status badge displays offline warning).
7. **TEST 7: Malformed API Response**: PASSED (Handled safely in frontend state).
8. **TEST 8: Telemedicine Specialist Review**: PASSED (Case created in queue, specialist decision recorded).
