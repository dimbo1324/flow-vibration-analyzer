"""Regression tests for Windows packaging and environment hygiene.

Covers the failure modes reported on a real Windows 11 setup:
- `pip install -e .` aborting on setuptools flat-layout auto-discovery;
- smoke-test scripts leaking QT_QPA_PLATFORM=offscreen into the interactive
  session, which made the next GUI launch render invisibly;
- a frozen (PyInstaller) build writing output into the read-only install
  directory under Program Files.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[3]


# ---------------------------------------------------------------------------
# pyproject packaging (editable install regression)
# ---------------------------------------------------------------------------


def test_pyproject_declares_build_system_and_packages() -> None:
    text = (_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "[build-system]" in text
    assert "setuptools.build_meta" in text
    assert "[tool.setuptools.packages.find]" in text
    assert '"iva*"' in text


# ---------------------------------------------------------------------------
# PowerShell env hygiene (offscreen leak regression)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("script", ["setup.ps1", "run.ps1"])
def test_smoke_scripts_restore_qt_platform(script: str) -> None:
    text = (_ROOT / "scripts" / script).read_text(encoding="utf-8")
    # Save/restore pattern around the offscreen smoke-test block.
    assert "$savedQpa" in text, f"{script} must save QT_QPA_PLATFORM before smoke test"
    assert "finally" in text, f"{script} must restore environment in a finally block"
    assert "$env:QT_QPA_PLATFORM = $savedQpa" in text


def test_run_script_clears_offscreen_for_gui_launch() -> None:
    text = (_ROOT / "scripts" / "run.ps1").read_text(encoding="utf-8")
    assert "Remove-Item Env:QT_QPA_PLATFORM" in text


def test_main_guards_against_offscreen_gui_launch() -> None:
    text = (_ROOT / "main.py").read_text(encoding="utf-8")
    assert 'os.environ.get("QT_QPA_PLATFORM") == "offscreen"' in text
    assert '"--smoke-test" not in sys.argv' in text


# ---------------------------------------------------------------------------
# Frozen-aware output/resource paths (installed-app stability)
# ---------------------------------------------------------------------------


def test_get_out_dir_dev_mode_uses_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from iva.infrastructure.diagnostics import output_paths

    monkeypatch.delenv("IVA_OUT_DIR", raising=False)
    assert output_paths.get_out_dir() == output_paths.get_project_root() / "out"


def test_get_out_dir_env_override_wins(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from iva.infrastructure.diagnostics import output_paths

    monkeypatch.setenv("IVA_OUT_DIR", str(tmp_path / "custom"))
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    assert output_paths.get_out_dir() == tmp_path / "custom"


def test_get_out_dir_frozen_uses_documents(monkeypatch: pytest.MonkeyPatch) -> None:
    from iva.infrastructure.diagnostics import output_paths

    monkeypatch.delenv("IVA_OUT_DIR", raising=False)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    out = output_paths.get_out_dir()
    # Must NOT point inside the (read-only) install/bundle directory.
    assert "Documents" in str(out)
    assert out.name == "out"
    assert "IVA" in out.parts


def test_get_resource_root_frozen_uses_meipass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from iva.infrastructure.diagnostics import output_paths

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    assert output_paths.get_resource_root() == tmp_path


def test_get_resource_root_dev_is_repo_root() -> None:
    from iva.infrastructure.diagnostics import output_paths

    root = output_paths.get_resource_root()
    assert (root / "config" / "defaults.toml").exists()
    assert (root / "config" / "strouhal_tables.toml").exists()


def test_build_requirements_file_lists_pyinstaller() -> None:
    text = (_ROOT / "requirements-build.txt").read_text(encoding="utf-8")
    assert "pyinstaller" in text
    assert "-r requirements.txt" in text
