"""IVA dark engineering theme tokens and stylesheet.

All color constants are taken from documentation/08_ui_ux_specification.md.
Components must reference color tokens, never hard-coded hex values.
"""

from __future__ import annotations

from PySide6.QtGui import QColor, QPalette  # type: ignore[import-untyped]
from PySide6.QtWidgets import QApplication  # type: ignore[import-untyped]

# ── Color tokens (dark engineering palette) ───────────────────────────────────
COLOR_BG = "#030405"  # window background
COLOR_SURFACE = "#070809"  # panel/card surfaces
COLOR_PANEL = "#0b0d10"  # elevated panels / cards
COLOR_BORDER = "#222832"  # borders/dividers
COLOR_TEXT = "#e7e9ee"  # primary text
COLOR_MUTED = "#8b94a3"  # secondary/muted text
COLOR_DIM = "#535d6b"  # dimmed / inactive elements
COLOR_ACCENT = "#9db7ff"  # accent blue (actions/links)
COLOR_GOOD = "#8fc9a4"  # safe/good status (green)
COLOR_WARN = "#d4b66e"  # warning status (amber)
COLOR_BAD = "#d27b7b"  # critical/error status (red)

# ── Typography tokens ─────────────────────────────────────────────────────────
FONT_FAMILY = "Inter, Segoe UI, SF Pro Display, Arial, sans-serif"
FONT_SIZE_SMALL = 11
FONT_SIZE_BASE = 13
FONT_SIZE_LARGE = 15
FONT_SIZE_TITLE = 18
FONT_WEIGHT_NORMAL = 400
FONT_WEIGHT_MEDIUM = 500
FONT_WEIGHT_BOLD = 700

# ── Layout/spacing tokens ─────────────────────────────────────────────────────
SPACING_XS = 4
SPACING_SM = 8
SPACING_MD = 16
SPACING_LG = 24
RADIUS_SM = 4
RADIUS_MD = 8
RADIUS_LG = 12

# ── Status color map (key used by MetricCard) ─────────────────────────────────
STATUS_COLOR_MAP: dict[str | None, str] = {
    "good": COLOR_GOOD,
    "warn": COLOR_WARN,
    "bad": COLOR_BAD,
    None: COLOR_TEXT,
}


def apply_dark_theme(app: QApplication) -> None:
    """Apply IVA dark engineering theme to a QApplication."""
    palette = QPalette()

    bg = QColor(COLOR_BG)
    surface = QColor(COLOR_SURFACE)
    panel = QColor(COLOR_PANEL)
    text = QColor(COLOR_TEXT)
    dim = QColor(COLOR_DIM)
    accent = QColor(COLOR_ACCENT)
    bad = QColor(COLOR_BAD)

    palette.setColor(QPalette.ColorRole.Window, bg)
    palette.setColor(QPalette.ColorRole.WindowText, text)
    palette.setColor(QPalette.ColorRole.Base, surface)
    palette.setColor(QPalette.ColorRole.AlternateBase, panel)
    palette.setColor(QPalette.ColorRole.ToolTipBase, panel)
    palette.setColor(QPalette.ColorRole.ToolTipText, text)
    palette.setColor(QPalette.ColorRole.Text, text)
    palette.setColor(QPalette.ColorRole.Button, surface)
    palette.setColor(QPalette.ColorRole.ButtonText, text)
    palette.setColor(QPalette.ColorRole.BrightText, bad)
    palette.setColor(QPalette.ColorRole.Link, accent)
    palette.setColor(QPalette.ColorRole.Highlight, accent)
    palette.setColor(QPalette.ColorRole.HighlightedText, bg)
    palette.setColor(QPalette.ColorRole.PlaceholderText, dim)

    # Disabled colours
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, dim)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, dim)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, dim)

    app.setPalette(palette)
    app.setStyleSheet(build_app_stylesheet())


def build_app_stylesheet() -> str:
    """Return global QSS stylesheet using theme tokens."""
    return f"""
    QMainWindow, QWidget {{
        background: {COLOR_BG};
        color: {COLOR_TEXT};
        font-size: {FONT_SIZE_BASE}pt;
    }}
    QListWidget {{
        background: {COLOR_SURFACE};
        border: 1px solid {COLOR_BORDER};
        color: {COLOR_TEXT};
        outline: none;
    }}
    QListWidget::item {{
        padding: 6px 12px;
        border-radius: {RADIUS_SM}px;
    }}
    QListWidget::item:selected {{
        background: {COLOR_ACCENT};
        color: {COLOR_BG};
    }}
    QListWidget::item:hover:!selected {{
        background: {COLOR_PANEL};
    }}
    QPushButton {{
        background: {COLOR_SURFACE};
        color: {COLOR_TEXT};
        border: 1px solid {COLOR_BORDER};
        border-radius: {RADIUS_SM}px;
        padding: 6px 14px;
        font-size: {FONT_SIZE_BASE}pt;
    }}
    QPushButton:hover {{
        background: {COLOR_PANEL};
        border-color: {COLOR_ACCENT};
    }}
    QPushButton:pressed {{
        background: {COLOR_ACCENT};
        color: {COLOR_BG};
    }}
    QPushButton:disabled {{
        color: {COLOR_DIM};
        border-color: {COLOR_BORDER};
        background: {COLOR_SURFACE};
    }}
    QLabel {{
        color: {COLOR_TEXT};
        background: transparent;
    }}
    QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox {{
        background: {COLOR_SURFACE};
        color: {COLOR_TEXT};
        border: 1px solid {COLOR_BORDER};
        border-radius: {RADIUS_SM}px;
        padding: 4px 8px;
        selection-background-color: {COLOR_ACCENT};
    }}
    QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus, QComboBox:focus {{
        border-color: {COLOR_ACCENT};
    }}
    QComboBox::drop-down {{
        border: none;
        padding-right: 8px;
    }}
    QComboBox QAbstractItemView {{
        background: {COLOR_SURFACE};
        color: {COLOR_TEXT};
        border: 1px solid {COLOR_BORDER};
        selection-background-color: {COLOR_ACCENT};
        selection-color: {COLOR_BG};
    }}
    QGroupBox {{
        color: {COLOR_MUTED};
        border: 1px solid {COLOR_BORDER};
        border-radius: {RADIUS_MD}px;
        margin-top: 8px;
        padding: 8px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        padding: 0 4px;
        color: {COLOR_MUTED};
    }}
    QScrollArea {{
        border: none;
    }}
    QScrollBar:vertical {{
        background: {COLOR_SURFACE};
        width: 8px;
    }}
    QScrollBar::handle:vertical {{
        background: {COLOR_DIM};
        border-radius: 4px;
        min-height: 20px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QDockWidget {{
        color: {COLOR_TEXT};
        titlebar-close-icon: none;
    }}
    QDockWidget::title {{
        background: {COLOR_PANEL};
        padding: 4px 8px;
        border-bottom: 1px solid {COLOR_BORDER};
    }}
    QTabWidget::pane {{
        border: 1px solid {COLOR_BORDER};
    }}
    QTabBar::tab {{
        background: {COLOR_SURFACE};
        color: {COLOR_MUTED};
        border: 1px solid {COLOR_BORDER};
        padding: 6px 12px;
    }}
    QTabBar::tab:selected {{
        background: {COLOR_PANEL};
        color: {COLOR_TEXT};
        border-bottom: 2px solid {COLOR_ACCENT};
    }}
    QStatusBar {{
        background: {COLOR_SURFACE};
        color: {COLOR_MUTED};
        border-top: 1px solid {COLOR_BORDER};
    }}
    QToolBar {{
        background: {COLOR_SURFACE};
        border-bottom: 1px solid {COLOR_BORDER};
        spacing: 4px;
        padding: 2px 4px;
    }}
    QToolBar QToolButton {{
        background: transparent;
        color: {COLOR_TEXT};
        border: 1px solid transparent;
        border-radius: {RADIUS_SM}px;
        padding: 4px 10px;
    }}
    QToolBar QToolButton:hover {{
        background: {COLOR_PANEL};
        border-color: {COLOR_BORDER};
    }}
    QToolBar QToolButton:pressed {{
        background: {COLOR_ACCENT};
        color: {COLOR_BG};
    }}
    QTextEdit {{
        background: {COLOR_SURFACE};
        color: {COLOR_TEXT};
        border: 1px solid {COLOR_BORDER};
        border-radius: {RADIUS_SM}px;
        font-size: {FONT_SIZE_SMALL}pt;
    }}
    QTableWidget {{
        background: {COLOR_SURFACE};
        color: {COLOR_TEXT};
        border: 1px solid {COLOR_BORDER};
        gridline-color: {COLOR_BORDER};
    }}
    QTableWidget::item:selected {{
        background: {COLOR_ACCENT};
        color: {COLOR_BG};
    }}
    QHeaderView::section {{
        background: {COLOR_PANEL};
        color: {COLOR_MUTED};
        border: 1px solid {COLOR_BORDER};
        padding: 4px 6px;
        font-size: {FONT_SIZE_SMALL}pt;
    }}
    QSplitter::handle {{
        background: {COLOR_BORDER};
    }}
    QCheckBox {{
        color: {COLOR_TEXT};
        spacing: 6px;
    }}
    QCheckBox::indicator {{
        width: 14px;
        height: 14px;
        border: 1px solid {COLOR_BORDER};
        border-radius: 3px;
        background: {COLOR_SURFACE};
    }}
    QCheckBox::indicator:checked {{
        background: {COLOR_ACCENT};
        border-color: {COLOR_ACCENT};
    }}
    QDialog {{
        background: {COLOR_BG};
        color: {COLOR_TEXT};
    }}
    QDialogButtonBox QPushButton {{
        min-width: 80px;
    }}
    """
