"""Tests for the dependency-free Russian UI string catalog."""

from __future__ import annotations

from pathlib import Path

import iva.ui.strings_ru as strings_ru
from iva.ui.strings_ru import (
    GEOMETRY_LABELS,
    RISK_LABELS,
    SIGNAL_ROLE_LABELS,
    display_label,
    source_value,
    tr,
)


def test_catalog_import_does_not_load_pyside() -> None:
    source = Path(strings_ru.__file__).read_text(encoding="utf-8")
    assert "PySide6" not in source


def test_primary_navigation_and_actions_are_russian() -> None:
    assert tr("01  Overview") == "01  Сводка"
    assert tr("Run Analysis  (F5)") == "Запустить анализ  (F5)"
    assert tr("07 — Report") == "07 — Отчёт"


def test_risk_labels_preserve_stable_source_values() -> None:
    assert display_label(RISK_LABELS, "safe") == "БЕЗОПАСНО"
    assert display_label(RISK_LABELS, "watch") == "НАБЛЮДЕНИЕ"
    assert display_label(RISK_LABELS, "critical") == "КРИТИЧЕСКИЙ"


def test_enum_display_labels_round_trip() -> None:
    role_label = SIGNAL_ROLE_LABELS["acceleration_x"]
    geometry_label = GEOMETRY_LABELS["single_cylinder"]
    assert source_value(SIGNAL_ROLE_LABELS, role_label) == "acceleration_x"
    assert source_value(GEOMETRY_LABELS, geometry_label) == "single_cylinder"
