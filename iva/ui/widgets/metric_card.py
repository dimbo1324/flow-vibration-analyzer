"""MetricCard — a card widget that displays a labelled hero-size metric."""

from __future__ import annotations

from PySide6.QtCore import Qt  # type: ignore[import-untyped]
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget  # type: ignore[import-untyped]

from iva.ui.styles.theme import (
    COLOR_ACCENT,
    COLOR_BORDER,
    COLOR_DIM,
    COLOR_MUTED,
    COLOR_SURFACE,
    COLOR_SURFACE_HOVER,
    COLOR_TEXT,
    FONT_SIZE_HERO,
    FONT_SIZE_SMALL,
    RADIUS_LG,
    SPACING_MD,
    STATUS_COLOR_MAP,
)

__all__ = ["MetricCard"]


class MetricCard(QWidget):
    """Card showing a named metric as a large hero number with optional unit.

    The value dominates visually (numbers over words); the label and unit are
    small and muted.  Hovering highlights the card border with the accent.

    Status colors:
        ``"good"``  → COLOR_GOOD (green)
        ``"warn"``  → COLOR_WARN (amber)
        ``"bad"``   → COLOR_BAD  (red)
        ``None``    → COLOR_TEXT (neutral)
    """

    def __init__(self, label: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui(label)

    def _setup_ui(self, label: str) -> None:
        # Without WA_StyledBackground a plain QWidget subclass silently skips
        # painting its stylesheet background/border, so the card style and the
        # :hover state would never be visible.
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)
        layout.setSpacing(4)

        self._label = QLabel(label.upper())
        self._label.setStyleSheet(
            f"color: {COLOR_DIM}; font-size: {FONT_SIZE_SMALL}pt; letter-spacing: 1.5px;"
        )

        self._value_label = QLabel("—")
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._value_label.setStyleSheet(self._value_style(COLOR_TEXT))

        self._unit_label = QLabel("")
        self._unit_label.setStyleSheet(f"color: {COLOR_MUTED}; font-size: {FONT_SIZE_SMALL}pt;")

        layout.addWidget(self._label)
        layout.addWidget(self._value_label)
        layout.addWidget(self._unit_label)
        layout.addStretch()

        self.setStyleSheet(
            f"MetricCard {{ background: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER};"
            f" border-radius: {RADIUS_LG}px; }}"
            f" MetricCard:hover {{ background: {COLOR_SURFACE_HOVER};"
            f" border-color: {COLOR_ACCENT}; }}"
        )
        self.setMinimumSize(150, 104)

    @staticmethod
    def _value_style(color: str) -> str:
        return f"color: {color}; font-size: {FONT_SIZE_HERO}pt; font-weight: 800;"

    def set_value(self, value: str, unit: str = "", status: str | None = None) -> None:
        """Update displayed value, unit, and status colour.

        Args:
            value: String representation of the metric (e.g. ``"40.04"``).
            unit:  Unit label displayed below the value (e.g. ``"Hz"``).
            status: One of ``"good"``, ``"warn"``, ``"bad"``, or ``None``.
        """
        self._value_label.setText(value)
        self._unit_label.setText(unit)
        color = STATUS_COLOR_MAP.get(status, COLOR_TEXT)
        self._value_label.setStyleSheet(self._value_style(color))

    def clear(self) -> None:
        """Reset the card to placeholder state."""
        self.set_value("—", "", None)
