"""End-to-end demo analysis, report, and project persistence tests."""

from __future__ import annotations

from pathlib import Path

from iva.app.demo_service import create_demo_session
from iva.app.report_service import export_report_html, export_report_pdf
from iva.app.session_service import load_saved_session, save_current_session
from iva.app.workflow_coordinator import run_pipeline


def test_demo_flow_exports_reports_and_roundtrips_project(tmp_path: Path) -> None:
    session = create_demo_session("clean_40hz", tmp_path / "runtime")
    result = run_pipeline(session)
    html_path = export_report_html(result, tmp_path / "report.html")
    pdf_path = export_report_pdf(result, tmp_path / "report.pdf")
    project_path = save_current_session(session, tmp_path / "demo.vibproj")

    html = html_path.read_text(encoding="utf-8")
    assert "Демонстрационные синтетические данные" in html
    assert "Данные сгенерированы программно" in html
    assert pdf_path.read_bytes().startswith(b"%PDF")

    loaded = load_saved_session(project_path)
    assert loaded.is_demo is True
    assert loaded.demo_scenario_key == "clean_40hz"
    assert loaded.result is not None and loaded.result.is_demo is True
