# Netra - Explainable AI Platform for Diabetic Retinopathy Screening

**Independent Clinical Decision-Support & Multimodal Retinal Screening Platform**

Netra is an end-to-end Explainable AI (XAI) clinical screening system engineered for primary healthcare centers and rural clinics. It performs automated Diabetic Retinopathy (DR) grading from fundus photography, enforces strict Image Quality Assessment (IQA) safeguards, quantifies diagnostic uncertainty, extracts anatomical retinal biomarkers, and generates comprehensive explainability maps and clinical decision-support reports.

---

## Key System Features

1. **Image Quality Assessment (IQA)**
   - Pre-inference quality gate preventing ungradable or severely blurred scans from receiving clinical inference.
   - Evaluates Tenengrad focus gradient energy, circular Retinal Field-of-View (FOV) mask, mean green-channel illumination, and sensor saturation.
   - Categorizes scans into **Gradable**, **Borderline Enhanced** (adaptive CLAHE enhancement), or **Ungradable** with human-readable retake feedback.

2. **Calibrated DR Classification Pipeline**
   - EfficientNet-B0 backbone fine-tuned on combined APTOS-2019 and DDR retinal cohorts.
   - 5-Grade International Clinical Diabetic Retinopathy (ICDR) scale:
     - **Grade 0**: No DR
     - **Grade 1**: Mild NPDR (Microaneurysms only)
     - **Grade 2**: Moderate NPDR (MAs, hard exudates, dot/blot hemorrhages)
     - **Grade 3**: Severe NPDR (4-2-1 rule criteria, extensive hemorrhages)
     - **Grade 4**: Proliferative DR (Neovascularization, preretinal hemorrhages)
   - Temperature scaling probability calibration on validation cohorts to prevent overconfident misclassifications.
   - Shannon entropy and margin-based uncertainty quantification triggering specialist review recommendations when diagnostic confidence is low.

3. **Multimodal Explainable AI (XAI)**
   - **Grad-CAM Saliency Maps**: Target layer neural activation overlays highlighting retinal regions driving classification.
   - **Computer Vision Biomarker Localization**:
     - Optic Disc localization (luminance & morphological circular Hough filter)
     - Fovea Centralis localization (anatomic sector anchoring relative to optic disc)
     - Retinal vessel segmentation & vascular density computation (matched filtering)
     - Microaneurysm detection (green channel contrast morphological top-hat filtering)
     - Hard exudate cluster detection and pixel area quantification
     - Hemorrhage segmentation (dot/blot vs flame hemorrhage shape classification)
     - Neovascularization rule-based candidate localization
   - **6-Sector Retinal Zoning (ETDRS-Aligned)**:
     - Macular/Perifoveal Ring (central visual preservation)
     - Superior-Temporal Sector
     - Inferior-Temporal Sector
     - Superior-Nasal Sector
     - Inferior-Nasal Sector
     - Optic Disc & Peripapillary Sector
   - **Spatial Map**: 448×448 high-contrast spatial mapping highlighting quadrant distribution and macular threat index.

4. **Telemedicine & Longitudinal Patient Tracking**
   - Asynchronous specialist review queue (Confirm, Override, or Request Recapture).
   - Longitudinal patient registry tracking progression across visits with grade deltas and macular threat escalation warnings.
   - Multilingual interface supporting English, Telugu, and Hindi.
   - Audit trail tracking all specialist actions, timestamps, and clinical review notes.

---

## Technology Stack

- **Backend**: Python 3.12, FastAPI, Uvicorn, Pydantic v2
- **Deep Learning**: PyTorch 2.2+, Torchvision, EfficientNet-B0
- **Computer Vision**: OpenCV (opencv-python-headless), NumPy, SciPy, Scikit-learn
- **Frontend**: Next.js 14 (App Router), TypeScript, React, Lucide Icons
- **Storage / Repositories**: Thread-safe Abstracted Repository Pattern with persistent JSON and audit trails
- **Testing**: Pytest, FastAPI TestClient, AnyIO

---

## Project Directory Structure

```text
Netra/
├── app.py                     # Root executable script (self-test & server runner)
├── package.json               # Monorepo task orchestration scripts
├── requirements.txt           # Monorepo Python dependencies
├── .env.example               # Environment variables template
│
├── backend/                   # FastAPI Backend Application
│   ├── app/
│   │   ├── core/              # Central configuration, logging, exceptions
│   │   ├── repositories/      # Repository layer (CaseRepository, PatientRepository)
│   │   ├── routes/            # API endpoints (screening, cases, patients, health)
│   │   ├── schemas/           # Pydantic data validation schemas
│   │   ├── services/          # Business logic & retinal computer vision services
│   │   │   ├── case_service.py
│   │   │   ├── patient_service.py
│   │   │   ├── retinal_analysis.py # Pure Python Retinal CV & Biomarker engine
│   │   │   └── screening_service.py
│   │   └── main.py            # FastAPI server entry point
│   ├── venv/                  # Python 3.12 Virtual Environment
│   └── requirements.txt       # Backend package manifest
│
├── frontend/                  # Next.js 14 Frontend Application
│   ├── app/                   # Next.js App Router (screening, dashboard, home)
│   ├── components/            # Modular UI components
│   │   ├── common/            # Header, Toast, Modals, Badges
│   │   ├── screening/         # UploadZone, ResultCard orchestration
│   │   ├── explainability/    # BiomarkersGrid, SpatialZoningTable
│   │   └── reports/           # FullReportModal, PDF printable views
│   ├── lib/                   # API client, translations (EN, TE, HI), types
│   │   ├── api.ts             # Typed REST API client
│   │   ├── translations.ts    # Multi-language clinical dictionaries
│   │   └── types/             # Modular TypeScript type definitions
│   └── package.json           # Frontend dependencies & build scripts
│
├── src/                       # Machine Learning & AI Modules
│   ├── evaluation/            # Calibration (ECE, Temperature scaling), Robustness
│   ├── explainability/        # Grad-CAM PyTorch implementation
│   ├── preprocessing/         # Ben Graham preprocessing, circular cropping
│   ├── quality/               # Tenengrad focus, FOV, green channel illumination
│   ├── reporting/             # Automated clinical screening report generator
│   ├── simulation/            # Discrete-event screening simulation engine
│   └── training/              # Model architecture & training pipelines
│
├── models/                    # Trained neural network weights
│   └── best_model_aptos_ddr.pth # Trained EfficientNet-B0 checkpoint
│
├── tools/                     # Operational scripts & benchmarks
│   └── benchmarks/            # Pipeline throughput & calibration audit scripts
│
├── outputs/                   # Persisted patient records, telemedicine cases, XAI maps
│   ├── cases/                 # Active telemedicine review queue cases
│   ├── patients/              # Registered patient profiles & longitudinal visits
│   └── explainability/        # Generated Grad-CAM, spatial maps & overlays
│
└── tests/                     # Comprehensive automated test suite (74 tests)
    ├── test_backend.py        # API endpoint validation & file checks
    ├── test_calibration.py    # ECE & temperature scaling verification
    ├── test_e2e_system.py     # End-to-end integration and error recovery
    ├── test_gradcam.py        # Grad-CAM activation and dimension tests
    ├── test_quality.py        # Image quality blur & exposure tests
    ├── test_retinal_analysis.py # Retinal CV anatomical structures & zoning
    ├── test_telemedicine.py   # Specialist review, override, and recapture
    └── test_workflow_grades.py# 5-grade clinical triage and routing
```

---

## Getting Started

### 1. Prerequisites
- Python 3.12+
- Node.js v18+ and npm

### 2. Environment Configuration
Copy the environment templates:
```bash
# Root environment configuration
cp .env.example .env

# Frontend environment configuration
cp frontend/.env.local.example frontend/.env.local
```

### 3. Quick System Self-Test
Run the automated runnable self-test:
```bash
.\backend\venv\Scripts\python app.py
```
This executes health checks, simulates a valid fundus image through IQA, DR grading, and biomarkers, and verifies ungradable blur safety rejection.

### 4. Running Both Frontend and Backend (Single Command)

To run both the FastAPI backend and Next.js frontend together with one command:

```bash
# Option A: Using the Python unified runner
python run.py

# Option B: Using npm
npm start
# or
npm run dev
```

This launches:
- **Frontend Web UI**: [http://localhost:3000](http://localhost:3000)
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Diagnostics**: [http://localhost:8000/health](http://localhost:8000/health)

Pressing `Ctrl+C` in your terminal cleanly shuts down both processes.

---

### 5. Running Components Individually (Optional)

```bash
# Run only FastAPI backend:
npm run backend

# Run only Next.js frontend:
npm run frontend
```

---

## Running Automated Tests

Run the complete 74-test verification suite:
```bash
.\backend\venv\Scripts\python -m pytest tests/ -v
```

---

## Clinical Safety Disclaimers

Netra is an assistive clinical decision-support tool designed for population screening and triage assistance. Automated outputs, including ICDR grades, lesion counts, and macular proximity indicators, must be reviewed and confirmed by an ophthalmologist or trained medical specialist before any surgical, pharmaceutical, or clinical intervention is made. Autonomous Diabetic Macular Edema (DME) diagnosis requires Optical Coherence Tomography (OCT) confirmation.
