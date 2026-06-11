"""Unit tests for iva.core.physics.lock_in_risk."""

from __future__ import annotations

import numpy as np
import pytest

from iva.core.models.analysis_result import (
    PhysicsResult,
    RiskAssessment,
    SpectralPeak,
    SpectrumResult,
)
from iva.core.models.enums import PeakInterpretation, RiskLevel, WindowType
from iva.core.models.settings import SpectralSettings
from iva.core.physics.lock_in_risk import assess_risk

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_physics(
    fs: float,
    fn: float | None,
) -> PhysicsResult:
    """Build a minimal PhysicsResult with the given shedding frequency and fn."""
    frequency_ratio = (fs / fn) if fn is not None else None
    velocity_ratio = 1.0 if fn is not None else None  # arbitrary non-None value
    return PhysicsResult(
        reynolds_number=20000.0,
        strouhal_number=0.20,
        calculated_shedding_frequency_hz=fs,
        velocity_ratio=velocity_ratio,
        frequency_ratio=frequency_ratio,
        kinematic_viscosity_m2s=1.0e-6,
    )


def _make_spectrum(dominant_amplitude: float = 1e3) -> SpectrumResult:
    """Build a minimal SpectrumResult with a dominant peak of given amplitude."""
    freqs = np.linspace(0, 200, 1000)
    # PSD median ≈ 1.0, dominant peak well above threshold
    psd = np.ones(1000, dtype=np.float64)
    settings = SpectralSettings(window_type=WindowType.HANN)
    dominant = SpectralPeak(
        frequency_hz=35.0,
        amplitude=dominant_amplitude,
        width_hz_3db=0.5,
        interpretation=PeakInterpretation.VORTEX_SHEDDING,
        confidence=0.9,
    )
    return SpectrumResult(
        frequencies=freqs,
        psd_values=psd,
        dominant_peak=dominant,
        all_peaks=(dominant,),
        rms_total=1.0,
        rms_in_band=None,
        rms_trend=np.ones(100),
        applied_settings=settings,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAssessRisk:

    @pytest.mark.parametrize(
        ("fs", "fn"),
        [(60.0, 40.0), (48.0, 40.0), (42.0, 40.0)],
    )
    def test_all_risk_recommendations_are_russian(self, fs: float, fn: float) -> None:
        result = assess_risk(_make_physics(fs=fs, fn=fn), _make_spectrum(1e6))
        assert any("Ѐ" <= ch <= "ӿ" for ch in result.recommendation_text)
        assert "risk" not in result.recommendation_text.lower()

    def test_critical_when_deviation_small(self) -> None:
        """deviation ≤ 0.10 → CRITICAL (with large amplitude)."""
        # fs very close to fn: frequency_ratio = 1.05 → deviation = 0.05
        physics = _make_physics(fs=42.0, fn=40.0)  # ratio=1.05, dev=0.05
        spectrum = _make_spectrum(dominant_amplitude=1e6)  # large → no downgrade
        result = assess_risk(physics, spectrum)
        assert result.risk_level == RiskLevel.CRITICAL

    def test_watch_when_deviation_medium(self) -> None:
        """0.10 < deviation ≤ 0.30 → WATCH (with large amplitude)."""
        # fs/fn = 1.20 → deviation = 0.20
        physics = _make_physics(fs=48.0, fn=40.0)
        spectrum = _make_spectrum(dominant_amplitude=1e6)
        result = assess_risk(physics, spectrum)
        assert result.risk_level == RiskLevel.WATCH

    def test_safe_when_deviation_large(self) -> None:
        """deviation > 0.30 → SAFE."""
        # fs/fn = 1.5 → deviation = 0.50
        physics = _make_physics(fs=60.0, fn=40.0)
        spectrum = _make_spectrum(dominant_amplitude=1e6)
        result = assess_risk(physics, spectrum)
        assert result.risk_level == RiskLevel.SAFE

    def test_safe_when_fn_not_set(self) -> None:
        """frequency_ratio is None → SAFE with fn-not-set message."""
        physics = _make_physics(fs=35.0, fn=None)
        spectrum = _make_spectrum()
        result = assess_risk(physics, spectrum)
        assert result.risk_level == RiskLevel.SAFE
        assert (
            "не задана" in result.recommendation_text.lower()
            or "не задан" in result.recommendation_text.lower()
        )

    def test_fn_not_set_recommendation_is_russian(self) -> None:
        physics = _make_physics(fs=35.0, fn=None)
        spectrum = _make_spectrum()
        result = assess_risk(physics, spectrum)
        # Russian text contains Cyrillic characters
        assert any("Ѐ" <= ch <= "ӿ" for ch in result.recommendation_text)

    def test_recommendation_text_non_empty(self) -> None:
        physics = _make_physics(fs=42.0, fn=40.0)
        spectrum = _make_spectrum(dominant_amplitude=1e6)
        result = assess_risk(physics, spectrum)
        assert len(result.recommendation_text) > 0

    def test_contributing_factors_non_empty(self) -> None:
        physics = _make_physics(fs=42.0, fn=40.0)
        spectrum = _make_spectrum(dominant_amplitude=1e6)
        result = assess_risk(physics, spectrum)
        assert len(result.contributing_factors) > 0

    def test_contributing_factors_use_russian_risk_labels(self) -> None:
        physics = _make_physics(fs=42.0, fn=40.0)
        spectrum = _make_spectrum(dominant_amplitude=1e6)
        result = assess_risk(physics, spectrum)
        factors = " ".join(result.contributing_factors)
        assert "КРИТИЧЕСКИЙ" in factors
        assert "CRITICAL" not in factors

    def test_amplitude_downgrade_critical_to_watch(self) -> None:
        """Small dominant peak amplitude should downgrade CRITICAL → WATCH."""
        # deviation = 0.05 → normally CRITICAL
        physics = _make_physics(fs=42.0, fn=40.0)
        # dominant amplitude = 0.5, median psd = 1.0 → 0.5 < 2.0 * 1.0 → downgrade
        spectrum = _make_spectrum(dominant_amplitude=0.5)
        result = assess_risk(physics, spectrum)
        # Should be downgraded to WATCH
        assert result.risk_level == RiskLevel.WATCH

    def test_amplitude_downgrade_watch_to_safe(self) -> None:
        """Small dominant peak amplitude should downgrade WATCH → SAFE."""
        # deviation = 0.20 → normally WATCH
        physics = _make_physics(fs=48.0, fn=40.0)
        spectrum = _make_spectrum(dominant_amplitude=0.5)
        result = assess_risk(physics, spectrum)
        assert result.risk_level == RiskLevel.SAFE

    def test_returns_risk_assessment(self) -> None:
        physics = _make_physics(fs=35.0, fn=40.0)
        spectrum = _make_spectrum()
        result = assess_risk(physics, spectrum)
        assert isinstance(result, RiskAssessment)

    def test_dominant_frequency_deviation_stored(self) -> None:
        fn = 40.0
        fs = 44.0  # ratio=1.1, deviation=0.1 exactly (boundary: WATCH)
        physics = _make_physics(fs=fs, fn=fn)
        spectrum = _make_spectrum(dominant_amplitude=1e6)
        result = assess_risk(physics, spectrum)
        expected_dev = abs(fs / fn - 1.0)
        assert abs(result.dominant_frequency_deviation - expected_dev) < 1e-9
