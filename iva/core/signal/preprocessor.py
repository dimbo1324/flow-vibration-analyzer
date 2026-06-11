"""Signal preprocessing pipeline (Algorithms 1, 3, and the main pipeline).

Algorithm reference: documentation/11_algorithms.md, Algorithms 1 and 3.
Pipeline order (fixed, per documentation/09_processing_pipeline.md):
    1. remove_mean
    2. detect_outliers → replace_outliers
    3. fill_gaps
    4. apply_bandpass_filter
"""

from __future__ import annotations

import logging

import numpy as np

from iva.core.models.settings import PreprocessingSettings
from iva.core.models.signal_data import ProcessedSignalData, ValidatedSignalData

logger = logging.getLogger(__name__)

_GAP_WARNING_FRACTION = 0.05  # warn if more than 5 % of samples are filled


def remove_mean(signal: np.ndarray) -> np.ndarray:
    """Subtract the mean from the signal (Algorithm 1).

    Args:
        signal: 1-D float array.  NaN values are ignored when computing
            the mean (``np.nanmean``).

    Returns:
        New array with zero mean.
    """
    offset = float(np.nanmean(signal))
    result = signal - offset
    logger.info("remove_mean: offset was %.6f", offset)
    return result


def fill_gaps(
    signal: np.ndarray,
    time_array: np.ndarray,
    max_gap_seconds: float,
    sampling_rate_hz: float,
) -> np.ndarray:
    """Fill NaN gaps in the signal (Algorithm 3).

    Short gaps (≤ *max_gap_seconds*) are filled with linear interpolation.
    Long gaps and gaps at the edges of the signal are filled with zeros.

    Args:
        signal: 1-D signal array that may contain NaN values.
        time_array: 1-D time axis in seconds, same length as *signal*.
        max_gap_seconds: Gaps of this duration or shorter are interpolated;
            longer gaps are zeroed.
        sampling_rate_hz: Used only for logging the gap fraction.

    Returns:
        New array with all NaN values replaced.
    """
    result = signal.copy()
    nan_mask = np.isnan(result)

    if not np.any(nan_mask):
        return result

    n = len(result)

    # Identify contiguous NaN runs as (start, end) index pairs (inclusive).
    gaps: list[tuple[int, int]] = []
    in_gap = False
    gap_start = 0
    for i in range(n):
        if nan_mask[i] and not in_gap:
            in_gap = True
            gap_start = i
        elif not nan_mask[i] and in_gap:
            in_gap = False
            gaps.append((gap_start, i - 1))
    if in_gap:
        gaps.append((gap_start, n - 1))

    n_interpolated = 0
    n_zeroed = 0

    for start, end in gaps:
        if start > 0 and end < n - 1:
            gap_duration = float(time_array[end] - time_array[start])
        else:
            gap_duration = max_gap_seconds + 1.0
        is_edge = start == 0 or end == n - 1

        if not is_edge and gap_duration <= max_gap_seconds:
            # Linear interpolation using flanking valid samples
            left_idx = start - 1
            right_idx = end + 1
            left_val = result[left_idx]
            right_val = result[right_idx]
            for j in range(start, end + 1):
                frac = (j - left_idx) / (right_idx - left_idx)
                result[j] = left_val + frac * (right_val - left_val)
            n_interpolated += end - start + 1
        else:
            result[start : end + 1] = 0.0
            n_zeroed += end - start + 1

    total_filled = n_interpolated + n_zeroed
    filled_fraction = total_filled / n if n > 0 else 0.0
    logger.debug(
        "fill_gaps: %d interpolated, %d zeroed (%.2f%% of signal)",
        n_interpolated,
        n_zeroed,
        filled_fraction * 100,
    )
    if filled_fraction > _GAP_WARNING_FRACTION:
        logger.warning(
            "fill_gaps: gap fraction %.1f%% exceeds %.0f%% threshold, interpolation applied",
            filled_fraction * 100,
            _GAP_WARNING_FRACTION * 100,
        )
    return result


def preprocess_signal(
    data: ValidatedSignalData,
    settings: PreprocessingSettings,
) -> ProcessedSignalData:
    """Run the full preprocessing pipeline and return cleaned signal data.

    Pipeline order (fixed per documentation/09_processing_pipeline.md):
        1. remove_mean
        2. detect_outliers + replace_outliers
        3. fill_gaps
        4. apply_bandpass_filter

    Args:
        data: Validated signal data from the infrastructure layer.
        settings: Preprocessing configuration.

    Returns:
        :class:`~iva.core.models.signal_data.ProcessedSignalData` with both
        the cleaned (pre-filter) and filtered signal arrays, plus a log of
        applied operations.
    """
    from iva.core.signal.filter import apply_bandpass_filter
    from iva.core.signal.outlier_detector import detect_outliers, replace_outliers

    log: list[str] = []
    signal = data.signal_array.copy()
    time = data.time_array

    # Step 1: remove mean
    if settings.remove_mean:
        offset = float(np.nanmean(signal))
        signal = remove_mean(signal)
        log.append(f"remove_mean: offset={offset:.6f}")

    # Step 2: outlier detection and replacement
    if settings.remove_outliers:
        outlier_mask = detect_outliers(
            signal,
            window_samples=settings.outlier_window_samples,
            threshold_sigma=settings.outlier_threshold_sigma,
        )
        n_outliers = int(np.sum(outlier_mask))
        if n_outliers > 0:
            signal = replace_outliers(signal, outlier_mask)
            log.append(f"replace_outliers: {n_outliers} point(s) replaced")
        else:
            log.append("replace_outliers: no outliers detected")

    # Step 3: gap filling
    if settings.fill_gaps:
        max_gap_seconds = settings.max_gap_ms / 1000.0
        signal = fill_gaps(
            signal,
            time_array=time,
            max_gap_seconds=max_gap_seconds,
            sampling_rate_hz=data.sampling_rate_hz,
        )
        log.append(f"fill_gaps: max_gap={max_gap_seconds*1000:.1f} ms")

    # Store cleaned signal before filtering
    signal_cleaned = signal.copy()

    # Step 4: bandpass filter
    signal_filtered = signal_cleaned.copy()
    if settings.apply_bandpass_filter:
        signal_filtered = apply_bandpass_filter(
            signal_cleaned,
            sampling_rate_hz=data.sampling_rate_hz,
            low_hz=settings.filter_low_hz,
            high_hz=settings.filter_high_hz,
            order=settings.filter_order,
        )
        log.append(
            f"apply_bandpass_filter: [{settings.filter_low_hz}, {settings.filter_high_hz}] Hz, "
            f"order={settings.filter_order}"
        )

    logger.info("preprocess_signal: pipeline completed (%d step(s))", len(log))

    return ProcessedSignalData(
        time_array=time,
        signal_cleaned=signal_cleaned,
        signal_filtered=signal_filtered,
        preprocessing_log=tuple(log),
        applied_settings=settings,
    )
