"""Analysis result containers.

These frozen dataclasses are produced by the processing pipeline and consumed
by the UI and report generator.  No calculations are performed here — all
numeric fields receive their values from the relevant ``core/`` algorithm
modules in later stages.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from iva.core.models.enums import PeakInterpretation, RiskLevel
from iva.core.models.settings import SpectralSettings
from iva.core.models.signal_data import ProcessedSignalData, ValidatedSignalData

__all__ = [
    "SpectralPeak",
    "SpectrumResult",
    "PhysicsResult",
    "RiskAssessment",
    "ValidationResult",
    "AnalysisResult",
]


@dataclass(frozen=True)
class SpectralPeak:
    """One detected peak in the power spectral density estimate."""

    frequency_hz: float
    amplitude: float
    width_hz_3db: float
    interpretation: PeakInterpretation
    confidence: float


@dataclass(frozen=True)
class SpectrumResult:
    """Full result of the spectral analysis step."""

    frequencies: NDArray[np.float64]
    psd_values: NDArray[np.float64]
    dominant_peak: SpectralPeak | None
    all_peaks: tuple[SpectralPeak, ...]
    rms_total: float
    rms_in_band: float | None
    rms_trend: NDArray[np.float64]
    applied_settings: SpectralSettings

    def __post_init__(self) -> None:  # noqa: D105
        for attr in ("frequencies", "psd_values", "rms_trend"):
            arr = np.asarray(getattr(self, attr), dtype=np.float64)
            object.__setattr__(self, attr, arr)
            arr.flags.writeable = False


@dataclass(frozen=True)
class PhysicsResult:
    """Computed dimensionless and dimensional flow characterisation values."""

    reynolds_number: float
    strouhal_number: float
    calculated_shedding_frequency_hz: float
    velocity_ratio: float | None
    frequency_ratio: float | None
    kinematic_viscosity_m2s: float


@dataclass(frozen=True)
class RiskAssessment:
    """Resonance risk classification with engineering recommendation."""

    risk_level: RiskLevel
    dominant_frequency_deviation: float
    recommendation_text: str
    contributing_factors: tuple[str, ...]


@dataclass(frozen=True)
class ValidationResult:
    """Experiment-versus-CFD comparison metrics."""

    coordinate_array: NDArray[np.float64]
    experiment_array: NDArray[np.float64]
    cfd_array: NDArray[np.float64]
    rmse: float
    mae: float
    mape: float | None
    pearson_r: float
    is_mape_valid: bool

    def __post_init__(self) -> None:  # noqa: D105
        for attr in ("coordinate_array", "experiment_array", "cfd_array"):
            arr = np.asarray(getattr(self, attr), dtype=np.float64)
            object.__setattr__(self, attr, arr)
            arr.flags.writeable = False


@dataclass(frozen=True)
class AnalysisResult:
    """Top-level container aggregating every result produced in one session."""

    session_id: str
    completed_at: datetime
    source_file_path: Path
    source_file_md5: str
    validated_data: ValidatedSignalData | None
    processed_data: ProcessedSignalData | None
    spectrum: SpectrumResult | None
    physics: PhysicsResult | None
    risk: RiskAssessment | None
    validation: ValidationResult | None
    warnings: tuple[str, ...]
