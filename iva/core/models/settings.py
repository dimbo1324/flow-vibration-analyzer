"""Analysis settings dataclasses.

Default values are taken verbatim from documentation/10_data_models_and_schemas.md.
These containers are frozen so that a settings object passed into one pipeline
step cannot be mutated by another.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from iva.core.models.enums import WindowType

if TYPE_CHECKING:
    from iva.core.models.flow_parameters import FlowParameters

__all__ = [
    "PreprocessingSettings",
    "SpectralSettings",
    "AnalysisSettings",
]


@dataclass(frozen=True)
class PreprocessingSettings:
    """Configuration for the signal preprocessing chain.

    The order of operations is fixed: remove mean → outlier removal →
    gap filling → bandpass filter → normalisation.
    """

    remove_mean: bool = True
    remove_outliers: bool = True
    outlier_window_samples: int = 21
    outlier_threshold_sigma: float = 4.0
    fill_gaps: bool = True
    max_gap_ms: float = 50.0
    apply_bandpass_filter: bool = True
    filter_low_hz: float = 5.0
    filter_high_hz: float = 250.0
    filter_order: int = 4


@dataclass(frozen=True)
class SpectralSettings:
    """Configuration for the Welch PSD estimation and peak detection."""

    window_type: WindowType = WindowType.HANN
    segment_length_samples: int = 1024
    overlap_fraction: float = 0.5
    peak_detection_threshold_db: float = 10.0
    peak_min_width_hz: float = 0.5
    rms_band_low_hz: float | None = None
    rms_band_high_hz: float | None = None
    rms_window_seconds: float = 1.0


@dataclass(frozen=True)
class AnalysisSettings:
    """Top-level container that groups all settings for one analysis session."""

    preprocessing: PreprocessingSettings = field(default_factory=PreprocessingSettings)
    spectral: SpectralSettings = field(default_factory=SpectralSettings)
    flow_parameters: FlowParameters | None = None
