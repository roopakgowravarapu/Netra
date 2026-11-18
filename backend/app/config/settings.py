"""Backward-compatible re-export of application settings from backend.app.core.config."""

from backend.app.core.config import Settings, settings

__all__ = ["Settings", "settings"]
