"""Проверка наличия и разумных значений компактных токенов темы."""

from __future__ import annotations

from iva.ui.styles.theme import (
    BUTTON_HEIGHT_COMPACT,
    CHART_TOOLBAR_ICON_SIZE,
    INPUT_HEIGHT_COMPACT,
    PANEL_PADDING_COMPACT,
    SIDEBAR_WIDTH_COMPACT,
    SIDEBAR_WIDTH_EXPANDED,
    TOOLBAR_HEIGHT_COMPACT,
)


def test_panel_padding_compact_is_small() -> None:
    assert 4 <= PANEL_PADDING_COMPACT <= 12


def test_button_height_compact_is_reasonable() -> None:
    assert 24 <= BUTTON_HEIGHT_COMPACT <= 36


def test_toolbar_height_compact_is_reasonable() -> None:
    assert 24 <= TOOLBAR_HEIGHT_COMPACT <= 40


def test_sidebar_widths_ordered() -> None:
    assert SIDEBAR_WIDTH_COMPACT < SIDEBAR_WIDTH_EXPANDED


def test_sidebar_compact_matches_existing_behavior() -> None:
    assert SIDEBAR_WIDTH_COMPACT == 64


def test_sidebar_expanded_is_compact_enough() -> None:
    assert SIDEBAR_WIDTH_EXPANDED <= 220


def test_input_height_compact_is_reasonable() -> None:
    assert 22 <= INPUT_HEIGHT_COMPACT <= 36


def test_chart_toolbar_icon_size_is_small() -> None:
    assert 12 <= CHART_TOOLBAR_ICON_SIZE <= 20
