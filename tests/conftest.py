"""Shared pytest configuration for the Industrial Vibration Analyzer test suite.

This module is imported by pytest before any test module (and therefore before
the infrastructure readers/validators import their module-level loggers).  We
set ``IVA_LOG_DIR`` to a temporary directory here so the suite never writes log
files into the real user Documents folder.  ``app_logger`` honours this
override (see iva/infrastructure/logging/app_logger.py).

``setdefault`` is used so an explicitly provided ``IVA_LOG_DIR`` (e.g. in CI)
is respected.
"""

from __future__ import annotations

import os
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pytest

os.environ.setdefault("IVA_LOG_DIR", str(Path(tempfile.gettempdir()) / "iva_test_logs"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_OPENGL", "software")
os.environ.setdefault("MPLBACKEND", "Agg")

from iva.app.analysis_session import AnalysisSession
from iva.core.models.analysis_result import (
    AnalysisResult,
    PhysicsResult,
    RiskAssessment,
    SpectralPeak,
    SpectrumResult,
    ValidationResult,
)
from iva.core.models.enums import PeakInterpretation, RiskLevel, SignalRole, WindowType
from iva.core.models.settings import AnalysisSettings, PreprocessingSettings, SpectralSettings
from iva.core.models.signal_data import (
    ColumnRoleAssignment,
    ProcessedSignalData,
    ValidatedSignalData,
)


@pytest.fixture
def stage9_result(tmp_path: Path) -> AnalysisResult:
    """Complete, compact result shared by Stage 9 tests."""
    time = np.linspace(0.0, 1.0, 101)
    signal = np.sin(2 * np.pi * 10 * time)
    preprocessing = PreprocessingSettings(apply_bandpass_filter=False)
    spectral = SpectralSettings(window_type=WindowType.HANN, segment_length_samples=64)
    peak = SpectralPeak(
        frequency_hz=10.0,
        amplitude=0.5,
        width_hz_3db=1.0,
        interpretation=PeakInterpretation.VORTEX_SHEDDING,
        confidence=0.95,
    )
    validated = ValidatedSignalData(
        time_array=time,
        signal_array=signal,
        sampling_rate_hz=100.0,
        duration_seconds=1.0,
        sample_count=len(time),
        signal_role=SignalRole.ACCELERATION_X,
        physical_unit="m/s^2",
        missing_fraction=0.0,
        outlier_fraction=0.0,
        warnings=(),
    )
    processed = ProcessedSignalData(
        time_array=time,
        signal_cleaned=signal,
        signal_filtered=signal,
        preprocessing_log=("mean removed",),
        applied_settings=preprocessing,
    )
    spectrum = SpectrumResult(
        frequencies=np.linspace(0.0, 50.0, 51),
        psd_values=np.linspace(0.001, 0.1, 51),
        dominant_peak=peak,
        all_peaks=(peak,),
        rms_total=0.707,
        rms_in_band=0.7,
        rms_trend=np.full(20, 0.707),
        applied_settings=spectral,
    )
    physics = PhysicsResult(10000.0, 0.2, 10.0, 5.0, 1.0, 1e-6)
    risk = RiskAssessment(RiskLevel.WATCH, 0.03, "Review <limits> & inspect", ("near",))
    validation = ValidationResult(
        coordinate_array=np.array([0.0, 0.5, 1.0]),
        experiment_array=np.array([1.0, 2.0, 3.0]),
        cfd_array=np.array([1.0, 2.1, 2.9]),
        rmse=0.08165,
        mae=0.06667,
        mape=3.0,
        pearson_r=0.99,
        is_mape_valid=True,
    )
    return AnalysisResult(
        session_id=str(uuid.uuid4()),
        completed_at=datetime(2026, 6, 11, tzinfo=UTC),
        source_file_path=tmp_path / "source<script>.csv",
        source_file_md5="abc123",
        validated_data=validated,
        processed_data=processed,
        spectrum=spectrum,
        physics=physics,
        risk=risk,
        validation=validation,
        warnings=("warning <unsafe>",),
    )


@pytest.fixture
def stage9_session(stage9_result: AnalysisResult, tmp_path: Path) -> AnalysisSession:
    role = ColumnRoleAssignment(
        time_column="time",
        primary_signal_column="value",
        signal_role=SignalRole.ACCELERATION_X,
        additional_columns={},
        sampling_rate_hz=100.0,
    )
    settings = AnalysisSettings(
        preprocessing=stage9_result.processed_data.applied_settings,  # type: ignore[union-attr]
        spectral=stage9_result.spectrum.applied_settings,  # type: ignore[union-attr]
    )
    return AnalysisSession(
        source_file_path=stage9_result.source_file_path,
        role_assignment=role,
        settings=settings,
        result=stage9_result,
        warnings=list(stage9_result.warnings),
        output_dir=tmp_path / "output",
    )
