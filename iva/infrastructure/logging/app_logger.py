"""Minimal logging helper for the Industrial Vibration Analyzer.

This module provides a single factory function.  It does not configure
handlers, file paths or formatters at import time — that is the responsibility
of the application entry point.  Each module that needs a logger calls
``get_logger(__name__)`` and the returned logger inherits whatever handlers the
root logger has configured at runtime.
"""

from __future__ import annotations

import logging

__all__ = ["get_logger"]


def get_logger(name: str) -> logging.Logger:
    """Return a standard-library logger for the given qualified name.

    Usage inside any IVA module::

        from iva.infrastructure.logging.app_logger import get_logger
        logger = get_logger(__name__)
    """
    return logging.getLogger(name)
