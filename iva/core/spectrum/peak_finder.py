"""Peak detection and interpretation in PSD spectra (Algorithms 6 and 7).

Algorithm reference: documentation/11_algorithms.md, Algorithms 6 and 7.

Algorithm 6 — peak finding:
    1. Convert PSD to dB: psd_db = 10 * log10(psd)
    2. Baseline = median(psd_db)
    3. Threshold = baseline + peak_detection_threshold_db
    4. Find peaks above threshold via scipy.signal.find_peaks
    5. Filter by minimum width
    6. Compute -3 dB width via scipy.signal.peak_widths

Algorithm 7 — peak interpretation:
    - VORTEX_SHEDDING: within 5 % of calculated shedding frequency
    - HARMONIC: within 2 % of integer multiple of dominant peak frequency
    - STRUCTURAL: within 3 % of natural frequency
    - UNKNOWN: otherwise
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np
import scipy.signal

from iva.core.models.analysis_result import SpectralPeak
from iva.core.models.enums import PeakInterpretation
from iva.core.models.settings import SpectralSettings

if TYPE_CHECKING:
    from iva.core.models.analysis_result import PhysicsResult

logger = logging.getLogger(__name__)

_VORTEX_THRESHOLD = 0.05  # 5 % relative deviation
_HARMONIC_THRESHOLD = 0.02  # 2 % relative deviation
_STRUCTURAL_THRESHOLD = 0.03  # 3 % relative deviation
_HARMONIC_CONFIDENCE = 0.85
_MIN_PSD_DB = -200.0  # floor for log conversion of near-zero PSD


def find_peaks(
    frequencies: np.ndarray,
    psd_values: np.ndarray,
    settings: SpectralSettings,
) -> list[SpectralPeak]:
    """Detect spectral peaks and return them sorted by amplitude (descending).

    Args:
        frequencies: 1-D array of frequency values in Hz.
        psd_values: 1-D array of PSD values (same length as *frequencies*).
        settings: Spectral analysis configuration; uses
            ``peak_detection_threshold_db`` and ``peak_min_width_hz``.

    Returns:
        List of :class:`~iva.core.models.analysis_result.SpectralPeak` objects
        sorted by amplitude descending.  May be empty if no peaks pass the
        threshold and width filters.
    """
    # Convert to dB, clip to floor to avoid -inf from log of zero
    with np.errstate(divide="ignore", invalid="ignore"):
        psd_db = np.where(psd_values > 0, 10.0 * np.log10(psd_values), _MIN_PSD_DB)

    baseline = float(np.median(psd_db))
    threshold = baseline + settings.peak_detection_threshold_db

    logger.debug(
        "find_peaks: baseline=%.2f dB, threshold=%.2f dB (offset=%.1f dB)",
        baseline,
        threshold,
        settings.peak_detection_threshold_db,
    )

    # Find candidate peaks above threshold (peak properties are not needed here)
    candidate_idx, _ = scipy.signal.find_peaks(psd_db, height=threshold)
    logger.debug("find_peaks: %d candidate peak(s) before width filter", len(candidate_idx))

    if len(candidate_idx) == 0:
        return []

    # Frequency resolution
    df = float(frequencies[1] - frequencies[0]) if len(frequencies) > 1 else 1.0

    # Compute -3 dB widths for all candidates at once
    widths_samples, _, _, _ = scipy.signal.peak_widths(psd_db, candidate_idx, rel_height=0.5)
    widths_hz = widths_samples * df

    # Filter by minimum width
    min_width_samples = settings.peak_min_width_hz / df if df > 0 else 0.0

    peaks: list[SpectralPeak] = []
    for i, idx in enumerate(candidate_idx):
        if widths_samples[i] < min_width_samples:
            continue
        freq = float(frequencies[idx])
        amplitude = float(psd_values[idx])
        width_hz = float(widths_hz[i])
        peaks.append(
            SpectralPeak(
                frequency_hz=freq,
                amplitude=amplitude,
                width_hz_3db=width_hz,
                interpretation=PeakInterpretation.UNKNOWN,
                confidence=1.0,
            )
        )

    # Sort by amplitude descending
    peaks.sort(key=lambda p: p.amplitude, reverse=True)
    dominant_hz = peaks[0].frequency_hz if peaks else 0.0
    logger.info("Peaks found: %d (dominant: %.1f Hz)", len(peaks), dominant_hz)
    return peaks


def _is_harmonic(peak: SpectralPeak, peaks: list[SpectralPeak]) -> bool:
    """Return True if *peak* is a harmonic of a stronger fundamental peak.

    Implements Algorithm 7 rule 2 (documentation/11_algorithms.md): a peak is a
    HARMONIC if its frequency lies within ``_HARMONIC_THRESHOLD`` (2 %) of an
    integer multiple (2x, 3x, 4x) of *another* peak whose amplitude is at least
    twice as high.  This rule is purely a peak-to-peak relationship and does not
    require any physics context.
    """
    for other in peaks:
        if other is peak or other.frequency_hz <= 0:
            continue
        # The fundamental must be clearly stronger than its harmonic.
        if other.amplitude < 2.0 * peak.amplitude:
            continue
        for n in (2, 3, 4):
            harmonic_freq = other.frequency_hz * n
            if abs(peak.frequency_hz - harmonic_freq) / harmonic_freq <= _HARMONIC_THRESHOLD:
                return True
    return False


def interpret_peaks(
    peaks: list[SpectralPeak],
    physics_result: PhysicsResult | None,
) -> list[SpectralPeak]:
    """Classify each peak following Algorithm 7 (documentation/11_algorithms.md).

    Rules are applied in order; the first match wins:

    1. ``VORTEX_SHEDDING`` — within 5 % of the calculated shedding frequency
       (requires ``physics_result``).
    2. ``HARMONIC`` — within 2 % of an integer multiple of a stronger peak
       (no physics context required).
    3. ``STRUCTURAL`` — within 3 % of the natural frequency (requires
       ``physics_result``).
    4. ``UNKNOWN`` — otherwise.

    When *physics_result* is ``None`` the vortex and structural rules are
    skipped, but harmonic classification still runs because it depends only on
    the relationship between detected peaks.

    The natural frequency is recovered from the canonical ``PhysicsResult``
    fields: documentation/10 defines ``frequency_ratio = fs / fn``, so
    ``fn = calculated_shedding_frequency_hz / frequency_ratio`` exactly
    (``PhysicsResult`` intentionally stores the ratio rather than ``fn``).

    Args:
        peaks: List of detected peaks (from :func:`find_peaks`).
        physics_result: Physical calculation result providing the shedding
            frequency and frequency ratio.  May be ``None``.

    Returns:
        New list with the same peaks but with ``interpretation`` and
        ``confidence`` fields updated.
    """
    if not peaks:
        return list(peaks)

    shedding_hz = 0.0
    fn: float | None = None
    if physics_result is not None:
        shedding_hz = physics_result.calculated_shedding_frequency_hz
        ratio = physics_result.frequency_ratio
        if ratio is not None and ratio != 0:
            fn = shedding_hz / ratio

    interpreted: list[SpectralPeak] = []
    for peak in peaks:
        freq = peak.frequency_hz
        interpretation = PeakInterpretation.UNKNOWN
        confidence = 1.0

        # Rule 1 — VORTEX_SHEDDING (requires physics context).
        matched = False
        if physics_result is not None and shedding_hz > 0:
            dev = abs(freq - shedding_hz) / shedding_hz
            if dev <= _VORTEX_THRESHOLD:
                interpretation = PeakInterpretation.VORTEX_SHEDDING
                confidence = 1.0 - dev / _VORTEX_THRESHOLD
                matched = True

        # Rule 2 — HARMONIC (no physics context required).
        if not matched and _is_harmonic(peak, peaks):
            interpretation = PeakInterpretation.HARMONIC
            confidence = _HARMONIC_CONFIDENCE
            matched = True

        # Rule 3 — STRUCTURAL (requires natural frequency).
        if not matched and fn is not None and fn > 0:
            dev = abs(freq - fn) / fn
            if dev <= _STRUCTURAL_THRESHOLD:
                interpretation = PeakInterpretation.STRUCTURAL
                confidence = 1.0 - dev / _STRUCTURAL_THRESHOLD

        interpreted.append(
            SpectralPeak(
                frequency_hz=freq,
                amplitude=peak.amplitude,
                width_hz_3db=peak.width_hz_3db,
                interpretation=interpretation,
                confidence=confidence,
            )
        )

    return interpreted
