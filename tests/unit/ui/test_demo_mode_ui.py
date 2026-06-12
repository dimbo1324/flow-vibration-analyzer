"""Headless-safe tests for demo quick-start controls."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from iva.core.models.enums import SignalRole
from iva.ui.main_window import MainWindow
from iva.ui.pages.import_page import ImportPage
from iva.ui.pages.overview_page import OverviewPage


def _qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_overview_has_quick_start_controls() -> None:
    _qapp()
    page = OverviewPage()
    assert page._quick_open_button.text() == "Открыть файл данных"
    assert page._quick_demo_button.text() == "Запустить демо-анализ"
    assert page._quick_project_button.text() == "Открыть проект .vibproj"
    page.close()


def test_import_page_has_demo_selector_and_button() -> None:
    _qapp()
    page = ImportPage()
    assert page._demo_selector.count() >= 6
    assert page._demo_button.text() == "Загрузить демо-сценарий"
    assert page.selected_demo_key() == "clean_40hz"
    page.set_demo_session(
        "Чистый сигнал 40 Гц",
        "Описание",
        Path("demo.csv"),
        1000.0,
        SignalRole.ACCELERATION_X,
    )
    assignment = page.get_role_assignment()
    assert assignment is not None
    assert assignment.time_column == "time_s"
    assert assignment.primary_signal_column == "signal"
    page.close()


def test_main_window_exposes_demo_workflow() -> None:
    _qapp()
    window = MainWindow()
    assert callable(window.run_demo_analysis)
    window.close()
