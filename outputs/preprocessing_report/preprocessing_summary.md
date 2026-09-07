# APTOS 2019 Preprocessing Pipeline Report

- **Target Image Dimensions**: `224 x 224`
- **CLAHE Contrast Enhancement**: `Enabled (clipLimit=2.0)`
- **Optional Denoising**: `Disabled (Configurable)`
- **Total Successfully Processed**: `3662`
- **Total Failed**: `0`

## 1. Processed Split Counts

| Split | Image Count | Status |
| --- | --- | --- |
| Train | 2563 | OK |
| Validation | 549 | OK |
| Test | 550 | OK |
| **Total** | **3662** | **Complete** |

## 2. Preprocessing Operations Applied

- 1. Retinal boundary detection & safe border cropping (crop_fundus_circle)
- 2. Configurable resizing to target dimensions (224, 224)
- 3. LAB space L-channel CLAHE contrast enhancement (clip_limit=2.0, tiles=(8, 8))
- 4. Optional Non-Local Means Denoising (enabled=False)
- 5. Deep learning normalization scheme (zero_to_one)
