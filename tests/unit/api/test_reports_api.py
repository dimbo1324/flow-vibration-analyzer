"""Unit tests for the reports API routes (no real pipeline run)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from iva.api.main import app

client = TestClient(app)


def test_html_report_unknown_analysis_id() -> None:
    resp = client.get("/api/analysis/does-not-exist/reports/html")
    assert resp.status_code == 404
    body = resp.json()
    assert body["error"]["code"] == "ANALYSIS_NOT_FOUND"


def test_pdf_report_unknown_analysis_id() -> None:
    resp = client.get("/api/analysis/does-not-exist/reports/pdf")
    assert resp.status_code == 404


def test_spectrum_export_unknown_analysis_id() -> None:
    resp = client.get("/api/analysis/does-not-exist/exports/spectrum")
    assert resp.status_code == 404


def test_signal_export_unknown_analysis_id() -> None:
    resp = client.get("/api/analysis/does-not-exist/exports/signal")
    assert resp.status_code == 404


def test_physics_export_unknown_analysis_id() -> None:
    resp = client.get("/api/analysis/does-not-exist/exports/physics")
    assert resp.status_code == 404
