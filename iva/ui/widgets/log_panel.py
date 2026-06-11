"""LogPanel — a read-only log/message panel with auto-scroll."""

from __future__ import annotations

from PySide6.QtWidgets import QTextEdit, QVBoxLayout, QWidget  # type: ignore[import-untyped]

from iva.ui.styles.theme import COLOR_BAD, COLOR_TEXT, COLOR_WARN

__all__ = ["LogPanel"]


class LogPanel(QWidget):
    """Read-only text area that displays coloured log messages."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._text = QTextEdit()
        self._text.setReadOnly(True)
        layout.addWidget(self._text)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def append_info(self, message: str) -> None:
        """Append an INFO-level message."""
        self._text.append(f'<span style="color:{COLOR_TEXT}">[INFO] {message}</span>')
        self._scroll_to_bottom()

    def append_warning(self, message: str) -> None:
        """Append a WARNING-level message."""
        self._text.append(f'<span style="color:{COLOR_WARN}">[WARN] {message}</span>')
        self._scroll_to_bottom()

    def append_error(self, message: str) -> None:
        """Append an ERROR-level message."""
        self._text.append(f'<span style="color:{COLOR_BAD}">[ERROR] {message}</span>')
        self._scroll_to_bottom()

    def clear(self) -> None:
        """Clear all messages."""
        self._text.clear()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _scroll_to_bottom(self) -> None:
        scrollbar = self._text.verticalScrollBar()
        if scrollbar is not None:
            scrollbar.setValue(scrollbar.maximum())
