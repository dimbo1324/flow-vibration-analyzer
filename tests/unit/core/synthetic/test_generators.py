"""Unit tests for pure synthetic signal generators."""

from __future__ import annotations

import numpy as np
import pytest

from iva.core.models.exceptions import ValidationError
from iva.core.synthetic.generators import (
    generate_clean_sine,
    generate_noisy_sine,
    generate_with_gaps,
    generate_with_harmonics,
    generate_with_outliers,
)


def _dominant_frequency(signal: np.ndarray, sampling_rate_hz: float) -> float:
    frequencies = np.fft.rfftfreq(len(signal), d=1.0 / sampling_rate_hz)
    amplitudes = np.abs(np.fft.rfft(signal))
    return float(frequencies[int(np.argmax(amplitudes[1:])) + 1])


def test_clean_sine_length_sampling_rate_and_peak() -> None:
    time_s, signal = generate_clean_sine(40.0, 8.0, 1000.0, 1.0)
    assert len(time_s) == len(signal) == 8000
    assert np.median(np.diff(time_s)) == pytest.approx(0.001)
    assert _dominant_frequency(signal, 1000.0) == pytest.approx(40.0, abs=0.2)


def test_noisy_sine_is_deterministic_with_seed() -> None:
    first = generate_noisy_sine(40.0, 6.0, 500.0, 1.0, 15.0, seed=7)[1]
    second = generate_noisy_sine(40.0, 6.0, 500.0, 1.0, 15.0, seed=7)[1]
    np.testing.assert_array_equal(first, second)


def test_harmonic_signal_contains_expected_components() -> None:
    _, signal = generate_with_harmonics(40.0, 8.0, 1000.0, 1.0, 3)
    spectrum = np.abs(np.fft.rfft(signal))
    frequencies = np.fft.rfftfreq(len(signal), d=0.001)
    for expected in (40.0, 80.0, 120.0):
        index = int(np.argmin(np.abs(frequencies - expected)))
        assert spectrum[index] > 100.0


def test_outlier_generator_changes_exact_number_of_samples() -> None:
    base = np.zeros(1000, dtype=np.float64)
    result = generate_with_outliers(base, 12, 5.0, seed=11)
    assert np.count_nonzero(result != base) == 12


def test_gap_generator_inserts_expected_nan_count() -> None:
    base = np.ones(1000, dtype=np.float64)
    result = generate_with_gaps(base, 0.05, seed=11)
    assert np.isnan(result).sum() == 50


@pytest.mark.parametrize(
    "call",
    [
        lambda: generate_clean_sine(0.0, 6.0, 1000.0, 1.0),
        lambda: generate_clean_sine(600.0, 6.0, 1000.0, 1.0),
        lambda: generate_with_harmonics(40.0, 6.0, 1000.0, 1.0, 0),
        lambda: generate_with_gaps(np.ones(10), 1.5),
        lambda: generate_with_outliers(np.ones(10), 11, 2.0),
    ],
)
def test_invalid_parameters_raise_validation_error(call) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(ValidationError):
        call()
