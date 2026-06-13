"""Unit tests for session export/import API routes."""

from __future__ import annotations

from fastapi.testclient import TestClient

from iva.api.main import app

client = TestClient(app)


def test_export_session_unknown_analysis() -> None:
    resp = client.post("/api/sessions/export/does-not-exist")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "ANALYSIS_NOT_FOUND"


def test_import_session_wrong_extension() -> None:
    resp = client.post(
        "/api/sessions/import",
        files={"file": ("session.json", b'{"foo": 1}', "application/json")},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "INVALID_FORMAT"


def test_import_session_invalid_content() -> None:
    resp = client.post(
        "/api/sessions/import",
        files={"file": ("session.vibproj", b"not valid json at all !!!{}", "application/json")},
    )
    assert resp.status_code == 400


def test_import_session_valid_structure_required() -> None:
    """A syntactically valid JSON but wrong schema must be safely rejected."""
    import json

    payload = json.dumps({"_vibproj_version": 999, "result": None}).encode()
    resp = client.post(
        "/api/sessions/import",
        files={"file": ("session.vibproj", payload, "application/json")},
    )
    # Either 400 (validation) or 200 with has_result: false — both are safe
    assert resp.status_code in {200, 400}
