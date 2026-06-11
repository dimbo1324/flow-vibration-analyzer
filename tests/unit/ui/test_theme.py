"""Unit tests for IVA dark theme tokens and stylesheet."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_theme_tokens_exist() -> None:
    from iva.ui.styles.theme import (
        COLOR_ACCENT,
        COLOR_BAD,
        COLOR_BG,
        COLOR_GOOD,
        COLOR_TEXT,
        COLOR_WARN,
        FONT_FAMILY,
        FONT_SIZE_BASE,
    )

    assert COLOR_BG.startswith("#")
    assert COLOR_ACCENT.startswith("#")
    assert COLOR_GOOD.startswith("#")
    assert COLOR_WARN.startswith("#")
    assert COLOR_BAD.startswith("#")
    assert COLOR_TEXT.startswith("#")
    assert isinstance(FONT_SIZE_BASE, int)
    assert FONT_SIZE_BASE > 0
    assert isinstance(FONT_FAMILY, str)


def test_build_app_stylesheet_returns_string() -> None:
    from iva.ui.styles.theme import build_app_stylesheet

    result = build_app_stylesheet()
    assert isinstance(result, str)
    assert len(result) > 100  # non-trivial content
    assert "QMainWindow" in result
    assert "QPushButton" in result


def test_apply_dark_theme_runs_without_error() -> None:
    from PySide6.QtWidgets import QApplication  # type: ignore[import-untyped]

    from iva.ui.styles.theme import apply_dark_theme

    app = QApplication.instance() or QApplication([])
    apply_dark_theme(app)  # should not raise


def test_status_color_map_has_all_keys() -> None:
    from iva.ui.styles.theme import STATUS_COLOR_MAP

    for key in ("good", "warn", "bad", None):
        assert key in STATUS_COLOR_MAP
        assert STATUS_COLOR_MAP[key].startswith("#")
