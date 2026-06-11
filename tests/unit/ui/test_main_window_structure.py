"""Unit tests for MainWindow structure and basic attributes."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _qapp():  # type: ignore[no-untyped-def]
    from PySide6.QtWidgets import QApplication  # type: ignore[import-untyped]

    return QApplication.instance() or QApplication([])


def test_toolbar_actions_exist() -> None:
    _qapp()
    from iva.ui.main_window import MainWindow

    w = MainWindow()
    assert w._action_open is not None
    assert w._action_run is not None
    assert w._action_save is not None
    w.close()


def test_main_window_has_session_and_thread_pool() -> None:
    _qapp()
    from iva.ui.main_window import MainWindow

    w = MainWindow()
    assert hasattr(w, "_session")
    assert hasattr(w, "_thread_pool")
    w.close()


def test_window_title_contains_iva() -> None:
    _qapp()
    from iva.ui.main_window import MainWindow

    w = MainWindow()
    assert "IVA" in w.windowTitle() or "Vibration" in w.windowTitle()
    w.close()


def test_error_banner_hidden_by_default() -> None:
    _qapp()
    from iva.ui.main_window import MainWindow

    w = MainWindow()
    assert not w._error_banner.isVisible()
    w.close()


def test_inspector_dock_hidden_by_default() -> None:
    _qapp()
    from iva.ui.main_window import MainWindow

    w = MainWindow()
    assert not w._inspector_dock.isVisible()
    w.close()


def test_page_names_count() -> None:
    from iva.ui.main_window import MainWindow

    assert len(MainWindow.PAGE_NAMES) == 7
