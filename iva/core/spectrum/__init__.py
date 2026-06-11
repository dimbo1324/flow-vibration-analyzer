"""Spectral analysis package for the Industrial Vibration Analyzer.

Public API — import from here rather than from submodules directly.
"""

from __future__ import annotations

from iva.core.spectrum.peak_finder import find_peaks, interpret_peaks
from iva.core.spectrum.psd_calculator import calculate_psd
from iva.core.spectrum.rms_calculator import (
    calculate_band_rms,
    calculate_rms_trend,
    calculate_total_rms,
)

__all__ = [
    "calculate_psd",
    "find_peaks",
    "interpret_peaks",
    "calculate_total_rms",
    "calculate_band_rms",
    "calculate_rms_trend",
]
