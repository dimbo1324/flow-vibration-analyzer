"""Reporting package for the Industrial Vibration Analyzer.

Public API:
- :func:`build_report_document` — build a :class:`ReportDocument` from an :class:`AnalysisResult`.
- :func:`export_pdf_report` — write a PDF report to disk.
- :func:`export_html_report` — write a standalone HTML report to disk.
"""

from __future__ import annotations

from iva.infrastructure.reporting.html_report_writer import export_html_report
from iva.infrastructure.reporting.pdf_report_writer import export_pdf_report
from iva.infrastructure.reporting.report_builder import build_report_document

__all__ = [
    "build_report_document",
    "export_pdf_report",
    "export_html_report",
]
