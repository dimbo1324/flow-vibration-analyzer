"""Input and intermediate signal data containers.

These frozen dataclasses travel through the processing pipeline from raw file
read (RawFileData) through quality validation (ValidatedSignalData) to the
end of preprocessing (ProcessedSignalData).  They are pure data containers —
no calculations are performed here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
from numpy.typing import NDArray

from iva.core.models.enums import SignalRole

if TYPE_CHECKING:
    from iva.core.models.settings import PreprocessingSettings

__all__ = [
    "RawFileData",
    "ColumnRoleAssignment",
    "ValidatedSignalData",
    "ProcessedSignalData",
]


@dataclass(frozen=True)
class RawFileData:
    """Result of reading an input file exactly as stored on disk.

    No interpretation or validation has been applied.  The ``data`` field
    holds the raw tabular content as a pandas DataFrame; its type is ``Any``
    because the concrete reader implementations are part of a later stage and
    the model layer must remain independent of infrastructure dependencies.
    """

    file_path: Path
    file_format: str
    column_names: tuple[str, ...]
    column_dtypes: dict[str, str]
    row_count: int
    file_size_bytes: int
    data: Any  # pandas DataFrame — typed concretely by the reader in Stage 3
    read_timestamp: datetime


@dataclass(frozen=True)
class ColumnRoleAssignment:
    """Mapping of file columns to semantic signal roles chosen by the user."""

    time_column: str
    primary_signal_column: str
    signal_role: SignalRole
    additional_columns: dict[str, SignalRole]
    sampling_rate_hz: float
    sensor_conversion_factor: float | None = None


@dataclass(frozen=True)
class ValidatedSignalData:
    """Signal data after structural and quality validation.

    Arrays are NumPy float64 arrays.  The ``warnings`` field accumulates
    non-critical issues discovered during validation so they can be surfaced
    to the user without aborting the pipeline.
    """

    time_array: NDArray[np.float64]
    signal_array: NDArray[np.float64]
    sampling_rate_hz: float
    duration_seconds: float
    sample_count: int
    signal_role: SignalRole
    physical_unit: str
    missing_fraction: float
    outlier_fraction: float
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:  # noqa: D105
        # Ensure arrays are read-only so downstream code cannot mutate them
        # without explicit intent.  This is a safety convention, not a
        # calculation.
        object.__setattr__(self, "time_array", np.asarray(self.time_array, dtype=np.float64))
        object.__setattr__(self, "signal_array", np.asarray(self.signal_array, dtype=np.float64))
        self.time_array.flags.writeable = False
        self.signal_array.flags.writeable = False


@dataclass(frozen=True)
class ProcessedSignalData:
    """Signal data after the full preprocessing chain has been applied.

    Contains both the cleaned signal (outlier/gap treatment only) and the
    filtered signal (bandpass applied).  The ``preprocessing_log`` list
    records which operations were applied, in order.
    """

    time_array: NDArray[np.float64]
    signal_cleaned: NDArray[np.float64]
    signal_filtered: NDArray[np.float64]
    preprocessing_log: tuple[str, ...]
    applied_settings: PreprocessingSettings

    def __post_init__(self) -> None:  # noqa: D105
        for attr in ("time_array", "signal_cleaned", "signal_filtered"):
            arr = np.asarray(getattr(self, attr), dtype=np.float64)
            object.__setattr__(self, attr, arr)
            arr.flags.writeable = False
