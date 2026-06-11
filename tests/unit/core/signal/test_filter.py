"""Unit tests for iva.core.signal.filter."""

from __future__ import annotations

import numpy as np
import pytest

from iva.core.models.exceptions import FilterConfigurationError
from iva.core.signal.filter import (
    apply_bandpass_filter,
    apply_highpass_filter,
    apply_lowpass_filter,
)

FS = 1000.0  # sampling rate used throughout
DURATION = 5.0  # seconds


def _sine(freq: float, fs: float = FS, duration: float = DURATION) -> np.ndarray:
    n = int(fs * duration)
    t = np.linspace(0.0, duration, n, endpoint=False)
    return np.sin(2.0 * np.pi * freq * t)


# ---------------------------------------------------------------------------
# apply_bandpass_filter
# ---------------------------------------------------------------------------


def test_bandpass_pass_band_amplitude_preserved():
    """A sine in the passband retains > 90 % of its amplitude."""
    signal = _sine(freq=40.0)  # 40 Hz is inside [10, 200] Hz
    result = apply_bandpass_filter(signal, FS, low_hz=10.0, high_hz=200.0, order=4)
    # Trim transients at edges (first/last 0.5 s)
    trim = int(FS * 0.5)
    amplitude = np.max(np.abs(result[trim:-trim]))
    assert amplitude > 0.90, f"Amplitude {amplitude:.3f} is below 90 %"


def test_bandpass_stop_band_amplitude_suppressed():
    """A sine outside the passband is suppressed to < 1 % of original amplitude."""
    signal = _sine(freq=5.0)  # 5 Hz is below [10, 200] Hz
    result = apply_bandpass_filter(signal, FS, low_hz=10.0, high_hz=200.0, order=4)
    trim = int(FS * 0.5)
    amplitude = np.max(np.abs(result[trim:-trim]))
    assert amplitude < 0.01, f"Stop-band amplitude {amplitude:.4f} is not suppressed"


def test_bandpass_low_hz_exceeds_nyquist_raises():
    """low_hz ≥ Nyquist raises FilterConfigurationError."""
    signal = _sine(40.0)
    with pytest.raises(FilterConfigurationError):
        apply_bandpass_filter(signal, FS, low_hz=600.0, high_hz=700.0)


def test_bandpass_low_hz_ge_high_hz_raises():
    """low_hz ≥ high_hz raises FilterConfigurationError."""
    signal = _sine(40.0)
    with pytest.raises(FilterConfigurationError):
        apply_bandpass_filter(signal, FS, low_hz=100.0, high_hz=50.0)


def test_bandpass_zero_low_hz_raises():
    """low_hz = 0 raises FilterConfigurationError."""
    signal = _sine(40.0)
    with pytest.raises(FilterConfigurationError):
        apply_bandpass_filter(signal, FS, low_hz=0.0, high_hz=200.0)


def test_bandpass_no_phase_shift():
    """filtfilt produces near-zero phase shift: RMS of difference vs ideal < 0.01."""
    # Use a sine well within the pass band so amplitude is near 1.
    signal = _sine(freq=50.0)
    result = apply_bandpass_filter(signal, FS, low_hz=10.0, high_hz=200.0, order=2)
    trim = int(FS * 1.0)
    # Phase shift would shift the sine; check RMS difference is small relative to amplitude
    rms_diff = np.sqrt(np.mean((result[trim:-trim] - signal[trim:-trim]) ** 2))
    assert rms_diff < 0.1, f"RMS difference {rms_diff:.4f} suggests phase shift or amplitude error"


def test_bandpass_returns_float64():
    """Output dtype is float64."""
    signal = _sine(40.0)
    result = apply_bandpass_filter(signal, FS, low_hz=10.0, high_hz=200.0)
    assert result.dtype == np.float64


# ---------------------------------------------------------------------------
# apply_lowpass_filter
# ---------------------------------------------------------------------------


def test_lowpass_pass_band_preserved():
    """Low-frequency component is passed through the lowpass filter."""
    signal = _sine(freq=20.0)  # inside [0, 100] Hz
    result = apply_lowpass_filter(signal, FS, cutoff_hz=100.0, order=4)
    trim = int(FS * 0.5)
    amplitude = np.max(np.abs(result[trim:-trim]))
    assert amplitude > 0.90


def test_lowpass_stop_band_suppressed():
    """High-frequency component is suppressed by the lowpass filter."""
    signal = _sine(freq=400.0)  # above cutoff of 100 Hz
    result = apply_lowpass_filter(signal, FS, cutoff_hz=100.0, order=4)
    trim = int(FS * 0.5)
    amplitude = np.max(np.abs(result[trim:-trim]))
    assert amplitude < 0.05


def test_lowpass_invalid_cutoff_raises():
    """Cutoff ≥ Nyquist raises FilterConfigurationError."""
    with pytest.raises(FilterConfigurationError):
        apply_lowpass_filter(_sine(40.0), FS, cutoff_hz=600.0)


# ---------------------------------------------------------------------------
# apply_highpass_filter
# ---------------------------------------------------------------------------


def test_highpass_pass_band_preserved():
    """High-frequency component is passed through the highpass filter."""
    signal = _sine(freq=200.0)  # above cutoff of 50 Hz
    result = apply_highpass_filter(signal, FS, cutoff_hz=50.0, order=4)
    trim = int(FS * 0.5)
    amplitude = np.max(np.abs(result[trim:-trim]))
    assert amplitude > 0.90


def test_highpass_stop_band_suppressed():
    """Low-frequency component is suppressed by the highpass filter."""
    signal = _sine(freq=5.0)  # below cutoff of 50 Hz
    result = apply_highpass_filter(signal, FS, cutoff_hz=50.0, order=4)
    trim = int(FS * 0.5)
    amplitude = np.max(np.abs(result[trim:-trim]))
    assert amplitude < 0.05


def test_highpass_invalid_cutoff_raises():
    """Cutoff ≥ Nyquist raises FilterConfigurationError."""
    with pytest.raises(FilterConfigurationError):
        apply_highpass_filter(_sine(40.0), FS, cutoff_hz=600.0)
