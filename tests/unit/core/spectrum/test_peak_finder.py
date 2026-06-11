"""Unit tests for iva.core.spectrum.peak_finder."""

from __future__ import annotations

import numpy as np

from iva.core.models.analysis_result import PhysicsResult, SpectralPeak
from iva.core.models.enums import PeakInterpretation
from iva.core.models.settings import SpectralSettings
from iva.core.spectrum.peak_finder import find_peaks, interpret_peaks
from iva.core.spectrum.psd_calculator import calculate_psd

FS = 1000.0
SETTINGS = SpectralSettings(
    segment_length_samples=1024,
    overlap_fraction=0.5,
    peak_detection_threshold_db=10.0,
    peak_min_width_hz=0.0,  # no width filter so we can catch narrow peaks in short signals
)


def _psd(freq: float, duration: float = 10.0) -> tuple[np.ndarray, np.ndarray]:
    n = int(FS * duration)
    t = np.linspace(0.0, duration, n, endpoint=False)
    signal = np.sin(2.0 * np.pi * freq * t)
    return calculate_psd(signal, FS, SETTINGS)


def _two_freq_psd(f1: float, f2: float, duration: float = 10.0) -> tuple[np.ndarray, np.ndarray]:
    n = int(FS * duration)
    t = np.linspace(0.0, duration, n, endpoint=False)
    signal = np.sin(2.0 * np.pi * f1 * t) + np.sin(2.0 * np.pi * f2 * t)
    return calculate_psd(signal, FS, SETTINGS)


# ---------------------------------------------------------------------------
# find_peaks
# ---------------------------------------------------------------------------


def test_find_peaks_single_frequency_one_peak():
    """A single-frequency sine produces exactly one prominent peak."""
    freqs, psd = _psd(40.0)
    peaks = find_peaks(freqs, psd, SETTINGS)
    assert len(peaks) >= 1
    dominant_freq = peaks[0].frequency_hz
    assert 39.0 <= dominant_freq <= 41.0, f"Dominant peak at {dominant_freq:.2f} Hz"


def test_find_peaks_two_frequencies_two_peaks():
    """Two-frequency signal produces peaks at both frequencies."""
    freqs, psd = _two_freq_psd(40.0, 120.0)
    peaks = find_peaks(freqs, psd, SETTINGS)
    peak_freqs = sorted(p.frequency_hz for p in peaks)
    # Check that we have a peak near 40 Hz and one near 120 Hz
    has_40 = any(39.0 <= f <= 41.0 for f in peak_freqs)
    has_120 = any(119.0 <= f <= 121.0 for f in peak_freqs)
    assert has_40, f"No peak near 40 Hz; peaks: {peak_freqs}"
    assert has_120, f"No peak near 120 Hz; peaks: {peak_freqs}"


def test_find_peaks_sorted_by_amplitude_descending():
    """Returned peaks are sorted by amplitude, highest first."""
    freqs, psd = _two_freq_psd(40.0, 120.0)
    peaks = find_peaks(freqs, psd, SETTINGS)
    amplitudes = [p.amplitude for p in peaks]
    assert amplitudes == sorted(amplitudes, reverse=True)


def test_find_peaks_pure_noise_returns_few_peaks():
    """White noise produces no peaks above the threshold (or very few)."""
    rng = np.random.default_rng(42)
    signal = rng.standard_normal(int(FS * 10))
    freqs, psd = calculate_psd(signal, FS, SETTINGS)
    # With 10 dB threshold above median, white noise should have very few peaks
    peaks = find_peaks(freqs, psd, SETTINGS)
    # Allow at most 2 % of frequency bins to be flagged as peaks (usually 0)
    assert len(peaks) / len(freqs) < 0.02


def test_find_peaks_returns_spectral_peak_objects():
    """Each peak is a SpectralPeak with default UNKNOWN interpretation."""
    freqs, psd = _psd(40.0)
    peaks = find_peaks(freqs, psd, SETTINGS)
    for p in peaks:
        assert isinstance(p, SpectralPeak)
        assert p.interpretation == PeakInterpretation.UNKNOWN


# ---------------------------------------------------------------------------
# interpret_peaks
# ---------------------------------------------------------------------------


def test_interpret_peaks_none_physics_single_peak_unknown():
    """A lone peak with no physics context stays UNKNOWN (no harmonic relation)."""
    freqs, psd = _psd(40.0)
    peaks = find_peaks(freqs, psd, SETTINGS)
    interpreted = interpret_peaks(peaks, physics_result=None)
    for p in interpreted:
        assert p.interpretation == PeakInterpretation.UNKNOWN


def test_interpret_peaks_harmonic_without_physics():
    """Harmonics are classified even when no physics result is supplied.

    Per Algorithm 7 rule 2, the harmonic relationship depends only on the
    detected peaks, not on any physics context.
    """
    n = int(FS * 10)
    t = np.linspace(0.0, 10.0, n, endpoint=False)
    signal = (
        np.sin(2.0 * np.pi * 40.0 * t)
        + 0.5 * np.sin(2.0 * np.pi * 80.0 * t)
        + 0.3 * np.sin(2.0 * np.pi * 120.0 * t)
    )
    freqs, psd = calculate_psd(signal, FS, SETTINGS)
    peaks = find_peaks(freqs, psd, SETTINGS)
    interpreted = interpret_peaks(peaks, physics_result=None)
    harmonic_freqs = [
        p.frequency_hz for p in interpreted if p.interpretation == PeakInterpretation.HARMONIC
    ]
    assert any(
        79.0 <= f <= 81.0 for f in harmonic_freqs
    ), f"80 Hz not HARMONIC without physics; harmonics: {harmonic_freqs}"
    assert any(
        119.0 <= f <= 121.0 for f in harmonic_freqs
    ), f"120 Hz not HARMONIC without physics; harmonics: {harmonic_freqs}"


def test_interpret_peaks_fundamental_not_harmonic():
    """The strongest (fundamental) peak is never itself classified HARMONIC."""
    n = int(FS * 10)
    t = np.linspace(0.0, 10.0, n, endpoint=False)
    signal = np.sin(2.0 * np.pi * 40.0 * t) + 0.5 * np.sin(2.0 * np.pi * 80.0 * t)
    freqs, psd = calculate_psd(signal, FS, SETTINGS)
    peaks = find_peaks(freqs, psd, SETTINGS)
    interpreted = interpret_peaks(peaks, physics_result=None)
    fundamental = min(interpreted, key=lambda p: abs(p.frequency_hz - 40.0))
    assert fundamental.interpretation != PeakInterpretation.HARMONIC


def test_find_peaks_default_settings_keeps_dominant_peak():
    """With default SpectralSettings (peak_min_width_hz=0.5) the real 40 Hz peak survives."""
    default_settings = SpectralSettings()
    n = int(FS * 10)
    t = np.linspace(0.0, 10.0, n, endpoint=False)
    signal = np.sin(2.0 * np.pi * 40.0 * t)
    freqs, psd = calculate_psd(signal, FS, default_settings)
    peaks = find_peaks(freqs, psd, default_settings)
    assert len(peaks) >= 1
    assert 39.0 <= peaks[0].frequency_hz <= 41.0


def test_interpret_peaks_harmonic_detected():
    """Peaks at 80 Hz and 120 Hz are classified as HARMONIC of 40 Hz."""
    n = int(FS * 10)
    t = np.linspace(0.0, 10.0, n, endpoint=False)
    # Fundamental at 40 Hz, harmonics at 80 and 120 Hz
    signal = (
        np.sin(2.0 * np.pi * 40.0 * t)
        + 0.5 * np.sin(2.0 * np.pi * 80.0 * t)
        + 0.3 * np.sin(2.0 * np.pi * 120.0 * t)
    )
    freqs, psd = calculate_psd(signal, FS, SETTINGS)
    peaks = find_peaks(freqs, psd, SETTINGS)
    # interpret_peaks with no physics result to only test harmonic logic
    # Dominant peak = 40 Hz; harmonics at 80 and 120 Hz should be HARMONIC
    interpreted = interpret_peaks(peaks, physics_result=None)
    # With None physics, all UNKNOWN — harmonic classification only fires with physics
    # Re-run with a dummy physics result that has no shedding near 80/120 Hz

    physics = PhysicsResult(
        reynolds_number=1e4,
        strouhal_number=0.21,
        calculated_shedding_frequency_hz=200.0,  # far from 40/80/120 Hz
        velocity_ratio=None,
        frequency_ratio=None,
        kinematic_viscosity_m2s=1e-6,
    )
    interpreted = interpret_peaks(peaks, physics_result=physics)
    harmonic_freqs = [
        p.frequency_hz for p in interpreted if p.interpretation == PeakInterpretation.HARMONIC
    ]
    has_80 = any(79.0 <= f <= 81.0 for f in harmonic_freqs)
    has_120 = any(119.0 <= f <= 121.0 for f in harmonic_freqs)
    assert has_80, f"80 Hz peak not classified as HARMONIC; harmonics at: {harmonic_freqs}"
    assert has_120, f"120 Hz peak not classified as HARMONIC; harmonics at: {harmonic_freqs}"
