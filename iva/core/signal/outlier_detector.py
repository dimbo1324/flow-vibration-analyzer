"""MAD-based outlier detection and replacement (Algorithms 2).

Algorithm reference: docs/11_algorithms.md, Algorithm 2.
Uses sliding median + MAD with scale factor 1.4826 (consistency factor for
normal distribution).  All operations are vectorised — no Python loops.
"""

from __future__ import annotations

import logging

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

logger = logging.getLogger(__name__)

# MAD consistency factor: makes MAD an unbiased estimator of σ for Gaussian data.
OUTLIER_SCALE_FACTOR: float = 1.4826


def detect_outliers(
    signal: np.ndarray,
    window_samples: int = 21,
    threshold_sigma: float = 4.0,
) -> np.ndarray:
    """Return a boolean mask where True marks outlier samples.

    Uses a sliding-window median + scaled MAD test.  The window is centred on
    each sample; edge samples outside the signal are handled by padding with the
    edge value before windowing.

    Args:
        signal: 1-D array of float signal values.  NaN values are treated as
            non-outlier (they are handled separately by ``fill_gaps``).
        window_samples: Number of samples in the sliding window (must be odd and ≥ 3).
        threshold_sigma: Samples deviating more than ``threshold_sigma * MAD``
            from the local median are flagged as outliers.

    Returns:
        Boolean array of the same shape as *signal*; True = outlier.
    """
    n = len(signal)
    outlier_mask = np.zeros(n, dtype=bool)

    if n < window_samples:
        return outlier_mask

    half = window_samples // 2

    # Pad edges by replicating boundary values so every sample gets a full window.
    padded = np.pad(signal, (half, half), mode="edge")

    windows = sliding_window_view(padded, window_shape=window_samples)  # shape (n, w)

    local_median = np.median(windows, axis=1)  # (n,)
    abs_dev = np.abs(windows - local_median[:, np.newaxis])  # (n, w)
    mad = np.median(abs_dev, axis=1) * OUTLIER_SCALE_FACTOR  # (n,)

    deviation = np.abs(signal - local_median)

    # Where MAD is zero, use a small epsilon to avoid false positives on flat regions.
    with np.errstate(invalid="ignore", divide="ignore"):
        threshold = np.where(mad > 0, threshold_sigma * mad, np.inf)

    # NaN samples are not outliers — they will be handled by gap filling.
    outlier_mask = (deviation > threshold) & ~np.isnan(signal)

    n_outliers = int(np.sum(outlier_mask))
    logger.debug("detect_outliers: %d outlier(s) flagged in %d samples", n_outliers, n)
    return outlier_mask


def replace_outliers(signal: np.ndarray, outlier_mask: np.ndarray) -> np.ndarray:
    """Replace flagged outliers with linearly interpolated values.

    Replaces each outlier with an interpolated value using the nearest valid
    (non-outlier, non-NaN) neighbours.  Edge outliers are replaced with the
    nearest valid value (constant extrapolation).

    Args:
        signal: 1-D signal array (may contain NaN for missing samples).
        outlier_mask: Boolean array of same length; True = outlier.

    Returns:
        New array with outliers replaced.  The original array is not modified.
    """
    result = signal.copy()
    n_outliers = int(np.sum(outlier_mask))
    if n_outliers == 0:
        return result

    indices = np.arange(len(signal))
    # Valid = not an outlier AND not NaN
    valid_mask = ~outlier_mask & ~np.isnan(signal)

    if not np.any(valid_mask):
        logger.warning("replace_outliers: no valid reference points found; returning zeros")
        result[outlier_mask] = 0.0
        return result

    valid_idx = indices[valid_mask]
    valid_val = signal[valid_mask]

    result[outlier_mask] = np.interp(indices[outlier_mask], valid_idx, valid_val)

    logger.info("replace_outliers: %d outlier(s) replaced by interpolation", n_outliers)
    return result
