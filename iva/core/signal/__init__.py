"""Signal preprocessing package for the Industrial Vibration Analyzer.

Public API — import from here rather than from submodules directly.
"""

from __future__ import annotations

from iva.core.signal.filter import (
    apply_bandpass_filter,
    apply_highpass_filter,
    apply_lowpass_filter,
)
from iva.core.signal.outlier_detector import detect_outliers, replace_outliers
from iva.core.signal.preprocessor import fill_gaps, preprocess_signal, remove_mean

__all__ = [
    "remove_mean",
    "fill_gaps",
    "preprocess_signal",
    "detect_outliers",
    "replace_outliers",
    "apply_bandpass_filter",
    "apply_lowpass_filter",
    "apply_highpass_filter",
]
