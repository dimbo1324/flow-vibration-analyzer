"""System smoke tests: verify IVA main window launches without errors."""

from __future__ import annotations

import os

# Must be set BEFORE any PySide6 import to enable headless rendering.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest


@pytest.fixture(scope="module")
def qapp():  # type: ignore[no-untyped-def]
    """Provide a QApplication instance for the test session."""
    from PySide6.QtWidgets import QApplication  # type: ignore[import-untyped]

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_main_window_instantiates(qapp: object) -> None:
    from iva.ui.main_window import MainWindow

    window = MainWindow()
    assert window.windowTitle() != ""
    assert window.centralWidget() is not None
    window.close()


def test_navigation_has_seven_pages(qapp: object) -> None:
    from iva.ui.main_window import MainWindow

    window = MainWindow()
    assert window._nav.count() == 7
    window.close()


def test_stack_has_seven_pages(qapp: object) -> None:
    from iva.ui.main_window import MainWindow

    window = MainWindow()
    assert window._stack.count() == 7
    window.close()


def test_inspector_dock_exists(qapp: object) -> None:
    from iva.ui.main_window import MainWindow

    window = MainWindow()
    assert window._inspector_dock is not None
    window.close()


def test_toolbar_actions_exist(qapp: object) -> None:
    from iva.ui.main_window import MainWindow

    window = MainWindow()
    assert window._action_open is not None
    assert window._action_run is not None
    assert window._action_save is not None
    window.close()


def test_session_initialized(qapp: object) -> None:
    from iva.ui.main_window import MainWindow

    window = MainWindow()
    assert window._session is not None
    assert window._thread_pool is not None
    window.close()
