"""Tests verifying PowerShell helper scripts exist and are well-formed."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "scripts"

REQUIRED_SCRIPTS = [
    "setup.ps1",
    "run.ps1",
    "clean.ps1",
    "clean-logs.ps1",
    "build-all.ps1",
    "lint.ps1",
    "test.ps1",
    "quality.ps1",
]


@pytest.mark.parametrize("name", REQUIRED_SCRIPTS)
def test_script_exists(name):
    assert (SCRIPTS / name).is_file(), f"Missing script: {name}"


@pytest.mark.parametrize("name", REQUIRED_SCRIPTS)
def test_script_has_no_user_specific_paths(name):
    text = (SCRIPTS / name).read_text(encoding="utf-8")
    assert "C:\\Users\\Users" not in text
    assert "C:/Users/Users" not in text


@pytest.mark.parametrize("name", REQUIRED_SCRIPTS)
def test_script_has_exit_code(name):
    text = (SCRIPTS / name).read_text(encoding="utf-8")
    assert "exit" in text.lower()


@pytest.mark.parametrize("name", REQUIRED_SCRIPTS)
def test_script_declares_parameters(name):
    text = (SCRIPTS / name).read_text(encoding="utf-8")
    assert "param(" in text.lower()


@pytest.mark.parametrize("name", REQUIRED_SCRIPTS)
def test_script_has_status_output(name):
    text = (SCRIPTS / name).read_text(encoding="utf-8")
    assert any(marker in text for marker in ("[OK]", "[FAILED]", "[INFO]", "Write-Status"))


def test_clean_supports_flags():
    text = (SCRIPTS / "clean.ps1").read_text(encoding="utf-8")
    assert "DryRun" in text
    assert "Force" in text
    assert "KeepLogs" in text


def test_run_supports_smoketest():
    text = (SCRIPTS / "run.ps1").read_text(encoding="utf-8")
    assert "SmokeTest" in text


def test_build_all_supports_checkonly():
    text = (SCRIPTS / "build-all.ps1").read_text(encoding="utf-8")
    assert "CheckOnly" in text


def test_setup_supports_flags():
    text = (SCRIPTS / "setup.ps1").read_text(encoding="utf-8")
    assert "NoEditable" in text
    assert "SkipSmokeTest" in text


def test_clean_preserves_virtual_environment():
    text = (SCRIPTS / "clean.ps1").read_text(encoding="utf-8")
    assert '".venv"' in text
    assert '"venv"' in text


def test_clean_logs_supports_safe_flags():
    text = (SCRIPTS / "clean-logs.ps1").read_text(encoding="utf-8")
    for flag in ("OlderThanDays", "Force", "DryRun", "CleanResults"):
        assert flag in text


def test_build_all_forwards_build_flags():
    text = (SCRIPTS / "build-all.ps1").read_text(encoding="utf-8")
    assert "--check-only" in text
    assert "--skip-tests" in text
    assert "quality.ps1" in text
