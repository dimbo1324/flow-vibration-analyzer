"""Headless tests for professional SAFE, WATCH, and CRITICAL risk display."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # type: ignore[import-untyped]

from iva.core.models.enums import RiskLevel
from iva.ui.styles.theme import COLOR_BAD, COLOR_GOOD, COLOR_WARN
from iva.ui.widgets.risk_card import RiskCard


def _qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


@pytest.mark.parametrize(
    ("level", "label", "color"),
    [
        (RiskLevel.SAFE, "Безопасно", COLOR_GOOD),
        (RiskLevel.WATCH, "Требует внимания", COLOR_WARN),
        (RiskLevel.CRITICAL, "Критично", COLOR_BAD),
    ],
)
def test_risk_card_displays_supported_levels(
    level: RiskLevel,
    label: str,
    color: str,
) -> None:
    _qapp()
    card = RiskCard()
    card.set_risk(level, "Проверить текущий режим.")
    assert card._level_label.text() == label
    assert color in card._level_label.styleSheet()
    assert "Проверить" in card._recommendation_label.text()
    card.close()
