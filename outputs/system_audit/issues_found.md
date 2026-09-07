# Audit Issues Log & Resolutions

## Resolved Issues During Verification

| Issue ID | Severity | Description | Fix Applied | Status |
|---|---|---|---|---|
| ISSUE-01 | **CRITICAL** | Model state_dict dictionary key mismatch when loading `best_model.pth` checkpoint. | Updated `generate_explainability_outputs.py` and `generate_calibration_outputs.py` to extract `checkpoint.get("model_state_dict", checkpoint)`. | RESOLVED |
| ISSUE-02 | **HIGH** | Function name collision `test_model_robustness` in `src/evaluation/robustness.py` caused Pytest fixture error. | Renamed function to `evaluate_model_robustness`. | RESOLVED |
| ISSUE-03 | **MEDIUM** | Health check response mismatch (`{"status": "ok", "service": "..."}` vs `{"status": "ok"}`). | Updated `backend/app/routes/health.py` to return exact `{"status": "ok"}` schema. | RESOLVED |
| ISSUE-04 | **LOW** | Python typing `Tuple` import missing in `generate_calibration_outputs.py`. | Added `from typing import Tuple` import. | RESOLVED |

## Remaining Operational Limitations (Non-Blocking)

1. **APTOS 2019 Dataset Labels**: APTOS 2019 dataset does not include explicit clinical gradability labels; deterministic thresholding is used for IQA without fabricating ground truth labels.
2. **MATLAB / Simulink Executable**: MATLAB executable is not present in local system PATH; complete reproducible SimEvents model script (`src/simulation/simulink_model.m`) and Python simulation engine (`src/simulation/screening_sim.py`) are provided.
