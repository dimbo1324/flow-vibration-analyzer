"""Shared fixtures for reporting tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pytest

from iva.core.models.analysis_result import (
    AnalysisResult,
    PhysicsResult,
    RiskAssessment,
    SpectralPeak,
    SpectrumResult,
)
from iva.core.models.enums import PeakInterpretation, RiskLevel, WindowType
from iva.core.models.settings import SpectralSettings


def _make_minimal_analysis_result(
    *,
    include_physics: bool = True,
    include_risk: bool = True,
    with_warnings: bool = True,
) -> AnalysisResult:
    settings = SpectralSettings(window_type=WindowType.HANN)
    peak = SpectralPeak(
        frequency_hz=40.0,
        amplitude=1e-3,
        width_hz_3db=0.5,
        interpretation=PeakInterpretation.VORTEX_SHEDDING,
        confidence=0.9,
    )
    spectrum = SpectrumResult(
        frequencies=np.linspace(0, 200, 512),
        psd_values=np.ones(512) * 1e-4,
        dominant_peak=peak,
        all_peaks=(peak,),
        rms_total=0.012,
        rms_in_band=None,
        rms_trend=np.ones(100) * 0.012,
        applied_settings=settings,
    )

    physics: PhysicsResult | None = None
    if include_physics:
        physics = PhysicsResult(
            reynolds_number=23904.0,
            strouhal_number=0.21,
            calculated_shedding_frequency_hz=35.0,
            velocity_ratio=5.1,
            frequency_ratio=0.875,
            kinematic_viscosity_m2s=1.002e-6,
        )

    risk: RiskAssessment | None = None
    if include_risk and include_physics:
        risk = RiskAssessment(
            risk_level=RiskLevel.WATCH,
            dominant_frequency_deviation=0.125,
            recommendation_text="Наблюдение: частота срыва вихрей близка к собственной частоте.",
            contributing_factors=("frequency_ratio=0.875",),
        )

    warnings = ("Missing fraction above 5%", "Signal short") if with_warnings else ()

    return AnalysisResult(
        session_id=str(uuid.uuid4()),
        completed_at=datetime(2025, 6, 11, 12, 0, 0, tzinfo=UTC),
        source_file_path=Path("/data/example_clean_sine.csv"),
        source_file_md5="abc123def456",
        validated_data=None,
        processed_data=None,
        spectrum=spectrum,
        physics=physics,
        risk=risk,
        validation=None,
        warnings=tuple(warnings),
    )


@pytest.fixture
def minimal_result() -> AnalysisResult:
    """Minimal valid AnalysisResult for reporting tests."""
    return _make_minimal_analysis_result()


@pytest.fixture
def result_no_physics() -> AnalysisResult:
    """AnalysisResult without physics or risk."""
    return _make_minimal_analysis_result(include_physics=False, include_risk=False)
