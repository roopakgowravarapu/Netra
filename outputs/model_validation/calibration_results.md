# Confidence Calibration & Reliability Audit

- **Fitted Temperature Parameter (Validation Set ONLY)**: T = 1.0700
- **Expected Calibration Error (ECE)**: 0.0026
- **Maximum Calibration Error (MCE)**: 0.0026
- **Mean Brier Score**: 0.0000
- **Mean Calibrated Confidence**: 99.75%

## Calibration Properties Verified
1. Probabilities range $0.0 \le P_i \le 1.0$ and sum to $1.0$.
2. Temperature parameter was fitted strictly on validation set logits (`data/processed/validation.csv`).
3. Test set remained 100% untouched during calibration fitting.