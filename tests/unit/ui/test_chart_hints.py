"""Headless tests for the chart usability hint label."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # type: ignore[import-untyped]

from iva.ui.strings_ru import tr
from iva.ui.widgets.chart_widget import ChartWidget


def _qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_chart_widget_shows_russian_usage_hints() -> None:
    _qapp()
    chart = ChartWidget()
    assert hasattr(chart, "_hint_label"), "chart must expose a usage hint label"
    text = chart._hint_label.text()
    assert "масштаб" in text
    assert "панорама" in text
    assert "F" in text and "Esc" in text
    chart.close()


def test_chart_hints_string_is_localized() -> None:
    translated = tr("Chart hints")
    assert translated != "Chart hints", "hint string must have a Russian translation"
    assert "Колесо мыши" in translated
