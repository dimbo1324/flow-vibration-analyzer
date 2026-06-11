"""Headless GUI tests for Stage 9 widgets and pages."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PySide6.QtWidgets import QApplication

from iva.ui.pages.profiles_page import ProfilesPage
from iva.ui.pages.report_page import ReportPage
from iva.ui.widgets.chart_widget import ChartWidget


@pytest.fixture(scope="module", autouse=True)
def application() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_chart_widget_plot_reset_cursor_and_png(tmp_path: Path) -> None:
    widget = ChartWidget()
    x = np.linspace(0.0, 1.0, 100)
    widget.plot_signal(x, np.sin(2 * np.pi * x))
    widget.enable_cursor_inspection(True)
    assert widget._cursor_enabled is True
    widget.reset_view()
    widget.plot_psd(x + 0.01, np.linspace(0.01, 1.0, 100))
    path = widget.export_png(tmp_path / "chart.png")
    assert path.exists() and path.stat().st_size > 0
    widget.enable_cursor_inspection(False)
    assert widget._cursor_enabled is False
    widget.close()


def test_report_page_becomes_ready(stage9_result) -> None:
    page = ReportPage()
    page.on_analysis_completed(stage9_result)
    assert page._result is stage9_result
    assert page._pdf_btn.isEnabled()
    assert page._html_btn.isEnabled()
    assert "Результат готов" in page._readiness_label.text()
    page.close()


def test_profiles_page_displays_validation(stage9_result) -> None:
    page = ProfilesPage()
    page.on_analysis_completed(stage9_result)
    assert page._metrics_table.rowCount() == 4
    assert page._metrics_table.item(0, 0).text() == "RMSE"
    page.close()
