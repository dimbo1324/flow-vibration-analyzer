"""Headless tests for expanded and compact navigation modes."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # type: ignore[import-untyped]

from iva.ui.main_window import MainWindow


def _qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_sidebar_toggles_between_expanded_and_compact_modes() -> None:
    _qapp()
    window = MainWindow()
    assert window._nav.count() == 7
    assert window._sidebar_compact is False

    window._toggle_sidebar()
    assert window._sidebar_compact is True
    assert window._sidebar_panel.maximumWidth() == 64
    assert all(window._nav.item(index).text() == "" for index in range(7))
    assert all(window._nav.item(index).toolTip() for index in range(7))

    window._toggle_sidebar()
    assert window._sidebar_compact is False
    assert window._nav.item(0).text() == window.PAGE_NAMES[0]
    assert window._nav.currentRow() == 0
    window.close()
