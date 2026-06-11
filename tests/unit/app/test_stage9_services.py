"""Application service tests for Stage 9."""

from __future__ import annotations

from pathlib import Path

import pytest

from iva.app.profile_comparison_service import compare_profile_csv_files
from iva.app.report_service import export_report_bundle
from iva.app.session_service import load_saved_session, save_current_session
from iva.core.models.exceptions import ValidationError


def test_report_bundle_exports_required_formats(stage9_result, tmp_path: Path) -> None:
    written = export_report_bundle(stage9_result, tmp_path / "bundle")
    expected = {"pdf", "html", "json_summary", "spectrum_csv", "signal_csv", "physics_csv"}
    assert expected <= set(written)
    assert all(path.exists() and path.stat().st_size > 0 for path in written.values())


def test_session_service_roundtrip(stage9_session, tmp_path: Path) -> None:
    path = save_current_session(stage9_session, tmp_path / "saved")
    loaded = load_saved_session(path)
    assert loaded.result is not None
    assert loaded.result.session_id == stage9_session.result.session_id


def test_profile_comparison_service_reads_expected_columns(tmp_path: Path) -> None:
    experiment = tmp_path / "experiment.csv"
    cfd = tmp_path / "cfd.csv"
    experiment.write_text("coordinate,value\n0,1\n1,2\n2,3\n", encoding="utf-8")
    cfd.write_text("coordinate,value\n0,1\n1,2\n2,3\n", encoding="utf-8")
    result = compare_profile_csv_files(experiment, cfd)
    assert result.rmse == pytest.approx(0.0)
    assert result.mae == pytest.approx(0.0)


def test_profile_comparison_rejects_invalid_columns(tmp_path: Path) -> None:
    experiment = tmp_path / "experiment.csv"
    cfd = tmp_path / "cfd.csv"
    experiment.write_text("x,y\n0,1\n1,2\n", encoding="utf-8")
    cfd.write_text("coordinate,value\n0,1\n1,2\n", encoding="utf-8")
    with pytest.raises(ValidationError, match="coordinate"):
        compare_profile_csv_files(experiment, cfd)


def test_profile_comparison_rejects_bad_numeric_value(tmp_path: Path) -> None:
    experiment = tmp_path / "experiment.csv"
    cfd = tmp_path / "cfd.csv"
    experiment.write_text("coordinate,value\n0,bad\n1,2\n", encoding="utf-8")
    cfd.write_text("coordinate,value\n0,1\n1,2\n", encoding="utf-8")
    with pytest.raises(ValidationError, match="строке 2"):
        compare_profile_csv_files(experiment, cfd)
