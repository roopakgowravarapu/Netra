# EfficientNet-B0 Baseline Model Training Report

- **Architecture**: `EfficientNet-B0` (Pretrained Transfer Learning)
- **Total Parameters**: `4,013,953`
- **Trainable Parameters**: `4,013,953`
- **Best Epoch**: `1`
- **Best Validation Loss**: `0.0012`
- **Best Validation Accuracy**: `100.00%`
- **Early Stopping Triggered**: `No`
- **Saved Model Weights**: `models/best_model.pth`

## Hyperparameters & Configuration

- **Optimizer**: `AdamW` (lr=0.001, weight_decay=0.0001)
- **Scheduler**: `CosineAnnealingLR`
- **Batch Size**: `32`
- **Random Seed**: `42`
- **Input Image Dimensions**: `224x224x3`

## Training Set Class Weights

| Level | DR Diagnosis | Weight |
| --- | --- | --- |
| Level 0 | No DR | 0.2161 |
| Level 1 | Mild | 1.0537 |
| Level 2 | Moderate | 0.3904 |
| Level 3 | Severe | 2.0215 |
| Level 4 | Proliferative DR | 1.3184 |
