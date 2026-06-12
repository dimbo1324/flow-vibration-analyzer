"""Tests for scripts/clean_project.py — safe cross-platform cleanup."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "scripts"
sys.path.insert(0, str(_SCRIPTS_DIR))

import clean_project  # noqa: E402


def _make_fake_repo(root: Path) -> dict[str, Path]:
    """Create a miniature repository with sources and generated artifacts."""
    paths: dict[str, Path] = {}

    # Protected source/content files that must never be touched.
    paths["source"] = root / "iva" / "core" / "module.py"
    paths["doc"] = root / "docs" / "00_overview.md"
    paths["test"] = root / "tests" / "test_x.py"
    paths["config"] = root / "config" / "defaults.toml"
    paths["example"] = root / "data" / "examples" / "demo.csv"
    for p in paths.values():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("content", encoding="utf-8")

    # Generated artifacts that should be removed.
    paths["pycache"] = root / "iva" / "core" / "__pycache__"
    paths["pycache"].mkdir()
    (paths["pycache"] / "module.cpython-311.pyc").write_text("x", encoding="utf-8")
    paths["build"] = root / "build"
    paths["build"].mkdir()
    (paths["build"] / "artifact.bin").write_text("x", encoding="utf-8")
    paths["out"] = root / "out"
    (paths["out"] / "logs").mkdir(parents=True)
    (paths["out"] / "logs" / "run.log").write_text("x", encoding="utf-8")
    paths["coverage"] = root / ".coverage"
    paths["coverage"].write_text("x", encoding="utf-8")
    return paths


def test_dry_run_deletes_nothing(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    paths = _make_fake_repo(tmp_path)
    rc = clean_project.main(["--dry-run", "--root", str(tmp_path)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "DRY RUN" in out
    # Everything still exists, artifacts included.
    for p in paths.values():
        assert p.exists(), f"dry-run must not delete {p}"


def test_force_removes_artifacts_and_preserves_sources(tmp_path: Path) -> None:
    paths = _make_fake_repo(tmp_path)
    rc = clean_project.main(["--force", "--root", str(tmp_path)])
    assert rc == 0
    # Artifacts removed.
    assert not paths["pycache"].exists()
    assert not paths["build"].exists()
    assert not paths["out"].exists()
    assert not paths["coverage"].exists()
    # Protected content untouched.
    for key in ("source", "doc", "test", "config", "example"):
        assert paths[key].exists(), f"{key} must survive cleanup"


def test_keep_logs_preserves_out_directory(tmp_path: Path) -> None:
    paths = _make_fake_repo(tmp_path)
    rc = clean_project.main(["--force", "--keep-logs", "--root", str(tmp_path)])
    assert rc == 0
    assert paths["out"].exists()
    assert not paths["build"].exists()


def test_is_safe_to_remove_rejects_protected_paths(tmp_path: Path) -> None:
    _make_fake_repo(tmp_path)
    forbidden = [
        tmp_path / "iva",
        tmp_path / "iva" / "core" / "module.py",
        tmp_path / "docs" / "00_overview.md",
        tmp_path / "tests" / "test_x.py",
        tmp_path / "config" / "defaults.toml",
        tmp_path / "data" / "examples" / "demo.csv",
        tmp_path,  # the root itself
        tmp_path.parent,  # outside the root
    ]
    for path in forbidden:
        assert not clean_project.is_safe_to_remove(path, tmp_path), path


def test_is_safe_to_remove_accepts_artifacts(tmp_path: Path) -> None:
    paths = _make_fake_repo(tmp_path)
    allowed = [
        paths["pycache"],
        paths["pycache"] / "module.cpython-311.pyc",
        paths["build"],
        paths["out"],
        paths["coverage"],
    ]
    for path in allowed:
        assert clean_project.is_safe_to_remove(path, tmp_path), path


def test_never_traverses_venv_or_git(tmp_path: Path) -> None:
    _make_fake_repo(tmp_path)
    cached = tmp_path / ".venv" / "lib" / "__pycache__"
    cached.mkdir(parents=True)
    directories, _files = clean_project.collect_targets(tmp_path, keep_logs=False)
    assert cached not in directories
    assert not clean_project.is_safe_to_remove(cached, tmp_path)


def test_cli_flags_exist() -> None:
    source = (_SCRIPTS_DIR / "clean_project.py").read_text(encoding="utf-8")
    for flag in ("--dry-run", "--force", "--keep-logs"):
        assert flag in source


def test_nothing_to_clean_returns_zero(tmp_path: Path) -> None:
    (tmp_path / "iva").mkdir()
    rc = clean_project.main(["--dry-run", "--root", str(tmp_path)])
    assert rc == 0
