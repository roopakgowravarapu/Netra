"""Structured logging configuration for Netra backend."""

import logging
import sys


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configures structured console logging for the application."""
    log_format = "%(asctime)s | %(levelname)-7s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
    formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    logger = logging.getLogger("netra")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Avoid duplicate handlers if already configured
    if not logger.handlers:
        logger.addHandler(handler)

    return logger


logger = setup_logging()
