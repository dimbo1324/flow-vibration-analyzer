"""Unit tests for iva.infrastructure.reporting.report_builder."""

from __future__ import annotations

from iva.infrastructure.reporting.report_builder import build_report_document
from iva.infrastructure.reporting.report_models import ReportDocument


class TestBuildReportDocument:
    def test_returns_report_document(self, minimal_result):
        doc = build_report_document(minimal_result)
        assert isinstance(doc, ReportDocument)

    def test_sections_non_empty(self, minimal_result):
        doc = build_report_document(minimal_result)
        assert len(doc.sections) > 0

    def test_has_overview_section(self, minimal_result):
        doc = build_report_document(minimal_result)
        titles = [s.title for s in doc.sections]
        assert "Overview" in titles

    def test_has_spectral_section(self, minimal_result):
        doc = build_report_document(minimal_result)
        titles = [s.title for s in doc.sections]
        assert "Spectral Analysis" in titles

    def test_has_physics_section(self, minimal_result):
        doc = build_report_document(minimal_result)
        titles = [s.title for s in doc.sections]
        assert "Physics" in titles

    def test_has_risk_section(self, minimal_result):
        doc = build_report_document(minimal_result)
        titles = [s.title for s in doc.sections]
        assert "Risk Assessment" in titles

    def test_has_warnings_section(self, minimal_result):
        doc = build_report_document(minimal_result)
        titles = [s.title for s in doc.sections]
        assert "Warnings" in titles

    def test_peaks_table_present(self, minimal_result):
        doc = build_report_document(minimal_result)
        assert len(doc.tables) >= 1

    def test_no_physics_graceful(self, result_no_physics):
        doc = build_report_document(result_no_physics)
        titles = [s.title for s in doc.sections]
        assert "Physics" in titles
        # Ensure no exception raised
        assert len(doc.sections) > 0

    def test_metadata_has_session_id(self, minimal_result):
        doc = build_report_document(minimal_result)
        assert "session_id" in doc.metadata
        assert doc.metadata["session_id"] == minimal_result.session_id

    def test_title_set(self, minimal_result):
        doc = build_report_document(minimal_result)
        assert "IVA" in doc.title or "Report" in doc.title

    def test_generated_at_set(self, minimal_result):
        from datetime import datetime

        doc = build_report_document(minimal_result)
        assert isinstance(doc.generated_at, datetime)
