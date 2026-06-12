"""Лёгкая защита русских пояснений в ключевых инженерных файлах."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CYRILLIC = re.compile(r"[А-Яа-яЁё]")

FILES_WITH_RUSSIAN_EXPLANATIONS = (
    "scripts/iva.ps1",
    "scripts/clean.ps1",
    "scripts/clean_project.py",
    "scripts/build_installer.py",
    "scripts/diagnose_project.py",
    "iva/app/workflow_coordinator.py",
    "iva/infrastructure/session/session_serializer.py",
    "iva/ui/analysis_worker.py",
    "iva/ui/widgets/chart_widget.py",
)


@pytest.mark.parametrize("relative_path", FILES_WITH_RUSSIAN_EXPLANATIONS)
def test_key_file_contains_russian_explanation(relative_path: str) -> None:
    text = (ROOT / relative_path).read_text(encoding="utf-8")
    assert CYRILLIC.search(text), f"В {relative_path} нет русского инженерного пояснения"
