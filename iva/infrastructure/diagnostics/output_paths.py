"""Utility functions for resolving project output directories."""

from __future__ import annotations

import os
from pathlib import Path


def get_project_root() -> Path:
    """Return project root (parent of this file's package)."""
    return Path(__file__).resolve().parents[3]


def get_out_dir() -> Path:
    """Return base output directory. Override with IVA_OUT_DIR env var."""
    env = os.environ.get("IVA_OUT_DIR")
    if env:
        return Path(env)
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
