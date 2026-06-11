"""Tests for iva.infrastructure.diagnostics.output_paths."""

from __future__ import annotations

from pathlib import Path

from iva.infrastructure.diagnostics.output_paths import (
    ensure_out_subdir,
    get_logs_dir,
    get_out_dir,
    get_project_root,
)


def test_get_out_dir_default() -> None:
    root = get_project_root()
    assert get_out_dir() == root / "out"


def test_get_out_dir_env_override(monkeypatch: object, tmp_path: Path) -> None:

    monkeypatch.setenv("IVA_OUT_DIR", str(tmp_path))  # type: ignore[attr-defined]
    assert get_out_dir() == tmp_path


def test_ensure_out_subdir_creates_dir(monkeypatch: object, tmp_path: Path) -> None:
    monkeypatch.setenv("IVA_OUT_DIR", str(tmp_path))  # type: ignore[attr-defined]
    d = ensure_out_subdir("logs")
    assert d.exists()
    assert d == tmp_path / "logs"


def test_get_logs_dir_creates_dir(monkeypatch: object, tmp_path: Path) -> None:
    monkeypatch.setenv("IVA_OUT_DIR", str(tmp_path))  # type: ignore[attr-defined]
    d = get_logs_dir()
    assert d.exists()


def test_get_project_root_is_directory() -> None:
    root = get_project_root()
    assert root.is_dir()


def test_get_project_root_contains_pyproject() -> None:
    """Sanity check: project root should have pyproject.toml."""
    root = get_project_root()
    assert (root / "pyproject.toml").exists()
