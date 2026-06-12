"""Headless tests for the modern UI refresh: tokens, QSS, hero cards, motion."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt  # type: ignore[import-untyped]
from PySide6.QtWidgets import QApplication  # type: ignore[import-untyped]

from iva.ui.styles.theme import (
    ANIM_FAST_MS,
    ANIM_NORMAL_MS,
    COLOR_ACCENT_HOVER,
    COLOR_ACCENT_SOFT,
    COLOR_SURFACE_HOVER,
    FONT_SIZE_HERO,
    RADIUS_XL,
    SPACING_XL,
    build_app_stylesheet,
)
from iva.ui.widgets.metric_card import MetricCard
from iva.ui.widgets.risk_card import RiskCard


def _qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_modern_tokens_exist() -> None:
    assert COLOR_SURFACE_HOVER.startswith("#")
    assert COLOR_ACCENT_HOVER.startswith("#")
    assert COLOR_ACCENT_SOFT.startswith("rgba(")
    assert FONT_SIZE_HERO > 20
    assert SPACING_XL > 24
    assert RADIUS_XL > 14
    assert 0 < ANIM_FAST_MS < ANIM_NORMAL_MS < 1000


def test_stylesheet_has_accent_button_and_chrome() -> None:
    qss = build_app_stylesheet()
    assert 'QPushButton[accent="true"]' in qss
    assert "QToolTip" in qss
    assert "QMenu" in qss
    assert "QScrollBar:horizontal" in qss


def test_metric_card_uses_hero_typography() -> None:
    _qapp()
    card = MetricCard("Тест")
    assert card.testAttribute(Qt.WidgetAttribute.WA_StyledBackground)
    assert f"{FONT_SIZE_HERO}pt" in card._value_label.styleSheet()
    card.set_value("40.0", "Hz", "good")
    assert f"{FONT_SIZE_HERO}pt" in card._value_label.styleSheet()
    card.close()


def test_risk_card_paints_styled_background() -> None:
    _qapp()
    card = RiskCard()
    assert card.testAttribute(Qt.WidgetAttribute.WA_StyledBackground)
    card.close()


def test_overview_demo_button_is_accent() -> None:
    _qapp()
    from iva.ui.pages.overview_page import OverviewPage

    page = OverviewPage()
    assert page._quick_demo_button.property("accent") is True
    page.close()


def test_main_window_page_transition_safe_offscreen(stage9_result) -> None:  # type: ignore[no-untyped-def]
    """Nav change must not leave a lingering opacity effect in offscreen mode."""
    _qapp()
    from iva.ui.main_window import MainWindow

    window = MainWindow()
    assert hasattr(window, "_animate_page_transition")
    window._nav.setCurrentRow(2)
    page = window._stack.currentWidget()
    assert page is not None
    assert page.graphicsEffect() is None  # animation skipped offscreen
    window.close()
