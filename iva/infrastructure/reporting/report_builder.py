"""Build a ReportDocument from an AnalysisResult.

No numerical calculations are performed here — only serialisation of
already-computed values from the AnalysisResult model.

Architecture rule: this module must NOT import from iva.ui or PySide6.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from iva.__version__ import __version__
from iva.infrastructure.reporting.report_models import (
    ReportDocument,
    ReportSection,
    ReportTable,
)

if TYPE_CHECKING:
    from iva.core.models.analysis_result import AnalysisResult

logger = logging.getLogger(__name__)

__all__ = ["build_report_document"]


def build_report_document(result: AnalysisResult) -> ReportDocument:
    """Build a :class:`ReportDocument` from a completed :class:`AnalysisResult`.

    Args:
        result: The completed analysis result to summarise.

    Returns:
        A frozen :class:`ReportDocument` with sections and tables derived
        from the result.  None fields in the result (physics, risk, validation)
        produce placeholder sections rather than errors.
    """
    sections: list[ReportSection] = []
    tables: list[ReportTable] = []

    # ── Section: Overview ──────────────────────────────────────────────────
    overview_body = (
        f"Session ID:     {result.session_id}\n"
        f"Completed at:   {result.completed_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        f"Source file:    {result.source_file_path}\n"
        f"MD5 (source):   {result.source_file_md5}\n"
        f"Warnings:       {len(result.warnings)}"
    )
    sections.append(ReportSection(title="Overview", body=overview_body, level=1))

    # ── Section: Data quality (validated_data) ─────────────────────────────
    if result.validated_data is not None:
        vd = result.validated_data
        dq_body = (
            f"Sample count:       {vd.sample_count}\n"
            f"Duration:           {vd.duration_seconds:.3f} s\n"
            f"Sampling rate:      {vd.sampling_rate_hz:.1f} Hz\n"
            f"Signal role:        {vd.signal_role}\n"
            f"Physical unit:      {vd.physical_unit}\n"
            f"Missing fraction:   {vd.missing_fraction:.4f}\n"
            f"Outlier fraction:   {vd.outlier_fraction:.4f}"
        )
        sections.append(ReportSection(title="Data Quality", body=dq_body, level=1))
    else:
        sections.append(
            ReportSection(
                title="Data Quality", body="Raw data not available in this session.", level=1
            )
        )

    # ── Section: Preprocessing ─────────────────────────────────────────────
    if result.processed_data is not None:
        pd_data = result.processed_data
        log_text = "\n".join(pd_data.preprocessing_log) if pd_data.preprocessing_log else "(none)"
        sections.append(
            ReportSection(title="Preprocessing", body=f"Applied steps:\n{log_text}", level=1)
        )
    else:
        sections.append(
            ReportSection(title="Preprocessing", body="Processed data not available.", level=1)
        )

    # ── Section: Spectral Analysis ────────────────────────────────────────
    if result.spectrum is not None:
        sp = result.spectrum
        spec_body_lines = [
            f"Frequency points:  {len(sp.frequencies)}",
            f"RMS total:         {sp.rms_total:.6g}",
        ]
        if sp.rms_in_band is not None:
            spec_body_lines.append(f"RMS in band:       {sp.rms_in_band:.6g}")
        if sp.dominant_peak is not None:
            dp = sp.dominant_peak
            spec_body_lines.append(
                f"Dominant peak:     {dp.frequency_hz:.3f} Hz "
                f"(amp={dp.amplitude:.4g}, width={dp.width_hz_3db:.3f} Hz, "
                f"{dp.interpretation}, conf={dp.confidence:.2f})"
            )
        spec_body_lines.append(f"Total peaks found: {len(sp.all_peaks)}")
        sections.append(
            ReportSection(title="Spectral Analysis", body="\n".join(spec_body_lines), level=1)
        )

        # Peaks table
        if sp.all_peaks:
            peak_rows = tuple(
                (
                    f"{pk.frequency_hz:.3f}",
                    f"{pk.amplitude:.4e}",
                    f"{pk.width_hz_3db:.3f}",
                    str(pk.interpretation),
                    f"{pk.confidence:.2f}",
                )
                for pk in sp.all_peaks
            )
            tables.append(
                ReportTable(
                    title="Detected Spectral Peaks",
                    headers=(
                        "Frequency (Hz)",
                        "Amplitude",
                        "Width -3dB (Hz)",
                        "Interpretation",
                        "Confidence",
                    ),
                    rows=peak_rows,
                )
            )
    else:
        sections.append(
            ReportSection(
                title="Spectral Analysis", body="Spectral analysis not performed.", level=1
            )
        )

    # ── Section: Physics ──────────────────────────────────────────────────
    if result.physics is not None:
        ph = result.physics
        phys_body = (
            f"Reynolds number (Re):           {ph.reynolds_number:.4e}\n"
            f"Strouhal number (St):           {ph.strouhal_number:.6f}\n"
            f"Shedding frequency (fs):        {ph.calculated_shedding_frequency_hz:.4f} Hz\n"
            f"Kinematic viscosity (nu):       {ph.kinematic_viscosity_m2s:.4e} m²/s\n"
            f"Velocity ratio (Vr):            "
            + (f"{ph.velocity_ratio:.4f}" if ph.velocity_ratio is not None else "N/A")
            + "\n"
            "Frequency ratio (fs/fn):        "
            + (f"{ph.frequency_ratio:.4f}" if ph.frequency_ratio is not None else "N/A")
        )
        sections.append(ReportSection(title="Physics", body=phys_body, level=1))
    else:
        sections.append(
            ReportSection(
                title="Physics",
                body="Physics not calculated — flow parameters were not provided.",
                level=1,
            )
        )

    # ── Section: Risk Assessment ──────────────────────────────────────────
    if result.risk is not None:
        risk = result.risk
        risk_body = (
            f"Risk level:                {risk.risk_level.upper()}\n"
            f"Frequency deviation:       {risk.dominant_frequency_deviation:.4f}\n\n"
            f"Recommendation:\n{risk.recommendation_text}\n\n"
            f"Contributing factors:\n" + "\n".join(f"  - {f}" for f in risk.contributing_factors)
        )
        sections.append(ReportSection(title="Risk Assessment", body=risk_body, level=1))
    else:
        sections.append(
            ReportSection(
                title="Risk Assessment",
                body="Risk not assessed — physics not available or fn not set.",
                level=1,
            )
        )

    # ── Section: Validation (Experiment vs CFD) ───────────────────────────
    if result.validation is not None:
        val = result.validation
        mape_str = f"{val.mape:.4f} %" if val.is_mape_valid and val.mape is not None else "N/A"
        val_body = (
            f"RMSE:      {val.rmse:.6g}\n"
            f"MAE:       {val.mae:.6g}\n"
            f"MAPE:      {mape_str}\n"
            f"Pearson r: {val.pearson_r:.6f}\n"
            f"Points:    {len(val.coordinate_array)}"
        )
        sections.append(ReportSection(title="Experiment vs CFD Validation", body=val_body, level=1))

    # ── Section: Warnings ─────────────────────────────────────────────────
    if result.warnings:
        warn_body = "\n".join(f"  [{i + 1}] {w}" for i, w in enumerate(result.warnings))
        sections.append(ReportSection(title="Warnings", body=warn_body, level=1))

    sections.append(
        ReportSection(
            title="Limitations and Disclaimer",
            body=(
                "This report supports engineering review and does not replace qualified "
                "inspection, structural assessment, or applicable safety procedures. "
                "Conclusions are limited by the supplied data quality and analysis settings."
            ),
            level=1,
        )
    )

    logger.debug(
        "build_report_document: %d sections, %d tables for session %s",
        len(sections),
        len(tables),
        result.session_id,
    )

    return ReportDocument(
        title="IVA Analysis Report",
        subtitle=f"Source: {result.source_file_path.name}",
        generated_at=datetime.now(tz=UTC),
        sections=tuple(sections),
        tables=tuple(tables),
        figures=(),
        metadata={
            "session_id": result.session_id,
            "source_file": str(result.source_file_path),
            "source_file_md5": result.source_file_md5,
            "completed_at": result.completed_at.isoformat(),
            "iva_version": __version__,
        },
    )
