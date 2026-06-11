"""Shared pytest configuration for the Industrial Vibration Analyzer test suite.

This module is imported by pytest before any test module (and therefore before
the infrastructure readers/validators import their module-level loggers).  We
set ``IVA_LOG_DIR`` to a temporary directory here so the suite never writes log
files into the real user Documents folder.  ``app_logger`` honours this
override (see iva/infrastructure/logging/app_logger.py).

``setdefault`` is used so an explicitly provided ``IVA_LOG_DIR`` (e.g. in CI)
is respected.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

os.environ.setdefault("IVA_LOG_DIR", str(Path(tempfile.gettempdir()) / "iva_test_logs"))
