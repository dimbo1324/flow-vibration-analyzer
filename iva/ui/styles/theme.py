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
COLOR_ACCENT_2 = "#5ad1c8"  # secondary accent (teal) for visual variety
COLOR_ACCENT_2_SOFT = "rgba(90, 209, 200, 0.14)"  # translucent secondary fill
COLOR_GOOD = "#7fd1a0"  # safe/good status (green)
COLOR_WARN = "#e0b15e"  # warning status (amber)
COLOR_BAD = "#ef7d8e"  # critical/error status (red)

# ── Typography tokens ─────────────────────────────────────────────────────────
FONT_FAMILY = "Inter, Segoe UI, SF Pro Display, Arial, sans-serif"
FONT_SIZE_SMALL = 11
FONT_SIZE_BASE = 13
FONT_SIZE_LARGE = 15
FONT_SIZE_TITLE = 18
FONT_SIZE_DISPLAY = 22  # page headers (large, calm hierarchy)
FONT_SIZE_HERO = 22  # hero metric values (big numbers over words)
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

# ── Compact density tokens (engineering workstation mode) ─────────────────────
PANEL_PADDING_COMPACT = 8
BUTTON_HEIGHT_COMPACT = 28
TOOLBAR_HEIGHT_COMPACT = 32
SIDEBAR_WIDTH_EXPANDED = 200
SIDEBAR_WIDTH_COMPACT = 64
INPUT_HEIGHT_COMPACT = 28
CHART_TOOLBAR_ICON_SIZE = 16

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

    /* ── Sidebar shell ─────────────────────────────────────────────── */
    QWidget#SidebarPanel {{
        background: {COLOR_SURFACE};
        border-right: 1px solid {COLOR_BORDER};
    }}

    /* ── Navigation list ──────────────────────────────────────────── */
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
    /* The workflow navigation gets a modern "active rail" indicator. */
    QListWidget#SidebarNav {{
        background: transparent;
        border: none;
        padding: 2px;
    }}
    QListWidget#SidebarNav::item {{
        padding: 7px 10px;
        border-radius: {RADIUS_MD}px;
        margin: 1px 2px;
        border-left: 3px solid transparent;
        color: {COLOR_MUTED};
    }}
    QListWidget#SidebarNav::item:hover:!selected {{
        background: {COLOR_SURFACE_HOVER};
        color: {COLOR_TEXT};
    }}
    QListWidget#SidebarNav::item:selected {{
        background: {COLOR_ACCENT_SOFT};
        border-left: 3px solid {COLOR_ACCENT};
        color: {COLOR_ACCENT};
        font-weight: 700;
    }}

    /* ── Buttons ──────────────────────────────────────────────────── */
    QPushButton {{
        background: {COLOR_PANEL};
        color: {COLOR_TEXT};
        border: 1px solid {COLOR_BORDER};
        border-radius: {RADIUS_MD}px;
        padding: 5px 14px;
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
    /* Quiet "ghost" button for secondary actions. */
    QPushButton[subtle="true"] {{
        background: transparent;
        border-color: transparent;
        color: {COLOR_MUTED};
    }}
    QPushButton[subtle="true"]:hover {{
        background: {COLOR_SURFACE_HOVER};
        color: {COLOR_TEXT};
        border-color: {COLOR_BORDER};
    }}

    QLabel {{
        color: {COLOR_TEXT};
        background: transparent;
    }}

    /* ── Inputs ───────────────────────────────────────────────────── */
    QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox {{
        background: {COLOR_SURFACE};
        color: {COLOR_TEXT};
        border: 1px solid {COLOR_BORDER};
        border-radius: {RADIUS_MD}px;
        padding: 4px 8px;
        min-height: 14px;
        selection-background-color: {COLOR_ACCENT};
    }}
    QLineEdit:hover, QDoubleSpinBox:hover, QSpinBox:hover, QComboBox:hover {{
        border-color: {COLOR_DIM};
    }}
    QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus, QComboBox:focus {{
        border-color: {COLOR_ACCENT};
        background: {COLOR_PANEL};
    }}
    QComboBox::drop-down {{
        border: none;
        padding-right: 8px;
    }}
    QComboBox QAbstractItemView {{
        background: {COLOR_PANEL};
        color: {COLOR_TEXT};
        border: 1px solid {COLOR_BORDER};
        border-radius: {RADIUS_SM}px;
        padding: 4px;
        selection-background-color: {COLOR_ACCENT_SOFT};
        selection-color: {COLOR_ACCENT};
    }}

    /* ── Cards / group boxes ──────────────────────────────────────── */
    QGroupBox {{
        background: {COLOR_SURFACE};
        color: {COLOR_MUTED};
        border: 1px solid {COLOR_BORDER};
        border-radius: {RADIUS_LG}px;
        margin-top: 10px;
        padding: 10px;
        font-weight: 600;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 10px;
        padding: 2px 8px;
        color: {COLOR_MUTED};
        background: {COLOR_PANEL};
        border: 1px solid {COLOR_BORDER};
        border-radius: {RADIUS_SM}px;
    }}
    QFrame[card="true"] {{
        background: {COLOR_SURFACE};
        border: 1px solid {COLOR_BORDER};
        border-radius: {RADIUS_LG}px;
    }}

    QScrollArea {{
        border: none;
        background: transparent;
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
        padding: 6px 10px;
        border-bottom: 1px solid {COLOR_BORDER};
        font-weight: 600;
    }}
    QTabWidget::pane {{
        border: 1px solid {COLOR_BORDER};
        border-radius: {RADIUS_MD}px;
        top: -1px;
    }}
    QTabBar::tab {{
        background: transparent;
        color: {COLOR_MUTED};
        border: none;
        padding: 8px 16px;
        margin-right: 2px;
        border-bottom: 2px solid transparent;
    }}
    QTabBar::tab:hover {{
        color: {COLOR_TEXT};
    }}
    QTabBar::tab:selected {{
        color: {COLOR_ACCENT};
        border-bottom: 2px solid {COLOR_ACCENT};
        font-weight: 600;
    }}
    QStatusBar {{
        background: {COLOR_SURFACE};
        color: {COLOR_MUTED};
        border-top: 1px solid {COLOR_BORDER};
    }}
    QStatusBar::item {{
        border: none;
    }}
    QToolBar {{
        background: {COLOR_SURFACE};
        border-bottom: 1px solid {COLOR_BORDER};
        spacing: 2px;
        padding: 3px 6px;
    }}
    QToolBar::separator {{
        background: {COLOR_BORDER};
        width: 1px;
        margin: 3px 4px;
    }}
    QToolBar QToolButton {{
        background: transparent;
        color: {COLOR_TEXT};
        border: 1px solid transparent;
        border-radius: {RADIUS_SM}px;
        padding: 3px 8px;
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
        border-radius: {RADIUS_MD}px;
        font-size: {FONT_SIZE_SMALL}pt;
    }}
    QTableWidget {{
        background: {COLOR_SURFACE};
        alternate-background-color: {COLOR_PANEL};
        color: {COLOR_TEXT};
        border: 1px solid {COLOR_BORDER};
        border-radius: {RADIUS_MD}px;
        gridline-color: transparent;
    }}
    QTableWidget::item {{
        padding: 4px 6px;
    }}
    QTableWidget::item:selected {{
        background: {COLOR_ACCENT_SOFT};
        color: {COLOR_ACCENT};
    }}
    QHeaderView::section {{
        background: {COLOR_PANEL};
        color: {COLOR_MUTED};
        border: none;
        border-bottom: 1px solid {COLOR_BORDER};
        padding: 7px 8px;
        font-size: {FONT_SIZE_SMALL}pt;
        font-weight: 600;
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
        border-radius: 5px;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLOR_ACCENT}, stop:1 {COLOR_ACCENT_2});
    }}
    QCheckBox {{
        color: {COLOR_TEXT};
        spacing: 6px;
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border: 1px solid {COLOR_BORDER};
        border-radius: 4px;
        background: {COLOR_SURFACE};
    }}
    QCheckBox::indicator:hover {{
        border-color: {COLOR_ACCENT};
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
