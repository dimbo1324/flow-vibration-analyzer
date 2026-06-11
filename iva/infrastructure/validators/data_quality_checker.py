"""Data quality checker for the Industrial Vibration Analyzer.

Converts a raw :class:`~iva.core.models.signal_data.RawFileData` + a column
role assignment into a validated :class:`~iva.core.models.signal_data.ValidatedSignalData`.

This module performs *structural and quality checks only*.  It does NOT:
  - interpolate gaps
  - remove outliers
  - apply filters
  - detrend signals
  - compute FFT/PSD/RMS
  - perform physical calculations

Warnings are accumulated as strings and included in ``ValidatedSignalData.warnings``
(a ``tuple[str, ...]`` as defined by the Stage 2 model).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from iva.core.models.enums import SignalRole
from iva.core.models.exceptions import (
    EmptySignalError,
    InsufficientDataError,
    NonMonotonicTimeAxisError,
    ValidationError,
)
from iva.core.models.signal_data import ColumnRoleAssignment, RawFileData, ValidatedSignalData
from iva.infrastructure.logging.app_logger import get_logger

logger = get_logger(__name__)

_MIN_DURATION_SECONDS = 5.0
_SAMPLING_INTERVAL_TOLERANCE = 0.0001  # 0.01 %
_MISSING_WARNING_THRESHOLD = 0.30  # 30 %

# Simple mapping from SignalRole to physical unit string.
_ROLE_TO_UNIT: dict[SignalRole, str] = {
    SignalRole.ACCELERATION_X: "m/s^2",
    SignalRole.ACCELERATION_Y: "m/s^2",
    SignalRole.ACCELERATION_Z: "m/s^2",
    SignalRole.PRESSURE: "Pa",
    SignalRole.VELOCITY: "m/s",
}


def check_data_quality(
    raw_data: RawFileData,
    assignment: ColumnRoleAssignment,
) -> ValidatedSignalData:
    """Validate raw tabular data and produce a :class:`ValidatedSignalData`.

    Args:
        raw_data: The result of reading a file with one of the infrastructure
            readers.  ``raw_data.data`` must be a pandas DataFrame.
        assignment: Column roles and sensor metadata supplied by the caller.

    Returns:
        A :class:`ValidatedSignalData` containing cleaned arrays and quality
        metrics.

    Raises:
        ValidationError: A required column is missing or contains non-numeric
            data.
        NonMonotonicTimeAxisError: The time column is not strictly increasing.
        EmptySignalError: The signal column is all-NaN, all-zero or empty.
        InsufficientDataError: The recording is shorter than 5 seconds.
    """
    warnings: list[str] = []

    # ------------------------------------------------------------------ #
    # 1. Verify raw data shape
    # ------------------------------------------------------------------ #
    logger.debug("Data quality check started for '%s'", raw_data.file_path.name)

    df = raw_data.data
    if df is None or not isinstance(df, pd.DataFrame):
        raise ValidationError(
            user_message="The raw data does not contain a valid table.",
            technical_details=f"Expected pandas DataFrame, got {type(df)}",
        )
    if len(df) < 2:
        raise InsufficientDataError(
            user_message="The file contains fewer than 2 data rows — too little data to validate.",
            technical_details=f"Row count: {len(df)}",
        )

    # ------------------------------------------------------------------ #
    # 2. Verify required columns exist
    # ------------------------------------------------------------------ #
    logger.debug(
        "Checking required columns: time='%s', signal='%s'",
        assignment.time_column,
        assignment.primary_signal_column,
    )

    for col_label, col_name in (
        ("time", assignment.time_column),
        ("primary signal", assignment.primary_signal_column),
    ):
        if col_name not in df.columns:
            raise ValidationError(
                user_message=f"Required {col_label} column '{col_name}' was not found in the file.",
                technical_details=f"Available columns: {list(df.columns)}",
                recovery_hint="Check column names and update the column role assignment.",
            )

    # ------------------------------------------------------------------ #
    # 3. Convert time column to numeric
    # ------------------------------------------------------------------ #
    logger.debug("Converting time column to numeric")
    try:
        time_series = pd.to_numeric(df[assignment.time_column], errors="raise")
    except (ValueError, TypeError) as exc:
        raise ValidationError(
            user_message=f"The time column '{assignment.time_column}' contains non-numeric values.",
            technical_details=str(exc),
            recovery_hint="Ensure the time column contains only numbers (seconds).",
        ) from exc

    time_array = time_series.to_numpy(dtype=np.float64, na_value=np.nan)

    # ------------------------------------------------------------------ #
    # 4. Convert signal column to numeric
    # ------------------------------------------------------------------ #
    logger.debug("Converting signal column to numeric")
    try:
        signal_series = pd.to_numeric(df[assignment.primary_signal_column], errors="raise")
    except (ValueError, TypeError) as exc:
        raise ValidationError(
            user_message=f"The signal column '{assignment.primary_signal_column}' "
            "contains non-numeric values.",
            technical_details=str(exc),
            recovery_hint="Ensure the signal column contains only numbers.",
        ) from exc

    signal_array = signal_series.to_numpy(dtype=np.float64, na_value=np.nan)

    # ------------------------------------------------------------------ #
    # 5. Check time axis monotonicity (NaN-tolerant)
    # ------------------------------------------------------------------ #
    logger.debug("Checking time axis monotonicity")
    finite_time = time_array[np.isfinite(time_array)]
    if len(finite_time) >= 2:
        diffs = np.diff(finite_time)
        if np.any(diffs <= 0):
            first_bad = int(np.argwhere(diffs <= 0)[0][0])
            raise NonMonotonicTimeAxisError(
                user_message="The time axis is not strictly increasing.",
                technical_details=(
                    f"Non-monotonic step found near index {first_bad}: "
                    f"t[{first_bad}]={finite_time[first_bad]}, "
                    f"t[{first_bad + 1}]={finite_time[first_bad + 1]}"
                ),
                recovery_hint="Sort the data by the time column before loading.",
            )

    # ------------------------------------------------------------------ #
    # 6. Sampling interval consistency
    # ------------------------------------------------------------------ #
    if len(finite_time) >= 2:
        diffs = np.diff(finite_time)
        median_interval = float(np.median(diffs))
        if median_interval > 0:
            relative_variation = float(np.max(np.abs(diffs - median_interval)) / median_interval)
            logger.debug(
                "Sampling interval variation: %.6f (tolerance: %.4f)",
                relative_variation,
                _SAMPLING_INTERVAL_TOLERANCE,
            )
            if relative_variation > _SAMPLING_INTERVAL_TOLERANCE:
                msg = (
                    f"Sampling interval is not perfectly constant "
                    f"(variation {relative_variation * 100:.3f}%, tolerance 0.010%)."
                )
                warnings.append(msg)
                logger.warning("%s", msg)

    # ------------------------------------------------------------------ #
    # 7. Missing fraction
    # ------------------------------------------------------------------ #
    n_total = len(signal_array)
    n_missing_signal = int(np.sum(np.isnan(signal_array)))
    n_missing_time = int(np.sum(np.isnan(time_array)))
    n_missing = max(n_missing_signal, n_missing_time)
    missing_fraction = n_missing / n_total if n_total > 0 else 0.0
    logger.debug("Missing fraction: %.4f", missing_fraction)

    if missing_fraction > _MISSING_WARNING_THRESHOLD:
        msg = (
            f"More than {_MISSING_WARNING_THRESHOLD * 100:.0f}% of signal values are missing "
            f"({missing_fraction * 100:.1f}% missing)."
        )
        warnings.append(msg)
        logger.warning("%s", msg)

    # ------------------------------------------------------------------ #
    # 8. Empty / all-zero signal
    # ------------------------------------------------------------------ #
    finite_signal = signal_array[np.isfinite(signal_array)]
    if len(finite_signal) == 0:
        raise EmptySignalError(
            user_message="The signal column contains no valid (finite) values.",
            technical_details=f"Column '{assignment.primary_signal_column}' is entirely NaN/Inf.",
        )

    if np.all(finite_signal == 0.0):
        raise EmptySignalError(
            user_message="The signal column contains only zeros. The sensor may not be connected.",
            technical_details=f"Column '{assignment.primary_signal_column}' is all-zero.",
            recovery_hint="Check the sensor connection and verify the data file.",
        )

    # ------------------------------------------------------------------ #
    # 9. Outlier fraction (4σ rule)
    # ------------------------------------------------------------------ #
    mean_val = float(np.mean(finite_signal))
    std_val = float(np.std(finite_signal))
    if std_val > 0:
        outlier_mask = np.abs(finite_signal - mean_val) > 4.0 * std_val
        outlier_fraction = float(np.sum(outlier_mask)) / len(finite_signal)
    else:
        outlier_fraction = 0.0
    logger.debug("Outlier fraction (4σ): %.4f", outlier_fraction)

    # ------------------------------------------------------------------ #
    # 10. Duration check
    # ------------------------------------------------------------------ #
    if len(finite_time) >= 2:
        duration_seconds = float(finite_time[-1] - finite_time[0])
    else:
        duration_seconds = 0.0

    logger.debug("Duration: %.3f s (minimum: %.1f s)", duration_seconds, _MIN_DURATION_SECONDS)

    if duration_seconds < _MIN_DURATION_SECONDS:
        raise InsufficientDataError(
            user_message=(
                f"The recording is only {duration_seconds:.2f} s long. "
                f"A minimum of {_MIN_DURATION_SECONDS:.0f} seconds is required."
            ),
            technical_details=f"time[0]={finite_time[0] if len(finite_time) else 'N/A'}, "
            f"time[-1]={finite_time[-1] if len(finite_time) else 'N/A'}",
            recovery_hint="Use a longer recording.",
        )

    # ------------------------------------------------------------------ #
    # 11. Sensor conversion factor
    # ------------------------------------------------------------------ #
    if assignment.sensor_conversion_factor is not None:
        signal_array = signal_array * assignment.sensor_conversion_factor
        logger.debug("Sensor conversion factor applied: %.6g", assignment.sensor_conversion_factor)

    # ------------------------------------------------------------------ #
    # 12. Sampling rate
    # ------------------------------------------------------------------ #
    if assignment.sampling_rate_hz > 0:
        sampling_rate_hz = assignment.sampling_rate_hz
    else:
        if len(finite_time) >= 2:
            sampling_rate_hz = 1.0 / float(np.median(np.diff(finite_time)))
        else:
            sampling_rate_hz = 0.0
    logger.debug("Sampling rate: %.2f Hz", sampling_rate_hz)

    # ------------------------------------------------------------------ #
    # 13. Physical unit
    # ------------------------------------------------------------------ #
    physical_unit = _ROLE_TO_UNIT.get(assignment.signal_role, "a.u.")

    sample_count = len(time_array)

    logger.info(
        "Data quality check passed for '%s': %d samples, %.2f s, "
        "missing=%.1f%%, outliers=%.1f%%",
        raw_data.file_path.name,
        sample_count,
        duration_seconds,
        missing_fraction * 100,
        outlier_fraction * 100,
    )

    return ValidatedSignalData(
        time_array=time_array,
        signal_array=signal_array,
        sampling_rate_hz=sampling_rate_hz,
        duration_seconds=duration_seconds,
        sample_count=sample_count,
        signal_role=assignment.signal_role,
        physical_unit=physical_unit,
        missing_fraction=missing_fraction,
        outlier_fraction=outlier_fraction,
        warnings=tuple(warnings),
    )
