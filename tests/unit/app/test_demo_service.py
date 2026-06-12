"""Unit tests for the app-level demo orchestration service."""

from __future__ import annotations

from pathlib import Path

import pytest

from iva.app.demo_service import create_demo_session, run_demo_analysis
from iva.core.models.enums import RiskLevel
from iva.core.models.exceptions import ValidationError


def test_create_demo_session_is_ready_and_writes_runtime_csv(tmp_path: Path) -> None:
    session = create_demo_session("clean_40hz", tmp_path)
    assert session.is_ready_for_analysis()
    assert session.is_demo is True
    assert session.demo_scenario_key == "clean_40hz"
    assert session.source_file_path is not None and session.source_file_path.exists()
    assert session.role_assignment is not None
    assert session.role_assignment.time_column == "time_s"
    assert session.role_assignment.primary_signal_column == "signal"


def test_run_demo_analysis_uses_normal_pipeline(tmp_path: Path) -> None:
    result = run_demo_analysis("clean_40hz", tmp_path)
    assert result.is_demo is True
    assert result.spectrum is not None and result.spectrum.dominant_peak is not None
    assert result.spectrum.dominant_peak.frequency_hz == pytest.approx(40.0, abs=1.0)
    assert "Демонстрационные синтетические данные" in result.warnings


def test_critical_demo_produces_high_risk(tmp_path: Path) -> None:
    result = run_demo_analysis("critical_risk", tmp_path)
    assert result.risk is not None
    assert result.risk.risk_level in (RiskLevel.WATCH, RiskLevel.CRITICAL)


def test_unknown_demo_scenario_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValidationError, match="Неизвестный"):
        create_demo_session("unknown", tmp_path)
