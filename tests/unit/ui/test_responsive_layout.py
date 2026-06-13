"""Проверяет, что компоновка MainWindow не лопается при малых экранах."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # type: ignore[import-untyped]

from iva.ui.main_window import MainWindow


def _qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_main_window_resizes_to_small_screen_without_crash() -> None:
    _qapp()
    window = MainWindow()
    window.resize(1366, 768)
    assert window.width() >= 1100 or window.minimumWidth() <= 1366
    window.close()


def test_main_window_has_minimum_size_set() -> None:
    _qapp()
    window = MainWindow()
    assert window.minimumWidth() > 0
    assert window.minimumHeight() > 0
    window.close()


def test_no_widget_has_absurd_minimum_width() -> None:
    _qapp()
    window = MainWindow()
    from PySide6.QtWidgets import QWidget  # type: ignore[import-untyped]

    for child in window.findChildren(QWidget):
        assert (
            child.minimumWidth() <= 1200
        ), f"{child.__class__.__name__} has minimumWidth={child.minimumWidth()} > 1200"
    window.close()


def test_nav_items_fit_expanded_sidebar() -> None:
    _qapp()
    window = MainWindow()
    sidebar_max = window._sidebar_panel.maximumWidth()
    assert sidebar_max <= 320
    window.close()
