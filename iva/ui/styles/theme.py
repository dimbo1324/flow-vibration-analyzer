"""IVA dark engineering theme tokens and stylesheet.

All color constants are taken from docs/08_ui_ux_specification.md.
Components must reference color tokens, never hard-coded hex values.
"""

from __future__ import annotations

from PySide6.QtGui import QColor, QPalette  # type: ignore[import-untyped]
from PySide6.QtWidgets import QApplication  # type: ignore[import-untyped]

# ── Color tokens (modern dark engineering palette) ───────────────────────────
# Blue-tinted dark surfaces with clear elevation steps and a vivid accent.
COLOR_BG = "#0b0e14"  # window background
COLOR_SURFACE = "#11151d"  # panel/card surfaces
COLOR_PANEL = "#171c26"  # elevated panels / cards
COLOR_SURFACE_HOVER = "#1c2230"  # hover state for surfaces/cards
COLOR_BORDER = "#262e3d"  # borders/dividers
COLOR_TEXT = "#e8ecf4"  # primary text
COLOR_MUTED = "#94a0b4"  # secondary/muted text
COLOR_DIM = "#5b6678"  # dimmed / inactive elements
COLOR_ACCENT = "#7aa2f7"  # accent blue (actions/links)
COLOR_ACCENT_HOVER = "#92b4ff"  # accent hover state
COLOR_ACCENT_SOFT = "rgba(122, 162, 247, 0.16)"  # translucent accent fill
COLOR_GOOD = "#7fd1a0"  # safe/good status (green)
COLOR_WARN = "#e0b15e"  # warning status (amber)
COLOR_BAD = "#ef7d8e"  # critical/error status (red)

# ── Typography tokens ─────────────────────────────────────────────────────────
FONT_FAMILY = "Inter, Segoe UI, SF Pro Display, Arial, sans-serif"
FONT_SIZE_SMALL = 11
FONT_SIZE_BASE = 13
FONT_SIZE_LARGE = 15
FONT_SIZE_TITLE = 18
FONT_SIZE_HERO = 26  # hero metric values (big numbers over words)
FONT_WEIGHT_NORMAL = 400
FONT_WEIGHT_MEDIUM = 500
FONT_WEIGHT_BOLD = 700

# ── Layout/spacing tokens ─────────────────────────────────────────────────────
SPACING_XS = 4
SPACING_SM = 8
SPACING_MD = 16
SPACING_LG = 24
SPACING_XL = 32
RADIUS_SM = 6
RADIUS_MD = 10
RADIUS_LG = 14
RADIUS_XL = 18

# ── Motion tokens (milliseconds) ──────────────────────────────────────────────
ANIM_FAST_MS = 140
ANIM_NORMAL_MS = 220

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
    QToolTip {{
        background: {COLOR_PANEL};
        color: {COLOR_TEXT};
        border: 1px solid {COLOR_BORDER};
        border-radius: {RADIUS_SM}px;
        padding: 6px 10px;
        font-size: {FONT_SIZE_SMALL}pt;
    }}
    QListWidget {{
        background: {COLOR_SURFACE};
        border: 1px solid {COLOR_BORDER};
        border-radius: {RADIUS_MD}px;
        color: {COLOR_TEXT};
        outline: none;
        padding: 4px;
    }}
    QListWidget::item {{
        padding: 10px 14px;
        border-radius: {RADIUS_SM}px;
        margin: 1px 2px;
    }}
    QListWidget::item:selected {{
        background: {COLOR_ACCENT_SOFT};
        color: {COLOR_ACCENT};
        font-weight: 600;
    }}
    QListWidget::item:hover:!selected {{
        background: {COLOR_SURFACE_HOVER};
    }}
    QPushButton {{
        background: {COLOR_PANEL};
        color: {COLOR_TEXT};
        border: 1px solid {COLOR_BORDER};
        border-radius: {RADIUS_MD}px;
        padding: 8px 18px;
        font-size: {FONT_SIZE_BASE}pt;
        font-weight: 500;
    }}
    QPushButton:hover {{
        background: {COLOR_SURFACE_HOVER};
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
    QPushButton[accent="true"] {{
        background: {COLOR_ACCENT};
        color: {COLOR_BG};
        border: 1px solid {COLOR_ACCENT};
        font-weight: 700;
    }}
    QPushButton[accent="true"]:hover {{
        background: {COLOR_ACCENT_HOVER};
        border-color: {COLOR_ACCENT_HOVER};
    }}
    QPushButton[accent="true"]:disabled {{
        background: {COLOR_PANEL};
        color: {COLOR_DIM};
        border-color: {COLOR_BORDER};
    }}
    QLabel {{
        color: {COLOR_TEXT};
        background: transparent;
    }}
    QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox {{
        background: {COLOR_SURFACE};
        color: {COLOR_TEXT};
        border: 1px solid {COLOR_BORDER};
        border-radius: {RADIUS_MD}px;
        padding: 7px 10px;
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
        background: transparent;
        width: 10px;
        margin: 2px;
    }}
    QScrollBar::handle:vertical {{
        background: {COLOR_BORDER};
        border-radius: 4px;
        min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {COLOR_DIM};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 10px;
        margin: 2px;
    }}
    QScrollBar::handle:horizontal {{
        background: {COLOR_BORDER};
        border-radius: 4px;
        min-width: 24px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {COLOR_DIM};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
    }}
    QMenu {{
        background: {COLOR_PANEL};
        color: {COLOR_TEXT};
        border: 1px solid {COLOR_BORDER};
        border-radius: {RADIUS_MD}px;
        padding: 6px;
    }}
    QMenu::item {{
        padding: 7px 24px 7px 14px;
        border-radius: {RADIUS_SM}px;
    }}
    QMenu::item:selected {{
        background: {COLOR_ACCENT_SOFT};
        color: {COLOR_ACCENT};
    }}
    QMenu::separator {{
        height: 1px;
        background: {COLOR_BORDER};
        margin: 6px 10px;
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
        background: transparent;
    }}
    QSplitter::handle:hover {{
        background: {COLOR_ACCENT_SOFT};
    }}
    QSplitter::handle:horizontal {{
        width: 5px;
    }}
    QSplitter::handle:vertical {{
        height: 5px;
    }}
    QProgressBar {{
        background: {COLOR_PANEL};
        color: transparent;
        border: none;
        border-radius: 5px;
        max-height: 10px;
        min-height: 10px;
    }}
    QProgressBar::chunk {{
        background: {COLOR_ACCENT};
        border-radius: 5px;
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
