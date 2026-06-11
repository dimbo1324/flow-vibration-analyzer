"""PDF report writer using ReportLab.

Generates a professional A4 PDF report from an :class:`AnalysisResult`.
The report uses a *light* background suitable for printing.

Cyrillic text is rendered with an embedded TrueType font.  The writer checks
the platform font directory and matplotlib's bundled DejaVu Sans fonts.

Architecture rule: no numerical calculations here — only serialisation.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any
from xml.sax.saxutils import escape

from iva.core.models.exceptions import ExportError
from iva.infrastructure.reporting.report_builder import build_report_document

if TYPE_CHECKING:
    from iva.core.models.analysis_result import AnalysisResult

logger = logging.getLogger(__name__)

__all__ = ["export_pdf_report"]

# ReportLab is an optional dependency from the project's requirements.txt.
# Import it lazily to avoid hard failures if it is somehow absent.
try:
    from reportlab.lib import colors  # type: ignore[import-untyped]
    from reportlab.lib.pagesizes import A4  # type: ignore[import-untyped]
    from reportlab.lib.styles import (  # type: ignore[import-untyped]
        ParagraphStyle,
        getSampleStyleSheet,
    )
    from reportlab.lib.units import mm  # type: ignore[import-untyped]
    from reportlab.pdfbase import pdfmetrics  # type: ignore[import-untyped]
    from reportlab.pdfbase.ttfonts import TTFont  # type: ignore[import-untyped]
    from reportlab.platypus import (  # type: ignore[import-untyped]
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    _REPORTLAB_AVAILABLE = True
except ImportError:  # pragma: no cover
    _REPORTLAB_AVAILABLE = False


def export_pdf_report(result: AnalysisResult, output_path: str | Path) -> Path:
    """Export a full PDF analysis report to *output_path*.

    Args:
        result: Completed analysis result.
        output_path: Destination file path (``*.pdf``).  Parent directories
            are created automatically.

    Returns:
        The resolved output :class:`~pathlib.Path`.

    Raises:
        ExportError: If ReportLab is unavailable or the file cannot be written.
    """
    if not _REPORTLAB_AVAILABLE:
        raise ExportError(
            user_message="Экспорт PDF недоступен: библиотека reportlab не установлена.",
            technical_details="import reportlab failed",
            recovery_hint="Установите библиотеку командой: pip install reportlab",
        )

    output_path = Path(output_path)
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        _write_pdf(result, output_path)
    except ExportError:
        raise
    except Exception as exc:
        raise ExportError(
            user_message=f"Не удалось записать отчет PDF в файл '{output_path.name}'.",
            technical_details=str(exc),
        ) from exc

    logger.info("export_pdf_report: written to '%s'", output_path.name)
    return output_path


# ---------------------------------------------------------------------------
# Internal implementation
# ---------------------------------------------------------------------------


def _font_candidates() -> tuple[list[Path], list[Path]]:
    regular = [
        Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "arial.ttf",
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
    ]
    bold = [
        Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "arialbd.ttf",
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"),
    ]
    try:
        from matplotlib import get_data_path  # type: ignore[import-untyped]

        font_dir = Path(get_data_path()) / "fonts" / "ttf"
        regular.append(font_dir / "DejaVuSans.ttf")
        bold.append(font_dir / "DejaVuSans-Bold.ttf")
    except ImportError:
        pass
    return regular, bold


def _register_pdf_fonts() -> tuple[str, str]:
    """Register Cyrillic-capable fonts and return regular/bold names."""
    regular_candidates, bold_candidates = _font_candidates()
    regular_path = next((path for path in regular_candidates if path.is_file()), None)
    bold_path = next((path for path in bold_candidates if path.is_file()), regular_path)
    if regular_path is None or bold_path is None:
        raise ExportError(
            user_message="Не найден шрифт с поддержкой кириллицы для экспорта PDF.",
            technical_details="No Arial, DejaVu Sans, or Liberation Sans TTF font found",
            recovery_hint="Установите шрифт DejaVu Sans и повторите экспорт.",
        )
    if "IVARegular" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("IVARegular", str(regular_path)))
    if "IVABold" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("IVABold", str(bold_path)))
    return "IVARegular", "IVABold"


def _safe_str(text: str) -> str:
    """Escape text for ReportLab while preserving Unicode characters."""
    return escape(str(text))


def _write_pdf(result: AnalysisResult, output_path: Path) -> None:  # noqa: C901
    """Build and write the PDF document."""
    doc_model = build_report_document(result)
    regular_font, bold_font = _register_pdf_fonts()

    doc = SimpleDocTemplate(  # type: ignore[possibly-undefined]
        str(output_path),
        pagesize=A4,  # type: ignore[possibly-undefined]
        rightMargin=20 * mm,  # type: ignore[possibly-undefined]
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    base_styles = getSampleStyleSheet()  # type: ignore[possibly-undefined]

    # Define custom paragraph styles
    title_style = ParagraphStyle(  # type: ignore[possibly-undefined]
        "IVATitle",
        parent=base_styles["Title"],
        fontName=bold_font,
        fontSize=18,
        spaceAfter=6,
        textColor=colors.HexColor("#111111"),  # type: ignore[possibly-undefined]
    )
    subtitle_style = ParagraphStyle(
        "IVASubtitle",
        parent=base_styles["Normal"],
        fontName=regular_font,
        fontSize=11,
        textColor=colors.HexColor("#555555"),
        spaceAfter=12,
    )
    heading1_style = ParagraphStyle(
        "IVAHeading1",
        parent=base_styles["Heading1"],
        fontName=bold_font,
        fontSize=13,
        textColor=colors.HexColor("#222222"),
        spaceBefore=12,
        spaceAfter=4,
        borderPad=4,
    )
    body_style = ParagraphStyle(
        "IVABody",
        parent=base_styles["Normal"],
        fontName=regular_font,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#1a1a1a"),
        spaceAfter=6,
    )
    meta_style = ParagraphStyle(
        "IVAMeta",
        parent=base_styles["Normal"],
        fontName=regular_font,
        fontSize=9,
        textColor=colors.HexColor("#666666"),
        spaceAfter=4,
    )

    story: list[Any] = []

    # ── Title page ────────────────────────────────────────────────────────
    story.append(Paragraph(_safe_str(doc_model.title), title_style))
    story.append(Paragraph(_safe_str(doc_model.subtitle), subtitle_style))
    story.append(Spacer(1, 4 * mm))

    # Metadata block
    meta_items = [
        f"ID сеанса: {doc_model.metadata.get('session_id', '')}",
        f"Сформировано: {doc_model.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"MD5 источника: {doc_model.metadata.get('source_file_md5', '')}",
    ]
    for item in meta_items:
        story.append(Paragraph(_safe_str(item), meta_style))
    story.append(Spacer(1, 6 * mm))

    # ── Sections ──────────────────────────────────────────────────────────
    for section in doc_model.sections:
        story.append(Paragraph(_safe_str(section.title), heading1_style))
        # Preserve newlines in body text
        body_lines = section.body.split("\n")
        for line in body_lines:
            if line.strip():
                story.append(Paragraph(_safe_str(line), body_style))
            else:
                story.append(Spacer(1, 3 * mm))
        story.append(Spacer(1, 4 * mm))

    # ── Tables ────────────────────────────────────────────────────────────
    if doc_model.tables:
        story.append(PageBreak())
        for tbl in doc_model.tables:
            story.append(Paragraph(_safe_str(tbl.title), heading1_style))
            story.append(Spacer(1, 2 * mm))

            table_data: list[list[str]] = [[_safe_str(header) for header in tbl.headers]]
            for row in tbl.rows:
                table_data.append([_safe_str(cell) for cell in row])

            # Calculate column widths
            n_cols = len(tbl.headers)
            available_width = A4[0] - 40 * mm
            col_width = available_width / max(n_cols, 1)
            col_widths = [col_width] * n_cols

            rl_table = Table(table_data, colWidths=col_widths)
            rl_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#111111")),
                        ("FONTNAME", (0, 0), (-1, 0), bold_font),
                        ("FONTNAME", (0, 1), (-1, -1), regular_font),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bbbbbb")),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [colors.white, colors.HexColor("#f7f7f7")],
                        ),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            story.append(rl_table)
            story.append(Spacer(1, 6 * mm))

    doc.build(story)
