"""Report assets: constants and colour palette for exported reports.

Exported reports (PDF, HTML) use a *light* background — the opposite of the
dark in-app theme.  All colour constants defined here are intended for report
output only and must NOT be used in the Qt UI.
"""

from __future__ import annotations

__all__ = [
    "REPORT_BG",
    "REPORT_TEXT",
    "REPORT_HEADING",
    "REPORT_MUTED",
    "REPORT_ACCENT",
    "REPORT_GOOD",
    "REPORT_WARN",
    "REPORT_BAD",
    "REPORT_BORDER",
    "IVA_APP_NAME",
    "IVA_REPORT_TITLE",
]

# Light-mode palette for printed/exported reports
REPORT_BG = "#ffffff"
REPORT_TEXT = "#1a1a1a"
REPORT_HEADING = "#111111"
REPORT_MUTED = "#666666"
REPORT_ACCENT = "#2055c7"
REPORT_GOOD = "#1e7e34"
REPORT_WARN = "#856404"
REPORT_BAD = "#721c24"
REPORT_BORDER = "#cccccc"

IVA_APP_NAME = "Industrial Vibration Analyzer (IVA)"
IVA_REPORT_TITLE = "Отчет об анализе IVA"
