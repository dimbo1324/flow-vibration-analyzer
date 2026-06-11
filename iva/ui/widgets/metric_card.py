"""MetricCard — a small widget that displays a labelled numeric metric."""

from __future__ import annotations

from PySide6.QtCore import Qt  # type: ignore[import-untyped]
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget  # type: ignore[import-untyped]

from iva.ui.styles.theme import (
    COLOR_BORDER,
    COLOR_DIM,
    COLOR_MUTED,
    COLOR_SURFACE,
    COLOR_TEXT,
    FONT_SIZE_LARGE,
    FONT_SIZE_SMALL,
    RADIUS_MD,
    SPACING_SM,
    STATUS_COLOR_MAP,
)

__all__ = ["MetricCard"]


class MetricCard(QWidget):
    """Compact card showing a named metric value with optional unit and status.

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
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_SM, SPACING_SM, SPACING_SM, SPACING_SM)
        layout.setSpacing(2)

        self._label = QLabel(label.upper())
        self._label.setStyleSheet(
            f"color: {COLOR_DIM}; font-size: {FONT_SIZE_SMALL}pt; letter-spacing: 1px;"
        )

        self._value_label = QLabel("—")
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._value_label.setStyleSheet(
            f"color: {COLOR_TEXT}; font-size: {FONT_SIZE_LARGE}pt; font-weight: bold;"
        )

        self._unit_label = QLabel("")
        self._unit_label.setStyleSheet(f"color: {COLOR_MUTED}; font-size: {FONT_SIZE_SMALL}pt;")

        layout.addWidget(self._label)
        layout.addWidget(self._value_label)
        layout.addWidget(self._unit_label)

        self.setStyleSheet(
            f"MetricCard {{ background: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER};"
            f" border-radius: {RADIUS_MD}px; }}"
        )
        self.setMinimumSize(120, 80)

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
        self._value_label.setStyleSheet(
            f"color: {color}; font-size: {FONT_SIZE_LARGE}pt; font-weight: bold;"
        )

    def clear(self) -> None:
        """Reset the card to placeholder state."""
        self.set_value("—", "", None)
