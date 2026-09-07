# Netra AI Pipeline Directory

This directory will contain the core Explainable AI modules for Diabetic Retinopathy screening:

- `quality.py`: Image Quality Assessment (IQA) module (checks blur, illumination, field of view).
- `classifier.py`: Deep learning model for DR Severity Classification (Level 0–4).
- `explainability.py`: Grad-CAM / Attention heatmap generator for model interpretability.
- `uncertainty.py`: Model confidence and epistemic uncertainty estimation.
- `report.py`: Automated clinical screening report synthesis module.
