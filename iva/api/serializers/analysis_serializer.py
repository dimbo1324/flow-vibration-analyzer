"""Convert AnalysisResult to a JSON-safe dict for the API response.

Rules:
- All numpy arrays are converted to Python lists.
- Arrays are downsampled to at most MAX_POINTS points.
- No tracebacks or internal paths are included.
"""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import NDArray

from iva.core.models.analysis_result import AnalysisResult
from iva.core.models.enums import RiskLevel

__all__ = ["serialize_analysis_result"]

MAX_POINTS = 2000

_RISK_LABELS_RU: dict[str, str] = {
    RiskLevel.SAFE: "Безопасно",
    RiskLevel.WATCH: "Наблюдение",
    RiskLevel.CRITICAL: "Критический",
}


def _downsample(arr: NDArray[np.float64], max_points: int = MAX_POINTS) -> list[float]:
    """Return a list of at most *max_points* evenly-spaced values from *arr*."""
    n = len(arr)
    if n <= max_points:
        return [float(v) if math.isfinite(float(v)) else 0.0 for v in arr]
    step = n / max_points
    indices = [int(i * step) for i in range(max_points)]
    return [float(arr[i]) if math.isfinite(float(arr[i])) else 0.0 for i in indices]


def serialize_analysis_result(result: AnalysisResult) -> dict:  # type: ignore[type-arg]
    """Convert *result* to a fully JSON-serialisable dict."""

    # --- summary ---
    risk_level_str: str | None = None
    risk_label_ru: str | None = None
    if result.risk is not None:
        risk_level_str = str(result.risk.risk_level)
        risk_label_ru = _RISK_LABELS_RU.get(risk_level_str, risk_level_str)

    dominant_peak_hz: float | None = None
    if result.spectrum and result.spectrum.dominant_peak:
        dominant_peak_hz = result.spectrum.dominant_peak.frequency_hz

    rms_total: float | None = None
    if result.spectrum:
        rms_total = result.spectrum.rms_total

    reynolds: float | None = None
    strouhal: float | None = None
    if result.physics:
        reynolds = result.physics.reynolds_number
        strouhal = result.physics.strouhal_number

    summary = {
        "risk_level": risk_level_str,
        "risk_label_ru": risk_label_ru,
        "dominant_peak_hz": dominant_peak_hz,
        "rms_total": rms_total,
        "reynolds_number": reynolds,
        "strouhal_number": strouhal,
    }

    # --- signal ---
    if result.processed_data is not None and result.validated_data is not None:
        time_s = _downsample(result.processed_data.time_array)
        raw = _downsample(result.validated_data.signal_array)
        filtered = _downsample(result.processed_data.signal_filtered)
    else:
        time_s = []
        raw = []
        filtered = []

    rms_trend: list[float] = []
    if result.spectrum and result.spectrum.rms_trend is not None:
        rms_trend = _downsample(result.spectrum.rms_trend)

    signal = {
        "time_s": time_s,
        "raw": raw,
        "filtered": filtered,
        "rms_trend": rms_trend,
    }

    # --- spectrum ---
    frequencies_hz: list[float] = []
    psd: list[float] = []
    peaks: list[dict] = []  # type: ignore[type-arg]

    if result.spectrum is not None:
        frequencies_hz = _downsample(result.spectrum.frequencies)
        psd = _downsample(result.spectrum.psd_values)

        for peak in result.spectrum.all_peaks:
            amplitude_linear = peak.amplitude
            # Convert PSD amplitude to dB (10 * log10), guard against zero/negative
            if amplitude_linear > 0:
                amplitude_db = 10.0 * math.log10(amplitude_linear)
            else:
                amplitude_db = -100.0
            peaks.append(
                {
                    "frequency_hz": peak.frequency_hz,
                    "amplitude_db": round(amplitude_db, 3),
                    "type": str(peak.interpretation),
                }
            )

    spectrum = {
        "frequencies_hz": frequencies_hz,
        "psd": psd,
        "peaks": peaks,
    }

    # --- analysis_id ---
    scenario_key = result.demo_scenario_key or "unknown"
    analysis_id = f"demo-{scenario_key}-{result.session_id[:8]}"

    return {
        "analysis_id": analysis_id,
        "is_demo": result.is_demo,
        "demo_title": result.demo_title,
        "summary": summary,
        "signal": signal,
        "spectrum": spectrum,
        "warnings": list(result.warnings),
    }
