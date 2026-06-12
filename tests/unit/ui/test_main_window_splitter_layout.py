"""Headless tests for the splitter-based workstation shell."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt  # type: ignore[import-untyped]
from PySide6.QtWidgets import QApplication  # type: ignore[import-untyped]

from iva.ui.main_window import MainWindow


def _qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_main_window_uses_three_panel_horizontal_splitter() -> None:
    _qapp()
    window = MainWindow()
    assert window._main_splitter.orientation() == Qt.Orientation.Horizontal
    assert window._main_splitter.count() == 3
    assert window._workspace_stack.indexOf(window._stack) == 0
    assert window._stack.count() == 7
    window.close()


def test_progress_bar_exists_and_accepts_worker_progress() -> None:
    _qapp()
    window = MainWindow()
    assert window._progress_bar.value() == 0
    window._on_progress(45)
    assert window._progress_bar.value() == 45
    assert window._progress_label.text() == "45%"
    window.close()
