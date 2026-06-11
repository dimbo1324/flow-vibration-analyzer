"""Localization contract tests for the command-line interface."""

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


def test_cli_help_is_russian_without_replacement_characters() -> None:
    proc = _run_cli("--help")
    assert proc.returncode == 0
    assert "интерфейс командной строки" in proc.stdout
    assert "Выполнить полный анализ" in proc.stdout
    assert "�" not in proc.stdout
    assert "IVA ?" not in proc.stdout


def test_analyze_help_localizes_options() -> None:
    proc = _run_cli("analyze", "--help")
    assert proc.returncode == 0
    assert "Путь к входному файлу данных" in proc.stdout
    assert "показать эту справку и выйти" in proc.stdout


def test_cli_failure_is_russian(tmp_path: Path) -> None:
    proc = _run_cli(
        "analyze",
        "--data",
        str(tmp_path / "missing.csv"),
        "--config",
        str(tmp_path / "missing.json"),
        "--output",
        str(tmp_path / "out"),
    )
    assert proc.returncode == 1
    assert "Ошибка:" in proc.stderr
    assert "Файл конфигурации не найден" in proc.stderr
    assert "Как исправить:" in proc.stderr


def test_cli_argument_error_is_russian() -> None:
    proc = _run_cli("analyze")
    assert proc.returncode == 2
    assert "ошибка:" in proc.stderr
    assert "не указаны обязательные аргументы" in proc.stderr
