"""Unit tests for iva.core.signal.preprocessor."""

from __future__ import annotations

import numpy as np

from iva.core.signal.preprocessor import fill_gaps, remove_mean

# ---------------------------------------------------------------------------
# remove_mean
# ---------------------------------------------------------------------------


def test_remove_mean_zero_mean():
    """After remove_mean the mean is numerically zero."""
    rng = np.random.default_rng(0)
    signal = rng.normal(loc=3.7, scale=1.0, size=1000)
    result = remove_mean(signal)
    assert abs(np.mean(result)) < 1e-10


def test_remove_mean_with_offset():
    """A constant offset of 5 is removed exactly."""
    signal = np.ones(500) * 5.0
    result = remove_mean(signal)
    assert np.allclose(result, 0.0)


def test_remove_mean_does_not_modify_input():
    """remove_mean returns a new array; the input is unchanged."""
    signal = np.array([1.0, 2.0, 3.0])
    original_copy = signal.copy()
    remove_mean(signal)
    np.testing.assert_array_equal(signal, original_copy)


def test_remove_mean_ignores_nan():
    """NaN values do not corrupt the mean calculation."""
    signal = np.array([1.0, 2.0, np.nan, 3.0, 4.0])
    result = remove_mean(signal)
    # mean of finite values = 2.5
    assert abs(result[0] - (1.0 - 2.5)) < 1e-12
    assert np.isnan(result[2])


# ---------------------------------------------------------------------------
# fill_gaps
# ---------------------------------------------------------------------------


def _make_time(n: int, fs: float = 1000.0) -> np.ndarray:
    return np.linspace(0.0, (n - 1) / fs, n)


def test_fill_gaps_short_gap_interpolated():
    """Gaps shorter than max_gap_seconds are linearly interpolated."""
    n = 100
    fs = 1000.0
    time = _make_time(n, fs)
    signal = np.ones(n) * 2.0
    # Insert a 3-sample gap at indices 40–42 (3 ms < max_gap_seconds=10 ms)
    signal[40:43] = np.nan
    result = fill_gaps(signal, time, max_gap_seconds=0.01, sampling_rate_hz=fs)
    # No NaN should remain
    assert not np.any(np.isnan(result))
    # Values in the gap should be close to 2.0 (interpolated from constant)
    np.testing.assert_allclose(result[40:43], 2.0, atol=1e-10)


def test_fill_gaps_long_gap_zeroed():
    """Gaps longer than max_gap_seconds are replaced with zeros."""
    n = 200
    fs = 1000.0
    time = _make_time(n, fs)
    signal = np.ones(n) * 5.0
    # 50-sample gap = 50 ms >> max_gap_seconds=5 ms
    signal[80:130] = np.nan
    result = fill_gaps(signal, time, max_gap_seconds=0.005, sampling_rate_hz=fs)
    assert not np.any(np.isnan(result))
    np.testing.assert_allclose(result[80:130], 0.0, atol=1e-10)


def test_fill_gaps_no_nan_unchanged():
    """Signal with no NaN is returned unchanged."""
    signal = np.sin(np.linspace(0, 2 * np.pi, 500))
    time = _make_time(500)
    result = fill_gaps(signal, time, max_gap_seconds=0.01, sampling_rate_hz=1000.0)
    np.testing.assert_array_equal(result, signal)


def test_fill_gaps_edge_gap_zeroed():
    """Gaps at the start or end of the signal are filled with zeros."""
    n = 100
    fs = 1000.0
    time = _make_time(n, fs)
    signal = np.ones(n)
    signal[:5] = np.nan  # leading gap
    signal[-5:] = np.nan  # trailing gap
    result = fill_gaps(signal, time, max_gap_seconds=0.5, sampling_rate_hz=fs)
    assert not np.any(np.isnan(result))
    np.testing.assert_allclose(result[:5], 0.0, atol=1e-10)
    np.testing.assert_allclose(result[-5:], 0.0, atol=1e-10)


def test_fill_gaps_returns_new_array():
    """fill_gaps does not modify its input."""
    signal = np.array([1.0, np.nan, 3.0])
    time = np.array([0.0, 0.001, 0.002])
    original = signal.copy()
    fill_gaps(signal, time, max_gap_seconds=0.01, sampling_rate_hz=1000.0)
    np.testing.assert_array_equal(signal, original)
