"""Subprocess tests for the CLI demo command."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "iva.cli.main", *args],
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_cli_lists_demo_scenarios() -> None:
    result = _run_cli("demo", "--list-scenarios")
    assert result.returncode == 0
    assert "clean_40hz" in result.stdout
    assert "Чистый сигнал 40 Гц" in result.stdout
    assert "critical_risk" in result.stdout
    assert "�" not in result.stdout


def test_cli_demo_exports_html_and_project(tmp_path: Path) -> None:
    output_dir = tmp_path / "demo"
    result = _run_cli(
        "demo",
        "--scenario",
        "clean_40hz",
        "--output",
        str(output_dir),
        "--export-html",
        "--save-project",
    )
    assert result.returncode == 0, result.stderr
    assert "Используется демонстрационный синтетический сигнал" in result.stdout
    assert "Доминирующий пик" in result.stdout
    assert "Общий RMS" in result.stdout
    assert "�" not in result.stdout
    assert (output_dir / "report.html").exists()
    assert (output_dir / "project.vibproj").exists()
    assert (output_dir / "signal.csv").exists()
