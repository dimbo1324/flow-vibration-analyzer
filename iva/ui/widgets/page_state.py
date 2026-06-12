"""Consistent empty, running, error, and result states for analysis pages."""

from __future__ import annotations

from PySide6.QtCore import Qt  # type: ignore[import-untyped]
from PySide6.QtWidgets import QLabel, QWidget  # type: ignore[import-untyped]

from iva.ui.styles.theme import (
    COLOR_ACCENT,
    COLOR_BAD,
    COLOR_BORDER,
    COLOR_MUTED,
    COLOR_PANEL,
    RADIUS_MD,
    SPACING_SM,
)

__all__ = ["PageStateBanner"]


class PageStateBanner(QLabel):
    """Compact page-level status banner with a uniform visual language."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("pageStateBanner")
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.setWordWrap(True)
        self.setMinimumHeight(42)
        self.show_empty()

    def show_empty(self, message: str = "") -> None:
        """Show the initial state before an analysis result exists."""
        self._set_state(
            message
            or "Результатов анализа пока нет. Запустите анализ или используйте демо-сценарий.",
            COLOR_MUTED,
        )

    def show_running(self, message: str = "") -> None:
        """Show that an analysis is currently running."""
        self._set_state(message or "Выполняется анализ...", COLOR_ACCENT)

    def show_error(self, message: str) -> None:
        """Show a concise page-specific analysis error."""
        self._set_state(
            message or "Не удалось построить данные для страницы.",
            COLOR_BAD,
        )

    def show_result(self) -> None:
        """Hide the banner when real result content is available."""
        self.clear()
        self.setVisible(False)

    def _set_state(self, message: str, color: str) -> None:
        self.setText(message)
        # Coloured left bar + soft panel: state is readable at a glance
        # without shouting; the message stays short and Russian.
        self.setStyleSheet(
            f"background: {COLOR_PANEL}; color: {color}; border: 1px solid {COLOR_BORDER};"
            f" border-left: 3px solid {color};"
            f" border-radius: {RADIUS_MD}px; padding: {SPACING_SM + 4}px {SPACING_SM + 6}px;"
            f" font-weight: 600;"
        )
        self.setVisible(True)
