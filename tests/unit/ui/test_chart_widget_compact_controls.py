"""Проверяет компактные элементы управления ChartWidget."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # type: ignore[import-untyped]

from iva.ui.widgets.chart_widget import ChartWidget


def _qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_reset_button_exists() -> None:
    _qapp()
    chart = ChartWidget()
    assert hasattr(chart, "_reset_button")
    chart.close()


def test_png_button_exists() -> None:
    _qapp()
    chart = ChartWidget()
    assert hasattr(chart, "_png_button")
    chart.close()


def test_cursor_checkbox_exists() -> None:
    _qapp()
    chart = ChartWidget()
    assert hasattr(chart, "_cursor_checkbox")
    chart.close()


def test_hint_label_text_preserved() -> None:
    _qapp()
    chart = ChartWidget()
    assert hasattr(chart, "_hint_label")
    text = chart._hint_label.text()
    assert "масштаб" in text
    assert "панорама" in text
    chart.close()


def test_hint_label_not_visible_in_controls() -> None:
    _qapp()
    chart = ChartWidget()
    # Метка подсказки скрыта — она занимает место только в tooltip.
    assert not chart._hint_label.isVisible()
    chart.close()


def test_reset_button_compact_width() -> None:
    _qapp()
    chart = ChartWidget()
    # Кнопка «↺» должна быть узкой.
    assert chart._reset_button.maximumWidth() <= 40
    chart.close()
