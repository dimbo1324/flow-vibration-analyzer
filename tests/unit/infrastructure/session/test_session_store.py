"""Safe ``.vibproj`` persistence tests."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from iva.core.models.exceptions import ValidationError
from iva.infrastructure.session import (
    VIBPROJ_SCHEMA_VERSION,
    analysis_result_from_dict,
    analysis_result_to_dict,
    load_project,
    save_project,
)


def test_result_serializer_roundtrip_restores_chart_data(stage9_result) -> None:
    restored = analysis_result_from_dict(analysis_result_to_dict(stage9_result))
    assert restored.session_id == stage9_result.session_id
    assert restored.processed_data is not None
    assert restored.spectrum is not None
    assert restored.validation is not None
    np.testing.assert_allclose(restored.spectrum.frequencies, stage9_result.spectrum.frequencies)


def test_project_roundtrip_preserves_settings_and_roles(stage9_session, tmp_path: Path) -> None:
    path = save_project(stage9_session, tmp_path / "analysis")
    loaded = load_project(path)
    assert path.suffix == ".vibproj"
    assert loaded.settings == stage9_session.settings
    assert loaded.role_assignment == stage9_session.role_assignment
    assert loaded.result is not None
    assert loaded.result.session_id == stage9_session.result.session_id


@pytest.mark.parametrize("content", ["not json", "[]", "{}"])
def test_invalid_project_is_rejected(tmp_path: Path, content: str) -> None:
    path = tmp_path / "broken.vibproj"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ValidationError):
        load_project(path)


def test_unsupported_schema_is_rejected(stage9_session, tmp_path: Path) -> None:
    path = save_project(stage9_session, tmp_path / "analysis.vibproj")
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["_vibproj_version"] = "99.0"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValidationError, match="не поддерживается"):
        load_project(path)


def test_schema_version_is_public() -> None:
    assert VIBPROJ_SCHEMA_VERSION == "1.0"


def test_session_implementation_does_not_use_pickle() -> None:
    root = Path(__file__).parents[4] / "iva" / "infrastructure" / "session"
    source = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.py"))
    assert "pickle" not in source.lower()
