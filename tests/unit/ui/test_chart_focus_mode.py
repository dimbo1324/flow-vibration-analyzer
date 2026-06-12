"""Headless tests for chart focus requests and workspace restoration."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # type: ignore[import-untyped]

from iva.ui.main_window import MainWindow
from iva.ui.pages.overview_page import OverviewPage
from iva.ui.widgets.chart_widget import ChartWidget


def _qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_chart_widget_exposes_focus_request_signal() -> None:
    _qapp()
    chart = ChartWidget()
    requested: list[object] = []
    chart.focus_requested.connect(requested.append)
    chart.request_focus()
    assert requested == [chart]
    chart.close()


def test_main_window_enters_and_exits_chart_focus_mode(stage9_result) -> None:  # type: ignore[no-untyped-def]
    _qapp()
    window = MainWindow()
    overview = window._pages[0]
    assert isinstance(overview, OverviewPage)
    overview.on_analysis_completed(stage9_result)

    window.enter_chart_focus_mode(overview._signal_chart)
    assert window._focus_mode is True
    assert window._workspace_stack.currentWidget() is window._focus_container
    assert window._sidebar_panel.isHidden()
    assert window._focus_chart._last_plot is not None

    window.exit_chart_focus_mode()
    assert window._focus_mode is False
    assert window._workspace_stack.currentWidget() is window._stack
    assert not window._sidebar_panel.isHidden()
    window.close()
