"""CSV export writers for analysis results.

Three public functions:
- :func:`export_spectrum_csv` — frequency / PSD / peak marker columns.
- :func:`export_signal_csv` — time / cleaned / filtered signal columns.
- :func:`export_physics_summary_csv` — physics parameters and risk level.

All functions accept an :class:`~iva.core.models.analysis_result.AnalysisResult`
and a destination path and return the resolved :class:`pathlib.Path`.

Architecture rule: no numerical calculations here — only serialisation.
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path

from iva.core.models.analysis_result import AnalysisResult
from iva.core.models.exceptions import ExportError

logger = logging.getLogger(__name__)

__all__ = [
    "export_spectrum_csv",
    "export_signal_csv",
    "export_physics_summary_csv",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ensure_parent(path: Path) -> None:
    """Create parent directories if they do not exist."""
    path.parent.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def export_spectrum_csv(result: AnalysisResult, output_path: str | Path) -> Path:
    """Export the frequency spectrum to a CSV file.

    Columns:
        ``frequency_hz``, ``psd``, ``is_peak``

    ``is_peak`` is ``1`` for frequency bins that correspond to a detected peak
    (nearest bin), ``0`` otherwise.

    Args:
        result: Completed analysis result.
        output_path: Destination file path.

    Returns:
        The resolved output path.

    Raises:
        ExportError: If the spectrum is unavailable or the file cannot be written.
    """
    output_path = Path(output_path)
    if result.spectrum is None:
        raise ExportError(
            user_message="Cannot export spectrum: spectral analysis was not performed.",
            technical_details="result.spectrum is None",
        )

    _ensure_parent(output_path)
    spectrum = result.spectrum
    frequencies = spectrum.frequencies
    psd_values = spectrum.psd_values

    # Build a set of peak frequency indices for the marker column
    peak_freqs = {p.frequency_hz for p in spectrum.all_peaks}

    try:
        with open(output_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["frequency_hz", "psd", "is_peak"])
            for freq, psd in zip(frequencies, psd_values, strict=True):
                # Mark a bin as a peak if any detected peak's frequency is
                # within half a frequency bin of this bin.
                df = float(frequencies[1] - frequencies[0]) if len(frequencies) > 1 else 1.0
                is_peak = int(any(abs(float(freq) - pf) <= df / 2 for pf in peak_freqs))
                writer.writerow([f"{float(freq):.6f}", f"{float(psd):.6e}", is_peak])
    except OSError as exc:
        raise ExportError(
            user_message=f"Cannot write spectrum CSV to '{output_path.name}'.",
            technical_details=str(exc),
        ) from exc

    logger.info("export_spectrum_csv: %d rows → '%s'", len(frequencies), output_path.name)
    return output_path


def export_signal_csv(result: AnalysisResult, output_path: str | Path) -> Path:
    """Export the time-domain signal to a CSV file.

    Columns:
        ``time_s``, ``signal_cleaned``, ``signal_filtered``

    Args:
        result: Completed analysis result.
        output_path: Destination file path.

    Returns:
        The resolved output path.

    Raises:
        ExportError: If processed signal data is unavailable or the file cannot
            be written.
    """
    output_path = Path(output_path)
    if result.processed_data is None:
        raise ExportError(
            user_message="Cannot export signal: signal processing was not performed.",
            technical_details="result.processed_data is None",
        )

    _ensure_parent(output_path)
    pd = result.processed_data

    try:
        with open(output_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["time_s", "signal_cleaned", "signal_filtered"])
            for t, sc, sf in zip(pd.time_array, pd.signal_cleaned, pd.signal_filtered, strict=True):
                writer.writerow([f"{float(t):.6f}", f"{float(sc):.6e}", f"{float(sf):.6e}"])
    except OSError as exc:
        raise ExportError(
            user_message=f"Cannot write signal CSV to '{output_path.name}'.",
            technical_details=str(exc),
        ) from exc

    n = len(pd.time_array)
    logger.info("export_signal_csv: %d rows → '%s'", n, output_path.name)
    return output_path


def export_physics_summary_csv(result: AnalysisResult, output_path: str | Path) -> Path:
    """Export a physics / risk summary to a CSV file.

    The file contains key–value rows.  If no physics result is available a
    single row ``physics,not available`` is written so the file always exists.

    Args:
        result: Completed analysis result.
        output_path: Destination file path.

    Returns:
        The resolved output path.

    Raises:
        ExportError: If the file cannot be written.
    """
    output_path = Path(output_path)
    _ensure_parent(output_path)

    rows: list[tuple[str, str]] = []

    if result.physics is None:
        rows.append(("physics", "not available"))
    else:
        ph = result.physics
        rows += [
            ("reynolds_number", f"{ph.reynolds_number:.4e}"),
            ("strouhal_number", f"{ph.strouhal_number:.6f}"),
            ("shedding_frequency_hz", f"{ph.calculated_shedding_frequency_hz:.4f}"),
            ("kinematic_viscosity_m2s", f"{ph.kinematic_viscosity_m2s:.4e}"),
        ]
        if ph.velocity_ratio is not None:
            rows.append(("velocity_ratio", f"{ph.velocity_ratio:.4f}"))
        if ph.frequency_ratio is not None:
            rows.append(("frequency_ratio", f"{ph.frequency_ratio:.4f}"))

    if result.risk is not None:
        risk = result.risk
        rows += [
            ("risk_level", str(risk.risk_level)),
            ("dominant_frequency_deviation", f"{risk.dominant_frequency_deviation:.4f}"),
            ("recommendation", risk.recommendation_text),
        ]
    else:
        rows.append(("risk_level", "not assessed"))

    try:
        with open(output_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["parameter", "value"])
            writer.writerows(rows)
    except OSError as exc:
        raise ExportError(
            user_message=f"Cannot write physics summary CSV to '{output_path.name}'.",
            technical_details=str(exc),
        ) from exc

    logger.info("export_physics_summary_csv: %d rows → '%s'", len(rows), output_path.name)
    return output_path
