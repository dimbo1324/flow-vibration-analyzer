"""Full HTML report writer for analysis results.

Generates a standalone HTML report (no external dependencies, no JavaScript)
from an :class:`AnalysisResult`.  All user-supplied content is escaped with
:func:`html.escape` to prevent injection.

Unlike the minimal :mod:`html_summary_writer`, this module renders a fully
structured report with all sections and tables matching the PDF report.

Architecture rule: no numerical calculations here — only serialisation.
"""

from __future__ import annotations

import html
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from iva.core.models.exceptions import ExportError
from iva.infrastructure.reporting.report_builder import build_report_document

if TYPE_CHECKING:
    from iva.core.models.analysis_result import AnalysisResult

logger = logging.getLogger(__name__)

__all__ = ["export_html_report"]


def export_html_report(result: AnalysisResult, output_path: str | Path) -> Path:
    """Write a full standalone HTML report to *output_path*.

    Args:
        result: Completed analysis result.
        output_path: Destination file path (created if necessary).

    Returns:
        The resolved output path.

    Raises:
        ExportError: If the file cannot be written.
    """
    output_path = Path(output_path)
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        doc_model = build_report_document(result)
        content = _render_html(result, doc_model)
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write(content)
    except (OSError, ValueError) as exc:
        raise ExportError(
            user_message=f"Не удалось записать отчет HTML в файл '{output_path.name}'.",
            technical_details=str(exc),
        ) from exc

    logger.info("export_html_report: written to '%s'", output_path.name)
    return output_path


# ---------------------------------------------------------------------------
# Internal rendering
# ---------------------------------------------------------------------------


def _e(text: str) -> str:
    """HTML-escape *text*."""
    return html.escape(str(text))


def _render_html(result: AnalysisResult, doc_model: object) -> str:  # noqa: C901
    """Build the full HTML document string from *doc_model*."""
    from iva.infrastructure.reporting.report_models import ReportDocument

    assert isinstance(doc_model, ReportDocument)

    # ── Sections HTML ────────────────────────────────────────────────────
    sections_html = ""
    for section in doc_model.sections:
        level = max(1, min(6, section.level + 1))  # h2..h7 (body uses h2+)
        body_escaped = _e(section.body).replace("\n", "<br>\n")
        sections_html += (
            f"  <section>\n"
            f"    <h{level}>{_e(section.title)}</h{level}>\n"
            f'    <p class="body-text">{body_escaped}</p>\n'
            f"  </section>\n"
        )

    # ── Tables HTML ───────────────────────────────────────────────────────
    tables_html = ""
    for tbl in doc_model.tables:
        header_cells = "".join(f"<th>{_e(h)}</th>" for h in tbl.headers)
        rows_html = ""
        for i, row in enumerate(tbl.rows):
            cls = "even" if i % 2 == 0 else "odd"
            cells = "".join(f"<td>{_e(cell)}</td>" for cell in row)
            rows_html += f'    <tr class="{cls}">{cells}</tr>\n'
        tables_html += (
            f"  <section>\n"
            f"    <h2>{_e(tbl.title)}</h2>\n"
            f"    <table>\n"
            f"      <thead><tr>{header_cells}</tr></thead>\n"
            f"      <tbody>\n{rows_html}      </tbody>\n"
            f"    </table>\n"
            f"  </section>\n"
        )

    generated = _e(doc_model.generated_at.strftime("%Y-%m-%d %H:%M:%S UTC"))
    source_name = _e(result.source_file_path.name)
    session_id = _e(result.session_id)
    md5 = _e(result.source_file_md5)

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Отчет IVA &mdash; {source_name}</title>
  <style>
    /* Light, professional report style */
    *, *::before, *::after {{ box-sizing: border-box; }}
    body {{
      font-family: Arial, Helvetica, sans-serif;
      font-size: 13px;
      color: #1a1a1a;
      background: #f4f4f4;
      margin: 0;
      padding: 0;
    }}
    .page {{
      max-width: 900px;
      margin: 2em auto;
      background: #ffffff;
      border: 1px solid #cccccc;
      border-radius: 4px;
      padding: 2em 2.5em;
      box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }}
    header {{
      border-bottom: 2px solid #222;
      margin-bottom: 1.5em;
      padding-bottom: 1em;
    }}
    header h1 {{
      margin: 0 0 0.2em;
      font-size: 22px;
      color: #111;
    }}
    header p {{
      margin: 0;
      font-size: 11px;
      color: #666;
    }}
    section {{ margin-bottom: 1.8em; }}
    h2 {{
      font-size: 15px;
      font-weight: bold;
      color: #222;
      border-bottom: 1px solid #ddd;
      padding-bottom: 0.3em;
      margin-top: 1.5em;
    }}
    h3 {{ font-size: 13px; color: #333; }}
    .body-text {{
      white-space: pre-wrap;
      font-family: "Courier New", monospace;
      font-size: 11px;
      background: #f8f8f8;
      border: 1px solid #e0e0e0;
      border-radius: 3px;
      padding: 0.7em 1em;
      line-height: 1.6;
    }}
    table {{
      border-collapse: collapse;
      width: 100%;
      margin-top: 0.5em;
      font-size: 11px;
    }}
    th {{
      background: #e8e8e8;
      color: #111;
      font-weight: bold;
      text-align: left;
      padding: 6px 10px;
      border: 1px solid #ccc;
    }}
    td {{
      padding: 5px 10px;
      border: 1px solid #ddd;
    }}
    tr.even {{ background: #ffffff; }}
    tr.odd  {{ background: #f7f7f7; }}
    footer {{
      margin-top: 2em;
      padding-top: 1em;
      border-top: 1px solid #ddd;
      font-size: 10px;
      color: #888;
    }}
  </style>
</head>
<body>
  <div class="page">
    <header>
      <h1>Отчет об анализе IVA</h1>
      <p>Исходный файл: <strong>{source_name}</strong></p>
      <p>ID сеанса: {session_id} &nbsp;&bull;&nbsp; Сформировано: {generated}</p>
      <p>MD5: {md5}</p>
    </header>

{sections_html}
{tables_html}

    <footer>
      <p>Сформировано приложением «Анализатор вибраций потока» (IVA).
      Отчет предназначен для инженерного анализа.</p>
    </footer>
  </div>
</body>
</html>
"""
