"""Public API for the IVA core domain model layer.

Import from this package to avoid depending on internal module layout:

    from iva.core.models import SignalRole, RiskLevel, AnalysisResult
"""

from __future__ import annotations

from iva.core.models.analysis_result import (
    AnalysisResult,
    PhysicsResult,
    RiskAssessment,
    SpectralPeak,
    SpectrumResult,
    ValidationResult,
)
from iva.core.models.enums import (
    GeometryType,
    PeakInterpretation,
    RiskLevel,
    SignalRole,
    WindowType,
)
from iva.core.models.exceptions import (
    EmptySignalError,
    ExportError,
    FileCorruptedError,
    FileReadError,
    FilterConfigurationError,
    InsufficientDataError,
    IVAError,
    IVAFileNotFoundError,
    NonMonotonicTimeAxisError,
    PhysicsInputError,
    ProcessingError,
    UnsupportedFormatError,
    ValidationError,
)
from iva.core.models.flow_parameters import FlowParameters
from iva.core.models.settings import AnalysisSettings, PreprocessingSettings, SpectralSettings
from iva.core.models.signal_data import (
    ColumnRoleAssignment,
    ProcessedSignalData,
    RawFileData,
    ValidatedSignalData,
)

__all__ = [
    # Enums
    "GeometryType",
    "PeakInterpretation",
    "RiskLevel",
    "SignalRole",
    "WindowType",
    # Input / intermediate signal data
    "ColumnRoleAssignment",
    "ProcessedSignalData",
    "RawFileData",
    "ValidatedSignalData",
    # Settings
    "AnalysisSettings",
    "PreprocessingSettings",
    "SpectralSettings",
    # Flow parameters
    "FlowParameters",
    # Analysis results
    "AnalysisResult",
    "PhysicsResult",
    "RiskAssessment",
    "SpectrumResult",
    "SpectralPeak",
    "ValidationResult",
    # Exceptions
    "EmptySignalError",
    "ExportError",
    "FileCorruptedError",
    "FileReadError",
    "FilterConfigurationError",
    "InsufficientDataError",
    "IVAError",
    "IVAFileNotFoundError",
    "NonMonotonicTimeAxisError",
    "PhysicsInputError",
    "ProcessingError",
    "UnsupportedFormatError",
    "ValidationError",
]
