"""Stage 9 report writer tests."""

from __future__ import annotations

from pathlib import Path

from iva.infrastructure.reporting import export_html_report, export_pdf_report


def test_html_report_is_non_empty_and_escapes_user_content(stage9_result, tmp_path: Path) -> None:
    path = export_html_report(stage9_result, tmp_path / "nested" / "report.html")
    content = path.read_text(encoding="utf-8")
    assert path.stat().st_size > 0
    assert "warning &lt;unsafe&gt;" in content
    assert "warning <unsafe>" not in content
    assert '<html lang="ru">' in content
    assert "Отчет об анализе IVA" in content
    assert "Оценка риска" in content
    assert "НАБЛЮДЕНИЕ" in content
    assert "Risk Assessment" not in content
    assert "Source file" not in content


def test_pdf_report_is_real_and_non_empty(stage9_result, tmp_path: Path) -> None:
    path = export_pdf_report(stage9_result, tmp_path / "report.pdf")
    assert path.read_bytes().startswith(b"%PDF")
    assert path.stat().st_size > 500


def test_html_summary_is_localized(minimal_result, tmp_path: Path) -> None:
    from iva.infrastructure.writers.html_summary_writer import export_analysis_summary_html

    path = export_analysis_summary_html(minimal_result, tmp_path / "summary.html")
    content = path.read_text(encoding="utf-8")
    assert '<html lang="ru">' in content
    assert "Сводка анализа IVA" in content
    assert "Спектральный анализ" in content
    assert "Оценка риска" in content
