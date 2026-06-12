"""Headless tests for inspector visibility and result content."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # type: ignore[import-untyped]

from iva.ui.main_window import MainWindow


def _qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_inspector_toggle_and_result_summary(stage9_result) -> None:  # type: ignore[no-untyped-def]
    _qapp()
    window = MainWindow()
    assert window._inspector_dock.isHidden()

    window._toggle_inspector()
    assert not window._inspector_dock.isHidden()

    window._session.result = stage9_result
    window._update_inspector(stage9_result)
    text = window._inspector_text.text()
    assert stage9_result.source_file_path.name in text
    assert "RMS:" in text
    assert "Re:" in text
    assert "Предупреждения: 1" in text

    window._toggle_inspector()
    assert window._inspector_dock.isHidden()
    window.close()
