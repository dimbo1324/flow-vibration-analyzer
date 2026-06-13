"""Integration tests: reports and sessions API after a real upload+analysis."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from iva.api.main import app

client = TestClient(app)

_EXAMPLE_CSV = Path(__file__).resolve().parents[2] / "data" / "examples" / "example_clean_sine.csv"


@pytest.fixture(autouse=True)
def _require_example_csv() -> None:
    if not _EXAMPLE_CSV.exists():
        pytest.skip("example CSV not found")


@pytest.fixture()
def analysis_id() -> str:
    """Upload example CSV and run analysis; return analysis_id."""
    with _EXAMPLE_CSV.open("rb") as f:
        up = client.post(
            "/api/files/upload",
            files={"file": ("example_clean_sine.csv", f, "text/csv")},
        )
    file_id = up.json()["file_id"]

    an = client.post(
        "/api/analysis/upload",
        json={
            "file_id": file_id,
            "role_assignment": {
                "time_column": "time_s",
                "primary_signal_column": "signal",
                "signal_role": "acceleration_y",
                "sampling_rate_hz": 1000.0,
            },
        },
    )
    assert an.status_code == 200, an.text
    return an.json()["analysis_id"]


def test_html_report_returns_file(analysis_id: str) -> None:
    resp = client.get(f"/api/analysis/{analysis_id}/reports/html")
    assert resp.status_code == 200
    ct = resp.headers.get("content-type", "")
    assert "html" in ct


def test_spectrum_csv_returns_file(analysis_id: str) -> None:
    resp = client.get(f"/api/analysis/{analysis_id}/exports/spectrum")
    assert resp.status_code == 200
    assert "csv" in resp.headers.get("content-type", "")


def test_signal_csv_returns_file(analysis_id: str) -> None:
    resp = client.get(f"/api/analysis/{analysis_id}/exports/signal")
    assert resp.status_code == 200
    assert "csv" in resp.headers.get("content-type", "")


def test_physics_csv_returns_file(analysis_id: str) -> None:
    resp = client.get(f"/api/analysis/{analysis_id}/exports/physics")
    assert resp.status_code == 200
    assert "csv" in resp.headers.get("content-type", "")


def test_session_export_returns_vibproj(analysis_id: str) -> None:
    resp = client.post(f"/api/sessions/export/{analysis_id}")
    assert resp.status_code == 200
    cd = resp.headers.get("content-disposition", "")
    assert ".vibproj" in cd or resp.headers.get("content-type", "") == "application/json"
    # Content must be valid JSON
    import json

    try:
        data = json.loads(resp.content)
    except ValueError:
        pytest.fail("Session export is not valid JSON")
    assert "_vibproj_version" in data


def test_session_import_invalid_file() -> None:
    resp = client.post(
        "/api/sessions/import",
        files={"file": ("broken.vibproj", b"not json", "application/json")},
    )
    assert resp.status_code == 400


def test_session_roundtrip(analysis_id: str) -> None:
    """Export session and import it back — summary should be present."""
    export_resp = client.post(f"/api/sessions/export/{analysis_id}")
    assert export_resp.status_code == 200

    import_resp = client.post(
        "/api/sessions/import",
        files={"file": ("session.vibproj", export_resp.content, "application/json")},
    )
    assert import_resp.status_code == 200
    body = import_resp.json()
    assert body["has_result"] is True
    assert "result" in body
