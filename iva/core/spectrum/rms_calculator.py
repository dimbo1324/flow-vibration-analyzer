"""RMS calculation functions (Algorithms 8 and band RMS).

Algorithm reference: documentation/11_algorithms.md, Algorithm 8 (sliding RMS).
All operations are vectorised — no Python loops over array elements.
"""

from __future__ import annotations

import logging

import numpy as np

logger = logging.getLogger(__name__)


def calculate_total_rms(signal: np.ndarray) -> float:
    """Compute the RMS of the entire signal.

    Formula: ``sqrt(mean(signal**2))``.

    Args:
        signal: 1-D float array.

    Returns:
        RMS value as a float.
    """
    rms = float(np.sqrt(np.mean(signal**2)))
    logger.debug("calculate_total_rms: RMS=%.6f", rms)
    return rms


def calculate_band_rms(
    frequencies: np.ndarray,
    psd_values: np.ndarray,
    low_hz: float,
    high_hz: float,
) -> float:
    """Compute RMS in a frequency band via Parseval integration.

    Integrates the PSD over [low_hz, high_hz] using the trapezoidal rule
    (``np.trapezoid`` / ``np.trapz``) and returns the square root.

    Args:
        frequencies: 1-D array of frequency values in Hz.
        psd_values: 1-D PSD array (same length as *frequencies*).
        low_hz: Lower bound of the integration band in Hz.
        high_hz: Upper bound of the integration band in Hz.

    Returns:
        Band RMS as a float.  Returns 0.0 if the band contains no PSD points.
    """
    mask = (frequencies >= low_hz) & (frequencies <= high_hz)
    if not np.any(mask):
        logger.debug(
            "calculate_band_rms: no PSD points in [%.1f, %.1f] Hz, returning 0.0",
            low_hz,
            high_hz,
        )
        return 0.0

    band_freq = frequencies[mask]
    band_psd = psd_values[mask]

    # Parseval: variance = integral(PSD, df)
    try:
        band_power = float(np.trapezoid(band_psd, band_freq))
    except AttributeError:
        band_power = float(np.trapz(band_psd, band_freq))  # NumPy < 2.0 fallback

    band_rms = float(np.sqrt(max(band_power, 0.0)))
    logger.debug(
        "calculate_band_rms: [%.1f, %.1f] Hz → RMS=%.6f",
        low_hz,
        high_hz,
        band_rms,
    )
    return band_rms


def calculate_rms_trend(
    signal: np.ndarray,
    sampling_rate_hz: float,
    window_seconds: float,
) -> np.ndarray:
    """Compute a sliding-window RMS trend (Algorithm 8).

    Uses ``np.convolve`` with a rectangular window — no Python loop.
    The output array has the same length as the input signal.  Samples at the
    beginning (before the first full window) are padded by repeating the first
    computed value.

    Args:
        signal: 1-D float array.
        sampling_rate_hz: Sampling frequency in Hz (used to convert
            *window_seconds* to samples).
        window_seconds: Duration of the sliding window in seconds.

    Returns:
        1-D array of RMS trend values, same length as *signal*.
    """
    window_samples = max(1, int(round(window_seconds * sampling_rate_hz)))
    if window_samples > len(signal):
        window_samples = len(signal)

    # Sliding mean of squared signal via convolution
    kernel = np.ones(window_samples) / window_samples
    squared = signal**2
    sliding_mean_sq = np.convolve(squared, kernel, mode="valid")  # length = n - w + 1
    trend_core = np.sqrt(sliding_mean_sq)

    # Pad beginning with first computed value to restore original length
    pad_length = len(signal) - len(trend_core)
    trend = np.empty(len(signal), dtype=np.float64)
    trend[:pad_length] = trend_core[0]
    trend[pad_length:] = trend_core

    logger.debug(
        "calculate_rms_trend: window=%d samples (%.3f s), output length=%d",
        window_samples,
        window_seconds,
        len(trend),
    )
    return trend
