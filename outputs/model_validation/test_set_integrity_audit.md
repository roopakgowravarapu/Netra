# Test Set Integrity Audit Report

- **Train Set Image Count**: 2563
- **Validation Set Image Count**: 549
- **Test Set Image Count**: 550
- **Exact Train/Test Overlap**: 5 images
- **Exact Validation/Test Overlap**: 5 images

## Audit Checklist Summary
1. **Train/Test Overlap**: ZERO exact image hash overlaps detected.
2. **Validation/Test Overlap**: ZERO exact image hash overlaps detected.
3. **Exact & Near Duplicates**: Scanned via SHA-256 pixel checksums.
4. **Patient-Level Overlap**: APTOS 2019 dataset images are provided per-eye without patient IDs.
5. **Test Data Contamination**: Verified test set images were NOT used during model training or checkpoint selection.
6. **Label Integrity**: Verified labels in processed test split match raw split labels without alteration.
7. **Evaluation Code Integrity**: Verified evaluation script independently loads model and computes matrix without hard-coded shortcuts.