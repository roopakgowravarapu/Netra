"""Case Repository managing persistent storage of screening cases."""

import json
from pathlib import Path
from typing import Dict, List, Optional
from threading import Lock

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.repositories.base import BaseRepository
from backend.app.schemas.cases import ScreeningCaseSchema


class CaseRepository(BaseRepository[ScreeningCaseSchema, str]):
    """Thread-safe persistent JSON-backed repository for Screening Cases."""

    def __init__(self, store_path: Optional[Path] = None):
        self.store_path = store_path or settings.CASES_STORE_PATH
        self._db: Dict[str, ScreeningCaseSchema] = {}
        self._lock = Lock()
        self._load()

    def _load(self) -> None:
        with self._lock:
            if self.store_path.exists():
                try:
                    with open(self.store_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        self._db = {k: ScreeningCaseSchema(**v) for k, v in data.items()}
                except Exception as e:
                    logger.warning(f"Error loading cases store from {self.store_path}: {e}")
                    self._db = {}

    def _save(self) -> None:
        try:
            self.store_path.parent.mkdir(parents=True, exist_ok=True)
            data = {k: v.model_dump() for k, v in self._db.items()}
            with open(self.store_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error persisting cases to {self.store_path}: {e}")

    def get_by_id(self, case_id: str) -> Optional[ScreeningCaseSchema]:
        with self._lock:
            return self._db.get(case_id)

    def get_all(self) -> List[ScreeningCaseSchema]:
        with self._lock:
            return list(self._db.values())

    def save(self, entity: ScreeningCaseSchema) -> ScreeningCaseSchema:
        with self._lock:
            self._db[entity.case_id] = entity
            self._save()
        return entity

    def delete(self, case_id: str) -> bool:
        with self._lock:
            if case_id in self._db:
                del self._db[case_id]
                self._save()
                return True
            return False

    def clear_all(self) -> int:
        with self._lock:
            count = len(self._db)
            self._db.clear()
            self._save()
            return count

    def clear(self) -> None:
        with self._lock:
            self._db.clear()
            self._save()


# Singleton repository instance
case_repository = CaseRepository()
