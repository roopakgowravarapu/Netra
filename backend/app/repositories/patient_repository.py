"""Patient Repository managing persistent storage of patient records and visits."""

import json
from pathlib import Path
from typing import Dict, List, Optional
from threading import Lock

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.repositories.base import BaseRepository
from backend.app.schemas.patients import PatientSchema


class PatientRepository(BaseRepository[PatientSchema, str]):
    """Thread-safe persistent JSON-backed repository for Patient demographics & screening visits."""

    def __init__(self, store_path: Optional[Path] = None):
        self.store_path = store_path or settings.PATIENTS_STORE_PATH
        self._db: Dict[str, PatientSchema] = {}
        self._lock = Lock()
        self._load()

    def _load(self) -> None:
        with self._lock:
            if self.store_path.exists():
                try:
                    with open(self.store_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        self._db = {k: PatientSchema(**v) for k, v in data.items()}
                except Exception as e:
                    logger.warning(f"Error loading patients store from {self.store_path}: {e}")
                    self._db = {}

    def _save(self) -> None:
        try:
            self.store_path.parent.mkdir(parents=True, exist_ok=True)
            data = {k: v.model_dump() for k, v in self._db.items()}
            with open(self.store_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error persisting patients to {self.store_path}: {e}")

    def get_by_id(self, patient_id: str) -> Optional[PatientSchema]:
        with self._lock:
            return self._db.get(patient_id)

    def get_all(self, query: Optional[str] = None) -> List[PatientSchema]:
        with self._lock:
            patients = list(self._db.values())
        if query:
            q = query.strip().lower()
            patients = [
                p for p in patients
                if q in p.patient_id.lower() or q in p.name.lower()
            ]
        patients.sort(key=lambda p: p.updated_at, reverse=True)
        return patients

    def save(self, entity: PatientSchema) -> PatientSchema:
        with self._lock:
            self._db[entity.patient_id] = entity
            self._save()
        return entity

    def delete(self, patient_id: str) -> bool:
        with self._lock:
            if patient_id in self._db:
                del self._db[patient_id]
                self._save()
                return True
            return False

    def clear(self) -> None:
        with self._lock:
            self._db.clear()
            self._save()


# Singleton repository instance
patient_repository = PatientRepository()
