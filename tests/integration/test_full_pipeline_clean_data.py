"""Integration test: full pipeline on a clean synthetic 40 Hz signal.

Verifies end-to-end pipeline from session creation through AnalysisResult,
asserting that the dominant spectral peak is in the expected range.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from iva.app.analysis_session import AnalysisSession
from iva.app.workflow_coordinator import run_pipeline
from iva.core.models.enums import SignalRole
from iva.core.models.settings import AnalysisSettings, PreprocessingSettings, SpectralSettings
from iva.core.models.signal_data import ColumnRoleAssignment


def _write_sine_csv(path: Path, freq_hz: float, fs: float, duration_s: float) -> None:
    """Write a clean single-frequency sinusoid to *path*.

    Uses ``endpoint=True`` so the last sample is exactly at ``duration_s``
    and the recorded duration is >= 5 s (required by the data quality checker).
    """
    n = int(fs * duration_s) + 1  # include endpoint
    t = np.linspace(0, duration_s, n, endpoint=True)
    signal = np.sin(2 * np.pi * freq_hz * t)
    with open(path, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["time_s", "signal"])
        for ti, si in zip(t, signal, strict=True):
            writer.writerow([ti, si])


def _make_session(
    csv_file: Path,
    fs: float = 1000.0,
    apply_filter: bool = False,
) -> AnalysisSession:
    """Build a minimal session pointing at *csv_file*."""
    preprocessing = PreprocessingSettings(
        remove_mean=True,
        remove_outliers=False,
        fill_gaps=False,
        apply_bandpass_filter=apply_filter,
        filter_low_hz=5.0,
        filter_high_hz=450.0,
    )
    spectral = SpectralSettings(
        segment_length_samples=1024,
        overlap_fraction=0.5,
        peak_detection_threshold_db=10.0,
        peak_min_width_hz=0.1,
    )
    settings = AnalysisSettings(preprocessing=preprocessing, spectral=spectral)
    role_assignment = ColumnRoleAssignment(
        time_column="time_s",
        primary_signal_column="signal",
        signal_role=SignalRole.ACCELERATION_X,
        additional_columns={},
        sampling_rate_hz=fs,
        sensor_conversion_factor=None,
    )
    return AnalysisSession(
        source_file_path=csv_file,
        role_assignment=role_assignment,
        settings=settings,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_full_pipeline_clean_40hz(tmp_path: Path) -> None:
    """Clean 40 Hz sine at 1000 Hz → dominant peak between 39 and 41 Hz."""
    csv_file = tmp_path / "test_40hz.csv"
    _write_sine_csv(csv_file, freq_hz=40.0, fs=1000.0, duration_s=6.0)

    session = _make_session(csv_file, fs=1000.0)
    result = run_pipeline(session)

    assert result is not None
    assert result.spectrum is not None
    assert result.spectrum.dominant_peak is not None, "No dominant peak found"
    freq = result.spectrum.dominant_peak.frequency_hz
    assert 39.0 <= freq <= 41.0, f"Dominant peak {freq:.2f} Hz outside expected [39, 41] Hz"


def test_full_pipeline_result_stored_in_session(tmp_path: Path) -> None:
    """Result is stored in session.result after pipeline completes."""
    csv_file = tmp_path / "test_store.csv"
    _write_sine_csv(csv_file, freq_hz=50.0, fs=1000.0, duration_s=6.0)

    session = _make_session(csv_file, fs=1000.0)
    result = run_pipeline(session)

    assert session.result is result


def test_full_pipeline_session_id_is_uuid(tmp_path: Path) -> None:
    """session_id is a valid UUID string."""
    import re

    csv_file = tmp_path / "test_uuid.csv"
    _write_sine_csv(csv_file, freq_hz=30.0, fs=1000.0, duration_s=6.0)

    session = _make_session(csv_file, fs=1000.0)
    result = run_pipeline(session)

    uuid_pattern = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
    assert uuid_pattern.match(result.session_id), f"Bad UUID: {result.session_id}"


def test_full_pipeline_md5_is_hex(tmp_path: Path) -> None:
    """source_file_md5 is a non-empty hex string."""
    csv_file = tmp_path / "test_md5.csv"
    _write_sine_csv(csv_file, freq_hz=20.0, fs=1000.0, duration_s=6.0)

    session = _make_session(csv_file, fs=1000.0)
    result = run_pipeline(session)

    assert len(result.source_file_md5) == 32
    int(result.source_file_md5, 16)  # raises ValueError if not hex


def test_full_pipeline_validated_data_populated(tmp_path: Path) -> None:
    """validated_data and processed_data are populated in the result."""
    csv_file = tmp_path / "test_data.csv"
    _write_sine_csv(csv_file, freq_hz=40.0, fs=1000.0, duration_s=6.0)

    session = _make_session(csv_file, fs=1000.0)
    result = run_pipeline(session)

    assert result.validated_data is not None
    assert result.processed_data is not None
    assert result.validated_data.sample_count > 0


def test_full_pipeline_no_physics_when_not_configured(tmp_path: Path) -> None:
    """physics is None when flow_parameters is not set."""
    csv_file = tmp_path / "test_no_physics.csv"
    _write_sine_csv(csv_file, freq_hz=40.0, fs=1000.0, duration_s=6.0)

    session = _make_session(csv_file, fs=1000.0)
    assert session.settings.flow_parameters is None
    result = run_pipeline(session)

    assert result.physics is None
    assert result.risk is None
