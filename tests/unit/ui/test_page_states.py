"""Headless tests for consistent analysis page states."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QWidget  # type: ignore[import-untyped]

from iva.ui.pages.overview_page import OverviewPage
from iva.ui.pages.physics_page import PhysicsPage
from iva.ui.pages.profiles_page import ProfilesPage
from iva.ui.pages.report_page import ReportPage
from iva.ui.pages.signal_page import SignalPage
from iva.ui.pages.spectrum_page import SpectrumPage


def _qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


@pytest.mark.parametrize(
    "page_type",
    [OverviewPage, SignalPage, SpectrumPage, PhysicsPage, ProfilesPage, ReportPage],
)
def test_page_states_are_switchable(page_type: type[QWidget]) -> None:
    _qapp()
    page = page_type()
    banner = page._state_banner  # type: ignore[attr-defined]
    assert not banner.isHidden()
    assert "Результ" in banner.text() or "Отчёт" in banner.text()

    page.set_running_state("Выполняется анализ...")  # type: ignore[attr-defined]
    assert banner.text() == "Выполняется анализ..."

    page.set_error_state("Ошибка страницы")  # type: ignore[attr-defined]
    assert banner.text() == "Ошибка страницы"
    page.close()


@pytest.mark.parametrize(
    "page_type",
    [OverviewPage, SignalPage, SpectrumPage, PhysicsPage, ProfilesPage, ReportPage],
)
def test_completed_result_still_updates_pages(page_type: type[QWidget], stage9_result) -> None:  # type: ignore[no-untyped-def]
    _qapp()
    page = page_type()
    page.on_analysis_completed(stage9_result)  # type: ignore[attr-defined]
    assert page._state_banner.isHidden()  # type: ignore[attr-defined]
    page.close()
