"""Report export service — orchestrates all output formats for one analysis result.

This module provides the application-layer facade over the infrastructure
reporting and CSV export writers.  It creates a bundle of all output formats
in a single output directory.

Architecture rule: no numerical calculations here — only coordination.
Must NOT import from iva.ui or PySide6.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from iva.infrastructure.reporting.html_report_writer import export_html_report
from iva.infrastructure.reporting.pdf_report_writer import export_pdf_report
from iva.infrastructure.writers.csv_export_writer import (
    export_physics_summary_csv,
    export_signal_csv,
    export_spectrum_csv,
)
from iva.infrastructure.writers.json_export_writer import export_analysis_summary_json

if TYPE_CHECKING:
    from iva.core.models.analysis_result import AnalysisResult

logger = logging.getLogger(__name__)

__all__ = [
    "export_report_pdf",
    "export_report_html",
    "export_report_json",
    "export_report_spectrum_csv",
    "export_report_signal_csv",
    "export_report_physics_csv",
    "export_report_bundle",
]


def export_report_pdf(result: AnalysisResult, output_path: str | Path) -> Path:
    """Export a PDF report through the application facade."""
    return export_pdf_report(result, output_path)


def export_report_html(result: AnalysisResult, output_path: str | Path) -> Path:
    """Export an HTML report through the application facade."""
    return export_html_report(result, output_path)


def export_report_json(result: AnalysisResult, output_path: str | Path) -> Path:
    """Export the JSON summary through the application facade."""
    return export_analysis_summary_json(result, output_path)


def export_report_spectrum_csv(result: AnalysisResult, output_path: str | Path) -> Path:
    """Export spectrum data through the application facade."""
    return export_spectrum_csv(result, output_path)


def export_report_signal_csv(result: AnalysisResult, output_path: str | Path) -> Path:
    """Export processed signal data through the application facade."""
    return export_signal_csv(result, output_path)


def export_report_physics_csv(result: AnalysisResult, output_path: str | Path) -> Path:
    """Export physics data through the application facade."""
    return export_physics_summary_csv(result, output_path)


def export_report_bundle(
    result: AnalysisResult,
    output_dir: str | Path,
) -> dict[str, Path]:
    """Export all output formats for *result* into *output_dir*.

    Formats attempted:
    - ``pdf``         — full PDF report (requires reportlab).
    - ``html``        — standalone HTML report.
    - ``json_summary``— concise JSON summary.
    - ``spectrum_csv``— spectrum CSV.
    - ``signal_csv``  — signal CSV (skipped if ``processed_data`` is None).
    - ``physics_csv`` — physics / risk CSV.

    PDF and HTML are required bundle outputs and propagate export failures.
    Optional CSV/JSON failures are logged so the remaining files can still be
    delivered.

    Args:
        result: Completed analysis result.
        output_dir: Directory where output files will be written.

    Returns:
        A ``dict`` mapping format keys to the paths of written files.
        Formats that failed are absent from the dict.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    written: dict[str, Path] = {}

    written["pdf"] = export_report_pdf(result, output_dir / "report.pdf")
    written["html"] = export_report_html(result, output_dir / "report.html")

    # JSON summary
    try:
        p = export_analysis_summary_json(result, output_dir / "analysis_summary.json")
        written["json_summary"] = p
    except Exception as exc:  # noqa: BLE001
        logger.warning("export_report_bundle: JSON export failed: %s", exc)

    # Spectrum CSV
    try:
        p = export_spectrum_csv(result, output_dir / "spectrum.csv")
        written["spectrum_csv"] = p
    except Exception as exc:  # noqa: BLE001
        logger.warning("export_report_bundle: spectrum CSV export failed: %s", exc)

    # Signal CSV
    try:
        p = export_signal_csv(result, output_dir / "signal.csv")
        written["signal_csv"] = p
    except Exception as exc:  # noqa: BLE001
        logger.warning("export_report_bundle: signal CSV export failed: %s", exc)

    # Physics CSV
    try:
        p = export_physics_summary_csv(result, output_dir / "physics_summary.csv")
        written["physics_csv"] = p
    except Exception as exc:  # noqa: BLE001
        logger.warning("export_report_bundle: physics CSV export failed: %s", exc)

    logger.info("export_report_bundle: %d formats written to '%s'", len(written), output_dir)
    return written
