"""Domain enumerations for the Industrial Vibration Analyzer.

These are the stable string-valued enums shared across all application layers.
Values match the strings used in serialised settings and reports.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = [
    "SignalRole",
    "WindowType",
    "PeakInterpretation",
    "GeometryType",
    "RiskLevel",
]


class SignalRole(StrEnum):
    """Physical role assigned to a data column by the user."""

    ACCELERATION_X = "acceleration_x"
    ACCELERATION_Y = "acceleration_y"
    ACCELERATION_Z = "acceleration_z"
    PRESSURE = "pressure"
    VELOCITY = "velocity"


class WindowType(StrEnum):
    """Spectral window function for Welch PSD estimation."""

    HANN = "hann"
    HAMMING = "hamming"
    RECTANGULAR = "rectangular"


class PeakInterpretation(StrEnum):
    """Classification of a detected spectral peak."""

    VORTEX_SHEDDING = "vortex_shedding"
    HARMONIC = "harmonic"
    STRUCTURAL = "structural"
    UNKNOWN = "unknown"


class GeometryType(StrEnum):
    """Cylinder configuration for flow-induced vibration analysis."""

    SINGLE_CYLINDER = "single_cylinder"
    TANDEM = "tandem"


class RiskLevel(StrEnum):
    """Three-level resonance risk classification."""

    SAFE = "safe"
    WATCH = "watch"
    CRITICAL = "critical"
