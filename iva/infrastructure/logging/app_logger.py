"""Daily-rotating file logger for the Industrial Vibration Analyzer.

Each call to ``get_logger`` returns a stdlib Logger configured with a handler
that writes to a date-based file under the user's Documents folder.

Log directory resolution order (production default):
    1. Environment variable ``IVA_LOG_DIR`` if set (useful for tests/CI so
       no permanent files are written into the real user Documents folder).
    2. ``%USERPROFILE%/Documents/IVA/logs`` on Windows.
    3. ``~/Documents/IVA/logs`` as a cross-platform fallback.

Log format::

    %(asctime)s.%(msecs)03d  %(levelname)-8s  %(name)s  %(message)s

Example log file path::

    C:/Users/engineer/Documents/IVA/logs/iva_2025-06-11.log

Retention: log files matching ``iva_*.log`` older than 30 days are removed
whenever a new handler is set up.  Deletion errors are silently ignored so
that a locked or read-only file cannot crash the application.
"""

from __future__ import annotations

import logging
import os
from datetime import date, timedelta
from pathlib import Path

__all__ = ["get_logger"]

_LOG_FORMAT = "%(asctime)s.%(msecs)03d  %(levelname)-8s  %(name)s  %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_RETENTION_DAYS = 30


def _get_log_dir() -> Path:
    """Return the resolved log directory path.

    Checks ``IVA_LOG_DIR`` first so that tests can redirect logs without
    touching the production Documents folder.
    """
    env_override = os.environ.get("IVA_LOG_DIR")
    if env_override:
        return Path(env_override)

    userprofile = os.environ.get("USERPROFILE")
    if userprofile:
        base = Path(userprofile)
    else:
        base = Path.home()

    return base / "Documents" / "IVA" / "logs"


def _purge_old_logs(log_dir: Path) -> None:
    """Delete ``iva_*.log`` files older than ``_RETENTION_DAYS`` days."""
    cutoff = date.today() - timedelta(days=_RETENTION_DAYS)
    try:
        for log_file in log_dir.glob("iva_*.log"):
            # Extract YYYY-MM-DD from filename like iva_2025-01-01.log
            stem = log_file.stem  # e.g. "iva_2025-01-01"
            date_part = stem[4:]  # drop "iva_"
            try:
                file_date = date.fromisoformat(date_part)
            except ValueError:
                continue
            if file_date < cutoff:
                try:
                    log_file.unlink()
                except OSError:
                    pass  # locked, read-only or already gone — ignore
    except OSError:
        pass


def get_logger(name: str) -> logging.Logger:
    """Return a Logger writing to today's date-based log file.

    If the logger for *name* already has a FileHandler pointing at today's
    log file, it is returned as-is to avoid duplicate handlers being added
    on repeated calls.

    Args:
        name: Qualified logger name, typically ``__name__`` of the caller.

    Returns:
        A stdlib :class:`logging.Logger` instance.
    """
    logger = logging.getLogger(name)

    # Only configure if not already done at DEBUG level with a file handler.
    today_str = date.today().isoformat()
    log_dir = _get_log_dir()
    log_file = log_dir / f"iva_{today_str}.log"

    # Check whether this exact file handler already exists to prevent
    # duplicate handler accumulation across multiple get_logger() calls.
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            if Path(handler.baseFilename).resolve() == log_file.resolve():
                return logger

    # Create the log directory (and any intermediate directories).
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        # Cannot create log dir — fall back to a NullHandler silently.
        if not logger.handlers:
            logger.addHandler(logging.NullHandler())
        return logger

    _purge_old_logs(log_dir)

    formatter = logging.Formatter(fmt=_LOG_FORMAT, datefmt=_DATE_FORMAT)
    try:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
    except OSError:
        if not logger.handlers:
            logger.addHandler(logging.NullHandler())
        return logger

    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    logger.addHandler(file_handler)
    logger.setLevel(logging.DEBUG)
    # Prevent messages from propagating to the root logger's handlers
    # (avoids duplicate output if root logger has its own handlers).
    logger.propagate = False

    return logger
