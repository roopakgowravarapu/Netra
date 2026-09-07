# Netra - Explainable AI for Diabetic Retinopathy Screening in Rural India

**Smart India Hackathon 2026 Project**

Netra is an end-to-end Explainable AI (XAI) screening platform designed for rural healthcare settings to detect Diabetic Retinopathy (DR) from fundus images, evaluate image quality, quantify uncertainty, and generate clinical screening reports.

---

## System Architecture Flow

```text
User / Clinician
      ↓
Netra Web Frontend (Next.js + TypeScript)
      ↓
Python AI Backend (FastAPI REST API)
      ↓
Image Quality Assessment (IQA)
      ↓
DR Classification (Level 0–4)
      ↓
Confidence & Uncertainty Estimation
      ↓
Explainable AI (Grad-CAM Saliency Maps)
      ↓
Screening Report Synthesis
      ↓
Display Diagnosis & Explanation on Web Frontend
```

---

## Directory Structure

```text
Netra/
├── frontend/             # Next.js (TypeScript, React, CSS Modules/Globals)
│   ├── app/              # App Router pages and global styles
│   ├── package.json      # Frontend package manifest & scripts
│   └── tsconfig.json     # TypeScript configuration
│
├── backend/              # Python FastAPI REST API server
│   ├── app/              # FastAPI application modules
│   │   ├── __init__.py
│   │   └── main.py       # FastAPI entrypoint (GET /health)
│   ├── venv/             # Python Virtual Environment
│   └── requirements.txt  # Core dependencies (fastapi, uvicorn, pytest, httpx)
│
├── ai/                   # Future AI pipeline modules (IQA, Classifier, Grad-CAM, Reports)
│   └── README.md
│
├── data/                 # Raw and preprocessed fundus image datasets (gitignored)
│   └── .gitkeep
│
├── models/               # Model weights, checkpoints, and artifacts (gitignored)
│   └── .gitkeep
│
├── outputs/              # Generated reports, heatmaps, and evaluation metrics (gitignored)
│   └── .gitkeep
│
├── tests/                # Automated test suite for backend API & core functions
│   ├── __init__.py
│   └── test_health.py    # Health check endpoint test
│
└── README.md             # Project documentation and setup guide
```

---

## Getting Started

### 1. Prerequisites
- Python 3.12+
- Node.js v20+ / npm v10+

### 2. Backend Setup & Run

Navigate to the `backend/` directory or run from the root:

```bash
# Activate virtual environment
# Windows PowerShell:
.\backend\venv\Scripts\Activate.ps1

# Start FastAPI dev server
backend/venv/Scripts/python -m uvicorn backend.app.main:app --reload --port 8000
```

Backend will be accessible at:
- **API Base**: `http://localhost:8000`
- **Health Check**: `http://localhost:8000/health`
- **Swagger Docs**: `http://localhost:8000/docs`

### 3. Running Backend Tests

```bash
backend/venv/Scripts/pytest tests/
```

### 4. Frontend Setup & Run

Navigate to the `frontend/` directory:

```bash
cd frontend
npm run dev
```

Frontend will be accessible at: `http://localhost:3000`

---

## Development Plan & Rules
1. **Initial Setup**: Project structure, virtual environment, health-check endpoint, basic frontend UI placeholder.
2. **Datasets**: Dataset ingestion & preprocessing pipeline (to be added in subsequent phase).
3. **AI Models**: Model training, Image Quality Assessment, DR grading (Level 0-4), Grad-CAM explainability, and report generation (to be added in subsequent phase).
