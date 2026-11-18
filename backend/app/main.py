"""FastAPI Entrypoint for Netra DR Screening Platform backend."""

import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.config.settings import settings
from backend.app.routes import cases, health, patients, predict

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Explainable AI for Diabetic Retinopathy Screening and Clinical Decision Support",
    version=settings.VERSION,
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount outputs directory as static files for visual explanations & heatmaps
static_path = settings.STATIC_DIR
static_path.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Include API routes
app.include_router(health.router)
app.include_router(predict.router)
app.include_router(cases.router)
app.include_router(patients.router)
