"""Проверки состава и безопасных контрактов PowerShell-автоматизации."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "scripts"

REQUIRED_SCRIPTS = [
    "iva.ps1",
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
    assert any(
        marker in text
        for marker in ("[OK]", "[FAILED]", "[INFO]", "Write-Status", "Write-IvaStatus")
    )


def test_clean_supports_flags():
    text = (SCRIPTS / "clean.ps1").read_text(encoding="utf-8")
    assert "DryRun" in text
    assert "Force" in text
    assert "KeepLogs" in text
    assert "IncludeVenv" in text


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
    assert "IncludeVenv" in text
    assert '"--include-venv"' in text
    assert "_base_executable" in text


def test_clean_logs_supports_safe_flags():
    text = (SCRIPTS / "clean-logs.ps1").read_text(encoding="utf-8")
    for flag in ("OlderThanDays", "Force", "DryRun", "CleanResults"):
        assert flag in text


def test_build_all_forwards_build_flags():
    text = (SCRIPTS / "build-all.ps1").read_text(encoding="utf-8")
    assert "--check-only" in text
    assert "--skip-tests" in text
    assert "quality.ps1" in text


def test_shared_module_exists_and_exports_expected_helpers():
    module = SCRIPTS / "lib" / "IvaDevTools.psm1"
    assert module.is_file()
    text = module.read_text(encoding="utf-8")
    for helper in (
        "Get-IvaRepositoryRoot",
        "Write-IvaStatus",
        "Invoke-IvaStep",
        "Get-IvaVenvPython",
        "Test-IvaVenv",
        "Set-IvaHeadlessQtEnvironment",
        "Restore-IvaEnvironment",
    ):
        assert helper in text


def test_iva_entrypoint_supports_required_commands():
    text = (SCRIPTS / "iva.ps1").read_text(encoding="utf-8")
    for command in (
        "setup",
        "run",
        "smoke",
        "lint",
        "test",
        "quality",
        "check",
        "diagnose",
        "clean",
        "clean-logs",
        "demo",
        "build-check",
        "build",
        "all",
    ):
        assert f'"{command}"' in text


def test_iva_clean_requires_force_for_deletion():
    text = (SCRIPTS / "iva.ps1").read_text(encoding="utf-8")
    assert "-not $DryRun -and -not $Force" in text
    assert "exit 2" in text


def test_iva_forwards_include_venv_to_clean_script():
    text = (SCRIPTS / "iva.ps1").read_text(encoding="utf-8")
    assert "[switch]$IncludeVenv" in text
    assert '$bound["IncludeVenv"] = $true' in text


def test_build_check_is_before_destructive_build_steps():
    text = (SCRIPTS / "build-all.ps1").read_text(encoding="utf-8")
    check_position = text.index("if ($CheckOnly)")
    clean_position = text.index('clean.ps1" -Force')
    quality_position = text.index('quality.ps1"')
    assert check_position < clean_position
    assert check_position < quality_position


def test_all_powershell_files_avoid_user_specific_paths():
    powershell_files = [*SCRIPTS.rglob("*.ps1"), *SCRIPTS.rglob("*.psm1")]
    forbidden = (r"C:\Users\Users", r"C:\Users\dim", "/home/")
    for path in powershell_files:
        text = path.read_text(encoding="utf-8")
        for fragment in forbidden:
            assert fragment not in text, f"{path.name} contains {fragment!r}"


def test_lint_runs_from_repository_root_for_tool_configuration():
    text = (SCRIPTS / "lint.ps1").read_text(encoding="utf-8")
    assert "Push-Location $repoRoot" in text
    assert "finally" in text
    assert "Pop-Location" in text
