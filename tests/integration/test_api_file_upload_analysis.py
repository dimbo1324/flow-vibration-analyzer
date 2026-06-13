"""Integration tests: upload a real CSV and run analysis through the API."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from iva.api.main import app

client = TestClient(app)

# Real example CSV shipped with the project
_EXAMPLE_CSV = Path(__file__).resolve().parents[2] / "data" / "examples" / "example_clean_sine.csv"


@pytest.fixture(autouse=True)
def _require_example_csv() -> None:
    if not _EXAMPLE_CSV.exists():
        pytest.skip("example CSV not found — skipping integration test")


def _upload_example() -> str:
    """Upload example CSV and return file_id."""
    with _EXAMPLE_CSV.open("rb") as f:
        resp = client.post(
            "/api/files/upload",
            files={"file": ("example_clean_sine.csv", f, "text/csv")},
        )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert "file_id" in body
    assert "saved_path" not in body  # must not expose server path
    return body["file_id"]


def test_upload_returns_metadata() -> None:
    file_id = _upload_example()
    resp = client.get(f"/api/files/{file_id}/preview")
    assert resp.status_code == 200
    body = resp.json()
    assert "columns" in body
    assert "time_s" in body["columns"]


def test_upload_reject_bad_extension() -> None:
    resp = client.post(
        "/api/files/upload",
        files={"file": ("script.exe", b"MZ\x00", "application/octet-stream")},
    )
    assert resp.status_code == 400
    assert "не поддерживается" in resp.json()["error"]["message"]


def test_upload_analysis_returns_result() -> None:
    file_id = _upload_example()
    payload = {
        "file_id": file_id,
        "role_assignment": {
            "time_column": "time_s",
            "primary_signal_column": "signal",
            "signal_role": "acceleration_y",
            "sampling_rate_hz": 1000.0,
        },
        "settings": {
            "flow_parameters": {
                "cylinder_diameter_m": 0.012,
                "mean_flow_velocity_ms": 2.0,
                "fluid_density_kgm3": 998.0,
                "dynamic_viscosity_pas": 0.001002,
                "natural_frequency_hz": 40.0,
            }
        },
    }
    resp = client.post("/api/analysis/upload", json=payload)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "analysis_id" in body
    assert "summary" in body
    assert "signal" in body
    assert "spectrum" in body
    # Must not expose server paths
    assert "saved_path" not in body
    # Arrays must be lists
    assert isinstance(body["signal"]["time_s"], list)
    assert isinstance(body["spectrum"]["frequencies_hz"], list)


def test_upload_analysis_unknown_file_id() -> None:
    resp = client.post(
        "/api/analysis/upload",
        json={"file_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert resp.status_code == 404


def test_get_analysis_by_id() -> None:
    file_id = _upload_example()
    payload = {
        "file_id": file_id,
        "role_assignment": {
            "time_column": "time_s",
            "primary_signal_column": "signal",
            "signal_role": "acceleration_y",
            "sampling_rate_hz": 1000.0,
        },
    }
    post_resp = client.post("/api/analysis/upload", json=payload)
    assert post_resp.status_code == 200
    analysis_id = post_resp.json()["analysis_id"]

    get_resp = client.get(f"/api/analysis/{analysis_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["analysis_id"] == analysis_id


def test_get_analysis_unknown_id() -> None:
    resp = client.get("/api/analysis/does-not-exist")
    assert resp.status_code == 404


def test_large_arrays_bounded() -> None:
    file_id = _upload_example()
    payload = {
        "file_id": file_id,
        "role_assignment": {
            "time_column": "time_s",
            "primary_signal_column": "signal",
            "signal_role": "acceleration_y",
            "sampling_rate_hz": 1000.0,
        },
    }
    resp = client.post("/api/analysis/upload", json=payload)
    body = resp.json()
    from iva.api.serializers.analysis_serializer import MAX_POINTS

    assert len(body["signal"]["time_s"]) <= MAX_POINTS
    assert len(body["spectrum"]["frequencies_hz"]) <= MAX_POINTS
