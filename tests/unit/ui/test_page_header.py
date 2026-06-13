"""Headless tests for the reusable PageHeader widget and its adoption."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # type: ignore[import-untyped]

from iva.ui.pages.overview_page import OverviewPage
from iva.ui.pages.physics_page import PhysicsPage
from iva.ui.pages.report_page import ReportPage
from iva.ui.pages.signal_page import SignalPage
from iva.ui.pages.spectrum_page import SpectrumPage
from iva.ui.styles.theme import COLOR_BAD
from iva.ui.widgets.page_header import PageHeader, make_divider


def _qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_page_header_title_and_subtitle() -> None:
    _qapp()
    header = PageHeader("Обзор", "Краткое описание")
    assert header._title_label.text() == "Обзор"
    assert header._subtitle_label.text() == "Краткое описание"
    # isHidden() reflects the explicit hide state regardless of show().
    assert header._subtitle_label.isHidden() is False
    header.close()


def test_page_header_empty_subtitle_hidden() -> None:
    _qapp()
    header = PageHeader("Заголовок")
    # An empty subtitle must not occupy space.
    assert header._subtitle_label.text() == ""
    assert header._subtitle_label.isHidden() is True
    header.close()


def test_page_header_chip_toggle() -> None:
    _qapp()
    header = PageHeader("T", "S")
    assert header._chip.isHidden() is True
    header.set_chip("ДЕМО", COLOR_BAD)
    assert header._chip.text() == "ДЕМО"
    assert header._chip.isHidden() is False
    assert COLOR_BAD in header._chip.styleSheet()
    header.clear_chip()
    assert header._chip.isHidden() is True
    header.close()


def test_make_divider_is_thin_line() -> None:
    _qapp()
    line = make_divider()
    assert line.height() <= 1 or line.maximumHeight() <= 1 or line.minimumHeight() <= 1
    line.close()


def test_pages_use_page_header() -> None:
    """Every redesigned page exposes a PageHeader instance at the top."""
    _qapp()
    for page_cls in (OverviewPage, SignalPage, SpectrumPage, PhysicsPage, ReportPage):
        page = page_cls()
        assert hasattr(page, "_header"), f"{page_cls.__name__} must have a PageHeader"
        assert isinstance(page._header, PageHeader)
        assert page._header._title_label.text() != ""
        page.close()
