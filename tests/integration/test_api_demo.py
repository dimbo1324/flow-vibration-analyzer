"""Integration tests for the FastAPI demo analysis endpoints."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from iva.api.main import app

MAX_ARRAY_POINTS = 2000

client = TestClient(app)


def test_health_returns_200() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "app" in data
    assert "version" in data


def test_demo_scenarios_returns_items() -> None:
    response = client.get("/api/demo-scenarios")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) > 0
    keys = [item["key"] for item in data["items"]]
    assert "clean_40hz" in keys


def test_demo_scenarios_have_required_fields() -> None:
    response = client.get("/api/demo-scenarios")
    items = response.json()["items"]
    for item in items:
        assert "key" in item
        assert "title_ru" in item
        assert "description_ru" in item
        assert "expected_peak_hz" in item


def test_demo_analysis_clean_40hz_returns_result() -> None:
    response = client.post("/api/analysis/demo", json={"scenario_key": "clean_40hz"})
    assert response.status_code == 200
    data = response.json()
    assert data["is_demo"] is True
    assert "analysis_id" in data
    assert "summary" in data
    assert "signal" in data
    assert "spectrum" in data
    assert "warnings" in data


def test_demo_analysis_unknown_scenario_returns_404() -> None:
    response = client.post("/api/analysis/demo", json={"scenario_key": "nonexistent_scenario"})
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "UNKNOWN_SCENARIO"


def test_demo_analysis_error_shape() -> None:
    response = client.post("/api/analysis/demo", json={"scenario_key": "bad_key_xyz"})
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert "code" in data["error"]
    assert "message" in data["error"]
    # No traceback in response
    text = response.text
    assert "Traceback" not in text
    assert "File " not in text


def test_signal_arrays_bounded() -> None:
    response = client.post("/api/analysis/demo", json={"scenario_key": "clean_40hz"})
    assert response.status_code == 200
    signal = response.json()["signal"]
    assert len(signal["time_s"]) <= MAX_ARRAY_POINTS
    assert len(signal["raw"]) <= MAX_ARRAY_POINTS
    assert len(signal["filtered"]) <= MAX_ARRAY_POINTS


def test_spectrum_arrays_bounded() -> None:
    response = client.post("/api/analysis/demo", json={"scenario_key": "clean_40hz"})
    assert response.status_code == 200
    spectrum = response.json()["spectrum"]
    assert len(spectrum["frequencies_hz"]) <= MAX_ARRAY_POINTS
    assert len(spectrum["psd"]) <= MAX_ARRAY_POINTS


def test_response_is_json_serializable() -> None:
    response = client.post("/api/analysis/demo", json={"scenario_key": "clean_40hz"})
    assert response.status_code == 200
    # If this doesn't raise, response is valid JSON
    data = response.json()
    # Re-serialize to confirm no numpy types remain
    json.dumps(data)


def test_all_scenarios_run_successfully() -> None:
    scenarios_resp = client.get("/api/demo-scenarios")
    keys = [item["key"] for item in scenarios_resp.json()["items"]]
    for key in keys:
        resp = client.post("/api/analysis/demo", json={"scenario_key": key})
        assert resp.status_code == 200, f"Scenario {key} failed: {resp.text}"
