"""Daily-rotating file logger for the Industrial Vibration Analyzer.

Each call to ``get_logger`` returns a stdlib Logger for the given name.
File logging is *not* configured at import time; call
``configure_file_logging()`` once at application startup to attach a
FileHandler.

Log directory resolution order (used by ``configure_file_logging`` when
*log_dir* is not supplied explicitly):
    1. ``get_logs_dir()`` from ``iva.infrastructure.diagnostics.output_paths``
       which itself checks ``IVA_OUT_DIR`` (useful for tests/CI so no
       permanent files are written into real user directories).
    2. Falls back to ``<project_root>/out/logs/`` by default.

Log format::

    %(asctime)s.%(msecs)03d  %(levelname)-8s  %(name)s  %(message)s

Example log file path::

    out/logs/iva_2025-06-11.log

Retention: log files matching ``iva_*.log`` older than *keep_days* days are
removed when ``configure_file_logging`` is called.  Deletion errors are
silently ignored so that a locked or read-only file cannot crash the
application.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from pathlib import Path

__all__ = ["get_logger", "configure_file_logging", "_cleanup_old_logs"]

_LOG_FORMAT = "%(asctime)s.%(msecs)03d  %(levelname)-8s  %(name)s  %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_RETENTION_DAYS = 30

# Root logger name for the IVA application.
_IVA_ROOT = "iva"

# Per Python logging best-practice for libraries: add a NullHandler to the
# package root logger so that log records from ``iva.*`` do not propagate to
# the root logger's default stderr StreamHandler when no file logging has been
# configured.  This prevents tracebacks logged with ``exc_info=True`` from
# leaking to stderr in CLI and test contexts.
logging.getLogger(_IVA_ROOT).addHandler(logging.NullHandler())


def _cleanup_old_logs(log_dir: Path, keep_days: int = 30) -> None:
    """Delete ``iva_*.log`` files older than *keep_days* days.

    Only files matching the ``iva_YYYY-MM-DD.log`` pattern are touched.
    Other files (including unrelated ``.log`` files) are left untouched.
    Deletion failures are silently ignored.
    """
    cutoff = date.today() - timedelta(days=keep_days)
    try:
        for log_file in log_dir.glob("iva_*.log"):
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


def configure_file_logging(
    log_dir: Path | None = None,
    log_level: int = logging.DEBUG,
) -> None:
    """Attach a date-based FileHandler to the ``iva`` root logger.

    Safe to call multiple times; a second call with the *same* log directory
    is a no-op (deduplication by resolved file path).  A call with a
    *different* log directory adds a new handler for that directory.

    Args:
        log_dir: Directory in which to create ``iva_YYYY-MM-DD.log``.
            Defaults to ``get_logs_dir()`` (``out/logs/`` by default,
            overridable via the ``IVA_OUT_DIR`` env var).
        log_level: Minimum level for the file handler.  Defaults to DEBUG.
    """
    if log_dir is None:
        # Import here to avoid a circular import at module level and to allow
        # the env var to be set after this module is first imported.
        from iva.infrastructure.diagnostics.output_paths import get_logs_dir

        log_dir = get_logs_dir()

    today_str = date.today().isoformat()
    log_file = log_dir / f"iva_{today_str}.log"

    root_logger = logging.getLogger(_IVA_ROOT)

    # Deduplication: skip if a FileHandler for this exact file already exists.
    resolved = log_file.resolve()
    for handler in root_logger.handlers:
        if isinstance(handler, logging.FileHandler):
            if Path(handler.baseFilename).resolve() == resolved:
                return

    # Ensure the directory exists.
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        if not root_logger.handlers:
            root_logger.addHandler(logging.NullHandler())
        return

    _cleanup_old_logs(log_dir, keep_days=_RETENTION_DAYS)

    formatter = logging.Formatter(fmt=_LOG_FORMAT, datefmt=_DATE_FORMAT)
    try:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
    except OSError:
        if not root_logger.handlers:
            root_logger.addHandler(logging.NullHandler())
        return

    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)

    root_logger.addHandler(file_handler)
    root_logger.setLevel(log_level)
    # Prevent duplicate output if the root logging logger has handlers.
    root_logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Return a stdlib Logger for the given *name*.

    This function does *not* configure any handlers — call
    ``configure_file_logging()`` at application startup to set up file
    output.  In tests, pass a ``tmp_path``-based directory to
    ``configure_file_logging`` to avoid writing to permanent locations.

    Args:
        name: Qualified logger name, typically ``__name__`` of the caller.

    Returns:
        A stdlib :class:`logging.Logger` instance.
    """
    return logging.getLogger(name)
