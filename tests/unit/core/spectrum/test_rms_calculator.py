"""Unit tests for iva.core.spectrum.rms_calculator."""

from __future__ import annotations

import numpy as np
import pytest

from iva.core.spectrum.rms_calculator import (
    calculate_band_rms,
    calculate_rms_trend,
    calculate_total_rms,
)

FS = 1000.0


def _sine(amplitude: float = 1.0, freq: float = 40.0, duration: float = 5.0) -> np.ndarray:
    n = int(FS * duration)
    t = np.linspace(0.0, duration, n, endpoint=False)
    return amplitude * np.sin(2.0 * np.pi * freq * t)


# ---------------------------------------------------------------------------
# calculate_total_rms
# ---------------------------------------------------------------------------


def test_total_rms_sine_analytical():
    """RMS of a sine with amplitude A equals A / sqrt(2)."""
    amplitude = 3.0
    signal = _sine(amplitude=amplitude, duration=10.0)
    rms = calculate_total_rms(signal)
    expected = amplitude / np.sqrt(2.0)
    assert abs(rms - expected) / expected < 0.001, f"rms={rms:.6f}, expected={expected:.6f}"


def test_total_rms_constant_signal():
    """RMS of a constant signal equals its absolute value."""
    signal = np.full(1000, 4.5)
    assert calculate_total_rms(signal) == pytest.approx(4.5)


def test_total_rms_zero_signal():
    """RMS of a zero signal is zero."""
    assert calculate_total_rms(np.zeros(500)) == pytest.approx(0.0)


def test_total_rms_returns_float():
    """Result is a Python float."""
    result = calculate_total_rms(np.ones(100))
    assert isinstance(result, float)


# ---------------------------------------------------------------------------
# calculate_band_rms
# ---------------------------------------------------------------------------


def test_band_rms_includes_dominant_peak():
    """Band RMS over the dominant peak frequency is > 0."""
    from iva.core.models.settings import SpectralSettings
    from iva.core.spectrum.psd_calculator import calculate_psd

    signal = _sine(amplitude=1.0, freq=40.0, duration=10.0)
    settings = SpectralSettings(segment_length_samples=1024)
    freqs, psd = calculate_psd(signal, FS, settings)
    band_rms = calculate_band_rms(freqs, psd, low_hz=35.0, high_hz=45.0)
    assert band_rms > 0.0


def test_band_rms_empty_band_returns_zero():
    """Band with no PSD points returns 0.0."""
    freqs = np.linspace(0.0, 500.0, 513)
    psd = np.ones_like(freqs)
    # Band completely above the frequency array range
    band_rms = calculate_band_rms(freqs, psd, low_hz=600.0, high_hz=700.0)
    assert band_rms == pytest.approx(0.0)


def test_band_rms_returns_float():
    """Result is a Python float."""
    freqs = np.linspace(0.0, 500.0, 513)
    psd = np.ones_like(freqs)
    result = calculate_band_rms(freqs, psd, 10.0, 100.0)
    assert isinstance(result, float)


# ---------------------------------------------------------------------------
# calculate_rms_trend
# ---------------------------------------------------------------------------


def test_rms_trend_correct_length():
    """Output trend has same length as input signal."""
    signal = _sine(duration=5.0)
    trend = calculate_rms_trend(signal, FS, window_seconds=1.0)
    assert len(trend) == len(signal)


def test_rms_trend_constant_signal():
    """RMS trend of a constant signal equals that constant (after window fills)."""
    value = 3.0
    signal = np.full(5000, value)
    trend = calculate_rms_trend(signal, FS, window_seconds=0.5)
    # After the window fills (trim first window), all values should equal 3.0
    window_samples = int(0.5 * FS)
    np.testing.assert_allclose(trend[window_samples:], value, rtol=1e-6)


def test_rms_trend_returns_float64():
    """Output dtype is float64."""
    signal = _sine(duration=2.0)
    trend = calculate_rms_trend(signal, FS, window_seconds=0.1)
    assert trend.dtype == np.float64


def test_rms_trend_non_negative():
    """RMS trend is always non-negative."""
    signal = _sine(duration=5.0)
    trend = calculate_rms_trend(signal, FS, window_seconds=1.0)
    assert np.all(trend >= 0.0)
