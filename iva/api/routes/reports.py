"""Report download endpoints.

GET /api/analysis/{analysis_id}/reports/html       — HTML report
GET /api/analysis/{analysis_id}/reports/pdf        — PDF report
GET /api/analysis/{analysis_id}/exports/spectrum   — spectrum CSV
GET /api/analysis/{analysis_id}/exports/signal     — signal CSV
GET /api/analysis/{analysis_id}/exports/physics    — physics summary CSV
"""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse

from iva.api.errors import api_error_response
from iva.api.services.analysis_service import analysis_service
from iva.api.utils import validate_resource_id
from iva.app.report_service import (
    export_report_html,
    export_report_pdf,
    export_report_physics_csv,
    export_report_signal_csv,
    export_report_spectrum_csv,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analysis", tags=["reports"])

_REPORTS_DIR = Path("out") / "web" / "reports"


def _report_dir(analysis_id: str) -> Path:
    validate_resource_id(analysis_id)
    d = (_REPORTS_DIR / analysis_id).resolve()
    d.mkdir(parents=True, exist_ok=True)
    return d


@router.get("/{analysis_id}/reports/html", response_model=None)
async def download_html_report(analysis_id: str) -> FileResponse | JSONResponse:
    """Generate (or reuse) and stream an HTML report."""
    stored = analysis_service.get(analysis_id)
    if stored is None:
        return api_error_response(404, "ANALYSIS_NOT_FOUND", "Результат анализа не найден.")

    try:
        report_dir = _report_dir(analysis_id)
    except ValueError:
        return api_error_response(400, "INVALID_ID", "Некорректный идентификатор.")

    dest = report_dir / "report.html"
    if not dest.exists():
        export_report_html(stored.result, dest)

    safe_name = f"iva_report_{analysis_id[:8]}.html"
    return FileResponse(
        path=str(dest),
        media_type="text/html",
        filename=safe_name,
    )


@router.get("/{analysis_id}/reports/pdf", response_model=None)
async def download_pdf_report(analysis_id: str) -> FileResponse | JSONResponse:
    """Generate (or reuse) and stream a PDF report."""
    stored = analysis_service.get(analysis_id)
    if stored is None:
        return api_error_response(404, "ANALYSIS_NOT_FOUND", "Результат анализа не найден.")

    try:
        report_dir = _report_dir(analysis_id)
    except ValueError:
        return api_error_response(400, "INVALID_ID", "Некорректный идентификатор.")

    dest = report_dir / "report.pdf"
    if not dest.exists():
        try:
            export_report_pdf(stored.result, dest)
        except Exception as exc:
            logger.warning("PDF export failed: %s", exc)
            return api_error_response(
                500,
                "REPORT_ERROR",
                "Не удалось создать PDF-отчёт. Проверьте, установлен ли reportlab.",
            )

    safe_name = f"iva_report_{analysis_id[:8]}.pdf"
    return FileResponse(
        path=str(dest),
        media_type="application/pdf",
        filename=safe_name,
    )


@router.get("/{analysis_id}/exports/spectrum", response_model=None)
async def export_spectrum(analysis_id: str) -> FileResponse | JSONResponse:
    """Export spectrum data as CSV."""
    stored = analysis_service.get(analysis_id)
    if stored is None:
        return api_error_response(404, "ANALYSIS_NOT_FOUND", "Результат анализа не найден.")

    try:
        report_dir = _report_dir(analysis_id)
    except ValueError:
        return api_error_response(400, "INVALID_ID", "Некорректный идентификатор.")

    dest = report_dir / "spectrum.csv"
    if not dest.exists():
        export_report_spectrum_csv(stored.result, dest)

    return FileResponse(
        path=str(dest),
        media_type="text/csv",
        filename=f"iva_spectrum_{analysis_id[:8]}.csv",
    )


@router.get("/{analysis_id}/exports/signal", response_model=None)
async def export_signal(analysis_id: str) -> FileResponse | JSONResponse:
    """Export signal data as CSV."""
    stored = analysis_service.get(analysis_id)
    if stored is None:
        return api_error_response(404, "ANALYSIS_NOT_FOUND", "Результат анализа не найден.")

    try:
        report_dir = _report_dir(analysis_id)
    except ValueError:
        return api_error_response(400, "INVALID_ID", "Некорректный идентификатор.")

    dest = report_dir / "signal.csv"
    if not dest.exists():
        export_report_signal_csv(stored.result, dest)

    return FileResponse(
        path=str(dest),
        media_type="text/csv",
        filename=f"iva_signal_{analysis_id[:8]}.csv",
    )


@router.get("/{analysis_id}/exports/physics", response_model=None)
async def export_physics(analysis_id: str) -> FileResponse | JSONResponse:
    """Export physics summary as CSV."""
    stored = analysis_service.get(analysis_id)
    if stored is None:
        return api_error_response(404, "ANALYSIS_NOT_FOUND", "Результат анализа не найден.")

    try:
        report_dir = _report_dir(analysis_id)
    except ValueError:
        return api_error_response(400, "INVALID_ID", "Некорректный идентификатор.")

    dest = report_dir / "physics_summary.csv"
    if not dest.exists():
        export_report_physics_csv(stored.result, dest)

    return FileResponse(
        path=str(dest),
        media_type="text/csv",
        filename=f"iva_physics_{analysis_id[:8]}.csv",
    )
