"""Unit tests for iva.core.spectrum.psd_calculator."""

from __future__ import annotations

import numpy as np
import pytest

from iva.core.models.exceptions import InsufficientDataError
from iva.core.models.settings import SpectralSettings
from iva.core.spectrum.psd_calculator import calculate_psd

FS = 1000.0
SETTINGS = SpectralSettings(segment_length_samples=1024, overlap_fraction=0.5)


def _sine(freq: float, duration: float = 5.0, fs: float = FS, amplitude: float = 1.0) -> np.ndarray:
    n = int(fs * duration)
    t = np.linspace(0.0, duration, n, endpoint=False)
    return amplitude * np.sin(2.0 * np.pi * freq * t)


def test_psd_dominant_peak_40hz():
    """A 40 Hz sine produces a dominant PSD peak within 39–41 Hz."""
    signal = _sine(freq=40.0, duration=10.0)
    freqs, psd = calculate_psd(signal, FS, SETTINGS)
    dominant_idx = int(np.argmax(psd))
    dominant_freq = float(freqs[dominant_idx])
    assert (
        39.0 <= dominant_freq <= 41.0
    ), f"Dominant peak at {dominant_freq:.2f} Hz, expected 39–41 Hz"


def test_psd_frequency_resolution():
    """Frequency resolution equals fs / nperseg."""
    signal = _sine(40.0, duration=10.0)
    freqs, _ = calculate_psd(signal, FS, SETTINGS)
    expected_df = FS / SETTINGS.segment_length_samples
    actual_df = float(freqs[1] - freqs[0])
    assert abs(actual_df - expected_df) < 1e-6, f"df={actual_df:.6f}, expected {expected_df:.6f}"


def test_psd_returns_float64():
    """Both output arrays are float64."""
    signal = _sine(40.0, duration=5.0)
    freqs, psd = calculate_psd(signal, FS, SETTINGS)
    assert freqs.dtype == np.float64
    assert psd.dtype == np.float64


def test_psd_signal_shorter_than_nperseg_raises():
    """Signal shorter than nperseg raises InsufficientDataError."""
    short_signal = np.ones(100)
    with pytest.raises(InsufficientDataError):
        calculate_psd(short_signal, FS, SETTINGS)


def test_psd_non_negative():
    """PSD values are all non-negative."""
    signal = _sine(40.0, duration=5.0)
    _, psd = calculate_psd(signal, FS, SETTINGS)
    assert np.all(psd >= 0.0)


def test_psd_frequencies_start_at_zero():
    """First frequency bin is 0 Hz."""
    signal = _sine(40.0, duration=5.0)
    freqs, _ = calculate_psd(signal, FS, SETTINGS)
    assert freqs[0] == pytest.approx(0.0)


def test_psd_highest_frequency_equals_nyquist():
    """Last frequency bin equals Nyquist frequency."""
    signal = _sine(40.0, duration=5.0)
    freqs, _ = calculate_psd(signal, FS, SETTINGS)
    assert freqs[-1] == pytest.approx(FS / 2.0)
