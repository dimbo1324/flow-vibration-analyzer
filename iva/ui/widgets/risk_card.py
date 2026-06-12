"""Prominent, reusable presentation of an engineering risk assessment."""

from __future__ import annotations

from PySide6.QtCore import Qt  # type: ignore[import-untyped]
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget  # type: ignore[import-untyped]

from iva.core.models.enums import RiskLevel
from iva.ui.styles.theme import (
    COLOR_BAD,
    COLOR_GOOD,
    COLOR_MUTED,
    COLOR_PANEL,
    COLOR_WARN,
    FONT_SIZE_LARGE,
    RADIUS_MD,
    SPACING_MD,
    SPACING_SM,
)

__all__ = ["RiskCard"]

_RISK_PRESENTATION: dict[str, tuple[str, str]] = {
    RiskLevel.SAFE: ("Безопасно", COLOR_GOOD),
    RiskLevel.WATCH: ("Требует внимания", COLOR_WARN),
    RiskLevel.CRITICAL: ("Критично", COLOR_BAD),
}


class RiskCard(QWidget):
    """Display risk level and recommendation using the project theme tokens."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("riskCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_MD, SPACING_SM, SPACING_MD, SPACING_SM)
        layout.setSpacing(4)

        self._title_label = QLabel("ОЦЕНКА РИСКА")
        self._title_label.setStyleSheet(f"color: {COLOR_MUTED}; font-weight: 600;")

        self._level_label = QLabel("Результат отсутствует")
        self._level_label.setObjectName("riskLevelLabel")
        self._level_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self._recommendation_label = QLabel(
            "Запустите анализ, чтобы получить инженерную оценку режима."
        )
        self._recommendation_label.setObjectName("riskRecommendationLabel")
        self._recommendation_label.setWordWrap(True)
        self._recommendation_label.setStyleSheet(f"color: {COLOR_MUTED};")

        layout.addWidget(self._title_label)
        layout.addWidget(self._level_label)
        layout.addWidget(self._recommendation_label)
        self.clear()

    def set_risk(self, level: RiskLevel | str, recommendation: str = "") -> None:
        """Show one of the supported SAFE, WATCH, or CRITICAL states."""
        key = str(level).lower()
        label, color = _RISK_PRESENTATION.get(key, ("Не определено", COLOR_MUTED))
        self._level_label.setText(label)
        self._level_label.setStyleSheet(
            f"color: {color}; font-size: {FONT_SIZE_LARGE + 3}pt; font-weight: 750;"
        )
        self._recommendation_label.setText(
            recommendation or "Рекомендация для текущего режима отсутствует."
        )
        self._recommendation_label.setStyleSheet(f"color: {color};")
        self.setStyleSheet(
            f"RiskCard {{ background: {COLOR_PANEL}; border: 2px solid {color};"
            f" border-radius: {RADIUS_MD}px; }}"
        )

    def clear(self) -> None:
        """Reset the card to its neutral empty state."""
        self._level_label.setText("Результат отсутствует")
        self._level_label.setStyleSheet(
            f"color: {COLOR_MUTED}; font-size: {FONT_SIZE_LARGE + 1}pt; font-weight: 700;"
        )
        self._recommendation_label.setText(
            "Запустите анализ, чтобы получить инженерную оценку режима."
        )
        self._recommendation_label.setStyleSheet(f"color: {COLOR_MUTED};")
        self.setStyleSheet(
            f"RiskCard {{ background: {COLOR_PANEL}; border: 1px solid {COLOR_MUTED};"
            f" border-radius: {RADIUS_MD}px; }}"
        )
