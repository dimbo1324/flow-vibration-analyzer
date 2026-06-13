"""Единый заголовок страницы для современной визуальной иерархии.

Каждая рабочая страница начинается с крупного заголовка, тонкой акцентной
черты и приглушённого подзаголовка. Вынесение этого в общий виджет убирает
дублирование и гарантирует одинаковый «воздух» и типографику на всех страницах.
"""

from __future__ import annotations

from PySide6.QtCore import Qt  # type: ignore[import-untyped]
from PySide6.QtWidgets import (  # type: ignore[import-untyped]
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from iva.ui.styles.theme import (
    COLOR_ACCENT,
    COLOR_BORDER,
    COLOR_MUTED,
    COLOR_TEXT,
    FONT_SIZE_DISPLAY,
    FONT_SIZE_SMALL,
    RADIUS_SM,
    SPACING_SM,
)

__all__ = ["PageHeader"]


class PageHeader(QWidget):
    """Заголовок страницы: акцентная черта, крупный титул, подзаголовок и чип.

    Чип статуса справа опционален и используется, например, для пометки
    демонстрационных данных или готовности результата — короткий визуальный
    маркер вместо длинного текста.
    """

    def __init__(
        self,
        title: str,
        subtitle: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._build(title, subtitle)

    def _build(self, title: str, subtitle: str) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(SPACING_SM + 4)

        # Вертикальная акцентная черта слева — недорогой, но узнаваемый приём,
        # который мгновенно задаёт начало смыслового блока.
        self._accent_bar = QFrame()
        self._accent_bar.setObjectName("pageHeaderAccent")
        self._accent_bar.setFixedWidth(4)
        self._accent_bar.setMinimumHeight(38)
        self._accent_bar.setStyleSheet(f"background: {COLOR_ACCENT}; border-radius: 2px;")
        root.addWidget(self._accent_bar)

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(2)

        self._title_label = QLabel(title)
        self._title_label.setObjectName("pageHeaderTitle")
        self._title_label.setStyleSheet(
            f"color: {COLOR_TEXT}; font-size: {FONT_SIZE_DISPLAY}pt; font-weight: 800;"
        )
        text_col.addWidget(self._title_label)

        self._subtitle_label = QLabel(subtitle)
        self._subtitle_label.setObjectName("pageHeaderSubtitle")
        self._subtitle_label.setWordWrap(True)
        self._subtitle_label.setStyleSheet(
            f"color: {COLOR_MUTED}; font-size: {FONT_SIZE_SMALL + 1}pt;"
        )
        self._subtitle_label.setVisible(bool(subtitle))
        text_col.addWidget(self._subtitle_label)

        root.addLayout(text_col, stretch=1)

        # Чип статуса скрыт до первого set_chip(): не занимать место зря.
        self._chip = QLabel("")
        self._chip.setObjectName("pageHeaderChip")
        self._chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._chip.setVisible(False)
        root.addWidget(self._chip, alignment=Qt.AlignmentFlag.AlignTop)

    def set_subtitle(self, subtitle: str) -> None:
        """Обновить подзаголовок (скрывается, если пустой)."""
        self._subtitle_label.setText(subtitle)
        self._subtitle_label.setVisible(bool(subtitle))

    def set_chip(self, text: str, color: str = COLOR_ACCENT) -> None:
        """Показать короткий цветной чип-маркер справа от заголовка."""
        if not text:
            self.clear_chip()
            return
        self._chip.setText(text)
        self._chip.setStyleSheet(
            f"color: {color}; border: 1px solid {color};"
            f" border-radius: {RADIUS_SM}px; padding: 3px 10px;"
            f" font-size: {FONT_SIZE_SMALL}pt; font-weight: 700;"
        )
        self._chip.setVisible(True)

    def clear_chip(self) -> None:
        """Скрыть чип статуса."""
        self._chip.setVisible(False)
        self._chip.setText("")


def make_divider() -> QFrame:
    """Вернуть тонкий горизонтальный разделитель в цвет границы темы."""
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFixedHeight(1)
    line.setStyleSheet(f"background: {COLOR_BORDER}; border: none;")
    return line
