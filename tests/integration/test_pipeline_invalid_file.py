"""Integration test: pipeline behaviour with invalid or missing input files."""

from __future__ import annotations

from pathlib import Path

import pytest

from iva.app.analysis_session import AnalysisSession
from iva.app.workflow_coordinator import run_pipeline
from iva.core.models.enums import SignalRole
from iva.core.models.exceptions import IVAError, IVAFileNotFoundError
from iva.core.models.settings import AnalysisSettings
from iva.core.models.signal_data import ColumnRoleAssignment


def _make_session(file_path: Path) -> AnalysisSession:
    role_assignment = ColumnRoleAssignment(
        time_column="time_s",
        primary_signal_column="signal",
        signal_role=SignalRole.ACCELERATION_X,
        additional_columns={},
        sampling_rate_hz=1000.0,
        sensor_conversion_factor=None,
    )
    return AnalysisSession(
        source_file_path=file_path,
        role_assignment=role_assignment,
        settings=AnalysisSettings(),
    )


def test_pipeline_missing_file_raises_iva_error(tmp_path: Path) -> None:
    """A non-existent source file raises an IVAError subclass (not a raw Python error)."""
    missing = tmp_path / "does_not_exist.csv"
    session = _make_session(missing)

    with pytest.raises(IVAError):
        run_pipeline(session)


def test_pipeline_missing_file_raises_file_not_found(tmp_path: Path) -> None:
    """Specifically raises IVAFileNotFoundError for a missing file."""
    missing = tmp_path / "nonexistent_signal.csv"
    session = _make_session(missing)

    with pytest.raises(IVAFileNotFoundError):
        run_pipeline(session)


def test_pipeline_not_ready_raises_processing_error() -> None:
    """Running pipeline on an incomplete session raises ProcessingError."""
    from iva.core.models.exceptions import ProcessingError

    session = AnalysisSession()  # no file, no role assignment
    with pytest.raises(ProcessingError):
        run_pipeline(session)
