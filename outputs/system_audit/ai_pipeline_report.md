# AI Pipeline Verification Audit Report

- **Framework**: PyTorch + torchvision
- **Trained Model File**: `models/best_model.pth` (~48.6 MB, EfficientNet-B0)
- **Status**: `PASS` (Model loaded successfully, zero fake predictions)

## Component Audit

### 1. Image Quality Assessment (IQA)
- **Implementation**: [`src/quality/image_quality.py`](file:///c:/Users/roopa/Downloads/Netra/src/quality/image_quality.py)
- **Evaluated Features**: Sharpness (Laplacian variance), Brightness mean, Contrast std, Retinal FOV ratio, Resolution.
- **Ungradable Safeguard**: If status is `ungradable`, the pipeline **aborts DR classification**, returns quality issue reasons, and recommends image recapture.

### 2. DR Classification Model
- **Architecture**: EfficientNet-B0 Transfer Learning (5-class output: Level 0-4).
- **Model File**: Verified present at `models/best_model.pth`. Weights strictly frozen (no retraining).
- **Classes**: Level 0 (No DR), Level 1 (Mild), Level 2 (Moderate), Level 3 (Severe), Level 4 (Proliferative).

### 3. Confidence Calibration & Uncertainty
- **Implementation**: [`src/evaluation/calibration.py`](file:///c:/Users/roopa/Downloads/Netra/src/evaluation/calibration.py)
- **Method**: Post-hoc Temperature Scaling fit strictly on validation split (`data/processed/validation.csv`).
- **Uncertainty Metrics**: Shannon Entropy & Prediction Margin.

### 4. Grad-CAM Explainability
- **Implementation**: [`src/explainability/gradcam.py`](file:///c:/Users/roopa/Downloads/Netra/src/explainability/gradcam.py)
- **Target Convolutional Layer**: Automatically targets `model.features[-1]` (last Conv2dNormActivation block in EfficientNet-B0).
- **Outputs**: Heatmap array normalized [0, 1] and RGB overlay image saved for frontend static serving.
