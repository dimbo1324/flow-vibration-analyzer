"""Unit tests for iva.infrastructure.validators.data_quality_checker."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from iva.core.models.enums import SignalRole
from iva.core.models.exceptions import (
    EmptySignalError,
    InsufficientDataError,
    NonMonotonicTimeAxisError,
    ValidationError,
)
from iva.core.models.signal_data import ColumnRoleAssignment, RawFileData
from iva.infrastructure.validators.data_quality_checker import check_data_quality

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _make_raw(df: pd.DataFrame, fmt: str = "csv") -> RawFileData:
    """Wrap a DataFrame in a minimal RawFileData."""
    return RawFileData(
        file_path=Path("test_file.csv"),
        file_format=fmt,
        column_names=tuple(str(c) for c in df.columns),
        column_dtypes={c: str(df[c].dtype) for c in df.columns},
        row_count=len(df),
        file_size_bytes=0,
        data=df,
        read_timestamp=datetime.now(),
    )


def _make_assignment(
    *,
    time_col: str = "time_s",
    signal_col: str = "signal",
    role: SignalRole = SignalRole.ACCELERATION_X,
    rate: float = 0.0,
    factor: float | None = None,
) -> ColumnRoleAssignment:
    return ColumnRoleAssignment(
        time_column=time_col,
        primary_signal_column=signal_col,
        signal_role=role,
        additional_columns={},
        sampling_rate_hz=rate,
        sensor_conversion_factor=factor,
    )


def _sine_df(duration: float = 10.0, fs: float = 1000.0) -> pd.DataFrame:
    n = int(duration * fs)
    t = np.linspace(0.0, duration, n, endpoint=False)
    s = np.sin(2.0 * np.pi * 40.0 * t)
    return pd.DataFrame({"time_s": t, "signal": s})


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------


def test_valid_signal_passes():
    """A clean, 10-second 40 Hz sine passes validation with no warnings."""
    df = _sine_df()
    result = check_data_quality(_make_raw(df), _make_assignment())
    assert result.sample_count == len(df)
    assert result.duration_seconds == pytest.approx(10.0, abs=0.01)
    assert result.warnings == ()
    assert result.missing_fraction == pytest.approx(0.0)
    assert result.outlier_fraction == pytest.approx(0.0, abs=0.01)


def test_missing_column_raises_validation_error():
    """ValidationError is raised when the required signal column is absent."""
    df = pd.DataFrame({"time_s": np.linspace(0, 10, 10000), "other": np.zeros(10000)})
    with pytest.raises(ValidationError):
        check_data_quality(_make_raw(df), _make_assignment(signal_col="signal"))


def test_non_monotonic_time_raises():
    """NonMonotonicTimeAxisError is raised when time is not strictly increasing."""
    n = 5001
    t_full = np.linspace(0.0, 6.0, n)
    t_full[2] = t_full[1] - 0.0001  # inject non-monotonic step
    s = np.sin(t_full)
    df = pd.DataFrame({"time_s": t_full, "signal": s})
    with pytest.raises(NonMonotonicTimeAxisError):
        check_data_quality(_make_raw(df), _make_assignment())


def test_all_zero_signal_raises_empty_signal_error():
    """EmptySignalError is raised when every sample is 0."""
    df = pd.DataFrame({"time_s": np.linspace(0.0, 10.0, 10000), "signal": np.zeros(10000)})
    with pytest.raises(EmptySignalError):
        check_data_quality(_make_raw(df), _make_assignment())


def test_duration_too_short_raises():
    """InsufficientDataError is raised when duration is less than 5 seconds."""
    df = _sine_df(duration=3.0)
    with pytest.raises(InsufficientDataError):
        check_data_quality(_make_raw(df), _make_assignment())


def test_missing_fraction_warning(caplog):
    """A >30% NaN fraction produces a warning in the result's warnings tuple."""
    import logging

    df = _sine_df()
    df_copy = df.copy()
    idx = np.random.default_rng(0).choice(
        len(df_copy), size=int(len(df_copy) * 0.35), replace=False
    )
    df_copy.loc[idx, "signal"] = np.nan

    with caplog.at_level(logging.WARNING):
        result = check_data_quality(_make_raw(df_copy), _make_assignment())

    assert result.missing_fraction > 0.30
    assert len(result.warnings) > 0


def test_sensor_conversion_factor_applied():
    """When sensor_conversion_factor is set, signal values are scaled."""
    df = _sine_df()
    result = check_data_quality(_make_raw(df), _make_assignment(factor=2.0))
    # Original amplitude is 1.0; after factor=2 it should be ≈2.0
    assert np.nanmax(np.abs(result.signal_array)) == pytest.approx(2.0, abs=0.01)


def test_physical_unit_mapped_correctly():
    """The physical_unit field reflects the signal role."""
    df = _sine_df()
    result = check_data_quality(_make_raw(df), _make_assignment(role=SignalRole.PRESSURE))
    assert result.physical_unit == "Pa"


def test_outlier_fraction_detected():
    """Signals with large spikes produce a non-zero outlier_fraction."""
    df = _sine_df()
    df_copy = df.copy()
    # Inject a clear outlier (>>4σ)
    df_copy.loc[500, "signal"] = 1000.0
    result = check_data_quality(_make_raw(df_copy), _make_assignment())
    assert result.outlier_fraction > 0.0
