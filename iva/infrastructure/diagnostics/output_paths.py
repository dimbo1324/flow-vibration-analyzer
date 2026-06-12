"""Utility functions for resolving project output and resource directories.

These helpers are frozen-aware: when the application runs as a PyInstaller
executable (installed e.g. under ``C:\\Program Files\\IVA``), generated output
must NOT be written next to the executable — that directory is read-only for
normal users.  In that case ``out/`` is redirected to the per-user documents
folder, matching where the application logger already writes.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def is_frozen() -> bool:
    """Return True when running as a bundled (PyInstaller) executable."""
    return bool(getattr(sys, "frozen", False))


def get_resource_root() -> Path:
    """Return the directory that holds bundled read-only resources.

    Frozen: the PyInstaller extraction/_internal directory (``sys._MEIPASS``),
    where the spec file places ``config/`` and ``data/examples/``.
    Development: the repository root.
    """
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return get_project_root()


def get_project_root() -> Path:
    """Return project root (parent of this file's package)."""
    return Path(__file__).resolve().parents[3]


def _get_user_documents_out_dir() -> Path:
    """Writable per-user output directory for the installed application."""
    userprofile = os.environ.get("USERPROFILE")
    base = Path(userprofile) if userprofile else Path.home()
    return base / "Documents" / "IVA" / "out"


def get_out_dir() -> Path:
    """Return base output directory. Override with IVA_OUT_DIR env var.

    Frozen executables write to ``Documents/IVA/out`` because the install
    directory (Program Files) is not writable for regular users.
    """
    env = os.environ.get("IVA_OUT_DIR")
    if env:
        return Path(env)
    if is_frozen():
        return _get_user_documents_out_dir()
    return get_project_root() / "out"


def ensure_out_subdir(name: str) -> Path:
    """Create and return out/<name>/ directory."""
    d = get_out_dir() / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_logs_dir() -> Path:
    return ensure_out_subdir("logs")


def get_test_results_dir() -> Path:
    return ensure_out_subdir("test-results")


def get_workflow_runs_dir() -> Path:
    return ensure_out_subdir("workflow-runs")


def get_cli_runs_dir() -> Path:
    return ensure_out_subdir("cli-runs")


def get_diagnostics_dir() -> Path:
    return ensure_out_subdir("diagnostics")
