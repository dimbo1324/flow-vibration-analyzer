"""Unit tests for iva.core.signal.outlier_detector."""

from __future__ import annotations

import numpy as np

from iva.core.signal.outlier_detector import detect_outliers, replace_outliers

# ---------------------------------------------------------------------------
# detect_outliers
# ---------------------------------------------------------------------------


def _clean_sine(n: int = 2000, freq: float = 40.0, fs: float = 1000.0) -> np.ndarray:
    t = np.linspace(0.0, (n - 1) / fs, n)
    return np.sin(2.0 * np.pi * freq * t)


def test_detect_outliers_known_spikes():
    """Large injected spikes are detected as outliers."""
    signal = _clean_sine()
    signal[100] = 100.0  # massive spike
    signal[500] = -100.0
    mask = detect_outliers(signal, window_samples=21, threshold_sigma=4.0)
    assert mask[100], "spike at index 100 should be flagged"
    assert mask[500], "spike at index 500 should be flagged"


def test_detect_outliers_clean_signal_no_false_positives():
    """A clean sine wave produces no (or very few) false-positive outliers."""
    signal = _clean_sine(n=2000)
    mask = detect_outliers(signal, window_samples=21, threshold_sigma=4.0)
    # At most 0.1 % false-positive rate on a clean signal
    assert np.sum(mask) / len(mask) < 0.001


def test_detect_outliers_zero_amplitude_no_division_error():
    """A constant (zero-amplitude) signal does not cause division-by-zero."""
    signal = np.zeros(500)
    mask = detect_outliers(signal, window_samples=21, threshold_sigma=4.0)
    # All-zero signal has no outliers
    assert np.sum(mask) == 0


def test_detect_outliers_nan_not_flagged():
    """NaN samples are never flagged as outliers."""
    signal = np.array([1.0, np.nan, 1.0, 100.0, 1.0] * 40, dtype=float)
    mask = detect_outliers(signal, window_samples=21, threshold_sigma=4.0)
    # NaN positions must not be outliers
    nan_positions = np.where(np.isnan(signal))[0]
    assert not np.any(mask[nan_positions])


def test_detect_outliers_returns_bool_array():
    """Result dtype is bool and shape matches input."""
    signal = _clean_sine()
    mask = detect_outliers(signal)
    assert mask.dtype == bool
    assert mask.shape == signal.shape


def test_detect_outliers_signal_shorter_than_window():
    """Signal shorter than window_samples returns all-False mask (no crash)."""
    signal = np.array([1.0, 2.0, 3.0])
    mask = detect_outliers(signal, window_samples=21)
    assert mask.shape == (3,)
    assert not np.any(mask)


# ---------------------------------------------------------------------------
# replace_outliers
# ---------------------------------------------------------------------------


def test_replace_outliers_no_nans_after_replacement():
    """After replacement, no NaN remains in positions that were outliers."""
    signal = _clean_sine()
    signal[300] = 500.0
    mask = detect_outliers(signal, window_samples=21, threshold_sigma=4.0)
    result = replace_outliers(signal, mask)
    assert not np.any(np.isnan(result[mask]))


def test_replace_outliers_no_outliers_unchanged():
    """If the mask is all-False, the returned array equals the input."""
    signal = _clean_sine()
    mask = np.zeros(len(signal), dtype=bool)
    result = replace_outliers(signal, mask)
    np.testing.assert_array_equal(result, signal)


def test_replace_outliers_does_not_modify_input():
    """replace_outliers returns a copy; the original signal is unchanged."""
    signal = _clean_sine()
    signal[200] = 999.0
    original = signal.copy()
    mask = detect_outliers(signal, window_samples=21, threshold_sigma=4.0)
    replace_outliers(signal, mask)
    np.testing.assert_array_equal(signal, original)


def test_replace_outliers_interpolated_value_in_range():
    """Replaced spike value is within the amplitude range of a clean sine."""
    signal = _clean_sine()
    signal[500] = 300.0
    mask = detect_outliers(signal, window_samples=21, threshold_sigma=4.0)
    result = replace_outliers(signal, mask)
    # Sine amplitude is 1.0; interpolated value should be within [-1.5, 1.5]
    assert abs(result[500]) < 1.5
