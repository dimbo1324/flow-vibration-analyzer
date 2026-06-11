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


def test_pdf_report_is_real_and_non_empty(stage9_result, tmp_path: Path) -> None:
    path = export_pdf_report(stage9_result, tmp_path / "report.pdf")
    assert path.read_bytes().startswith(b"%PDF")
    assert path.stat().st_size > 500
