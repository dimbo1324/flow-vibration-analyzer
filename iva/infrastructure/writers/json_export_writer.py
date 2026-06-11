"""JSON export writer for analysis results.

Writes a concise, machine-readable JSON summary of the analysis.  Large arrays
(``frequencies``, ``psd_values``, ``rms_trend``) are intentionally excluded to
keep the file small.  Only scalar summaries are written.

Architecture rule: no numerical calculations here — only serialisation.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from iva.core.models.analysis_result import AnalysisResult
from iva.core.models.exceptions import ExportError

logger = logging.getLogger(__name__)

__all__ = ["export_analysis_summary_json"]


def export_analysis_summary_json(result: AnalysisResult, output_path: str | Path) -> Path:
    """Write a concise JSON summary of *result* to *output_path*.

    The file contains all scalar values but no large numerical arrays.

    Args:
        result: Completed analysis result.
        output_path: Destination file path (created if necessary).

    Returns:
        The resolved output path.

    Raises:
        ExportError: If the file cannot be written.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    summary = _build_summary(result)

    try:
        with open(output_path, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, indent=2, ensure_ascii=False, default=_json_default)
    except OSError as exc:
        raise ExportError(
            user_message=f"Cannot write JSON summary to '{output_path.name}'.",
            technical_details=str(exc),
        ) from exc

    logger.info("export_analysis_summary_json: written to '%s'", output_path.name)
    return output_path


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _json_default(obj: Any) -> Any:  # noqa: ANN401
    """Fallback serialiser for non-standard types."""
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (datetime,)):
        return obj.isoformat()
    if isinstance(obj, Path):
        return str(obj)
    # Enum subclasses (StrEnum) stringify naturally via str(); call it explicitly.
    return str(obj)


def _build_summary(result: AnalysisResult) -> dict[str, Any]:
    """Convert *result* to a plain dict suitable for JSON serialisation."""
    summary: dict[str, Any] = {
        "session_id": result.session_id,
        "completed_at": result.completed_at.isoformat(),
        "source_file": str(result.source_file_path),
        "source_file_md5": result.source_file_md5,
    }

    # Spectrum section
    if result.spectrum is not None:
        sp = result.spectrum
        dominant = None
        if sp.dominant_peak is not None:
            dp = sp.dominant_peak
            dominant = {
                "frequency_hz": float(dp.frequency_hz),
                "amplitude": float(dp.amplitude),
                "width_hz_3db": float(dp.width_hz_3db),
                "interpretation": str(dp.interpretation),
                "confidence": float(dp.confidence),
            }
        summary["spectrum"] = {
            "dominant_peak": dominant,
            "peak_count": len(sp.all_peaks),
            "all_peaks": [
                {
                    "frequency_hz": float(p.frequency_hz),
                    "amplitude": float(p.amplitude),
                    "width_hz_3db": float(p.width_hz_3db),
                    "interpretation": str(p.interpretation),
                    "confidence": float(p.confidence),
                }
                for p in sp.all_peaks
            ],
            "rms_total": float(sp.rms_total),
            "rms_in_band": float(sp.rms_in_band) if sp.rms_in_band is not None else None,
            "frequency_points": len(sp.frequencies),
            "freq_min_hz": float(sp.frequencies[0]) if len(sp.frequencies) > 0 else None,
            "freq_max_hz": float(sp.frequencies[-1]) if len(sp.frequencies) > 0 else None,
        }
    else:
        summary["spectrum"] = None

    # Physics section
    if result.physics is not None:
        ph = result.physics
        summary["physics"] = {
            "reynolds_number": float(ph.reynolds_number),
            "strouhal_number": float(ph.strouhal_number),
            "calculated_shedding_frequency_hz": float(ph.calculated_shedding_frequency_hz),
            "velocity_ratio": float(ph.velocity_ratio) if ph.velocity_ratio is not None else None,
            "frequency_ratio": (
                float(ph.frequency_ratio) if ph.frequency_ratio is not None else None
            ),
            "kinematic_viscosity_m2s": float(ph.kinematic_viscosity_m2s),
        }
    else:
        summary["physics"] = None

    # Risk section
    if result.risk is not None:
        risk = result.risk
        summary["risk"] = {
            "risk_level": str(risk.risk_level),
            "dominant_frequency_deviation": float(risk.dominant_frequency_deviation),
            "recommendation_text": risk.recommendation_text,
            "contributing_factors": list(risk.contributing_factors),
        }
    else:
        summary["risk"] = None

    # Warnings
    summary["warnings"] = list(result.warnings)

    return summary
