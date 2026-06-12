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
from iva.infrastructure.reporting.report_strings_ru import (
    PEAK_INTERPRETATION_LABELS,
    RISK_LABELS,
    SIGNAL_ROLE_LABELS,
    display_label,
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

    if result.is_demo:
        demo_body = (
            "Демонстрационные синтетические данные\n"
            f"Сценарий: {result.demo_title or result.demo_scenario_key or 'демо-сценарий'}\n"
            "Данные сгенерированы программно и предназначены только для "
            "демонстрации работы приложения."
        )
        sections.append(ReportSection(title="Демонстрационный режим", body=demo_body, level=1))

    # ── Section: Overview ──────────────────────────────────────────────────
    overview_body = (
        f"ID сеанса:        {result.session_id}\n"
        f"Завершено:        {result.completed_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        f"Исходный файл:    {result.source_file_path}\n"
        f"MD5 источника:    {result.source_file_md5}\n"
        f"Предупреждения:   {len(result.warnings)}"
    )
    sections.append(ReportSection(title="Обзор", body=overview_body, level=1))

    # ── Section: Data quality (validated_data) ─────────────────────────────
    if result.validated_data is not None:
        vd = result.validated_data
        dq_body = (
            f"Количество отсчетов: {vd.sample_count}\n"
            f"Длительность:         {vd.duration_seconds:.3f} s\n"
            f"Частота дискретизации:{vd.sampling_rate_hz:>10.1f} Hz\n"
            f"Роль сигнала:         {display_label(SIGNAL_ROLE_LABELS, vd.signal_role)}\n"
            f"Физическая единица:   {vd.physical_unit}\n"
            f"Доля пропусков:       {vd.missing_fraction:.4f}\n"
            f"Доля выбросов:        {vd.outlier_fraction:.4f}"
        )
        sections.append(ReportSection(title="Качество данных", body=dq_body, level=1))
    else:
        sections.append(
            ReportSection(
                title="Качество данных",
                body="Исходные данные в этом сеансе недоступны.",
                level=1,
            )
        )

    # ── Section: Preprocessing ─────────────────────────────────────────────
    if result.processed_data is not None:
        pd_data = result.processed_data
        log_text = "\n".join(pd_data.preprocessing_log) if pd_data.preprocessing_log else "(нет)"
        sections.append(
            ReportSection(title="Предобработка", body=f"Выполненные операции:\n{log_text}", level=1)
        )
    else:
        sections.append(
            ReportSection(title="Предобработка", body="Обработанные данные недоступны.", level=1)
        )

    # ── Section: Spectral Analysis ────────────────────────────────────────
    if result.spectrum is not None:
        sp = result.spectrum
        spec_body_lines = [
            f"Частотных точек:    {len(sp.frequencies)}",
            f"Общий RMS:          {sp.rms_total:.6g}",
        ]
        if sp.rms_in_band is not None:
            spec_body_lines.append(f"RMS в полосе:       {sp.rms_in_band:.6g}")
        if sp.dominant_peak is not None:
            dp = sp.dominant_peak
            spec_body_lines.append(
                f"Доминирующий пик:  {dp.frequency_hz:.3f} Hz "
                f"(амплитуда={dp.amplitude:.4g}, ширина={dp.width_hz_3db:.3f} Hz, "
                f"{display_label(PEAK_INTERPRETATION_LABELS, dp.interpretation)}, "
                f"достоверность={dp.confidence:.2f})"
            )
        spec_body_lines.append(f"Всего найдено пиков: {len(sp.all_peaks)}")
        sections.append(
            ReportSection(title="Спектральный анализ", body="\n".join(spec_body_lines), level=1)
        )

        # Peaks table
        if sp.all_peaks:
            peak_rows = tuple(
                (
                    f"{pk.frequency_hz:.3f}",
                    f"{pk.amplitude:.4e}",
                    f"{pk.width_hz_3db:.3f}",
                    display_label(PEAK_INTERPRETATION_LABELS, pk.interpretation),
                    f"{pk.confidence:.2f}",
                )
                for pk in sp.all_peaks
            )
            tables.append(
                ReportTable(
                    title="Обнаруженные спектральные пики",
                    headers=(
                        "Частота (Hz)",
                        "Амплитуда",
                        "Ширина -3 dB (Hz)",
                        "Интерпретация",
                        "Достоверность",
                    ),
                    rows=peak_rows,
                )
            )
    else:
        sections.append(
            ReportSection(
                title="Спектральный анализ",
                body="Спектральный анализ не выполнен.",
                level=1,
            )
        )

    # ── Section: Physics ──────────────────────────────────────────────────
    if result.physics is not None:
        ph = result.physics
        phys_body = (
            f"Число Рейнольдса (Re):          {ph.reynolds_number:.4e}\n"
            f"Число Струхаля (St):            {ph.strouhal_number:.6f}\n"
            f"Частота срыва (fs):             {ph.calculated_shedding_frequency_hz:.4f} Hz\n"
            f"Кинематическая вязкость (nu):   {ph.kinematic_viscosity_m2s:.4e} m²/s\n"
            f"Приведенная скорость (Vr):      "
            + (f"{ph.velocity_ratio:.4f}" if ph.velocity_ratio is not None else "нет данных")
            + "\n"
            "Отношение частот (fs/fn):       "
            + (f"{ph.frequency_ratio:.4f}" if ph.frequency_ratio is not None else "нет данных")
        )
        sections.append(ReportSection(title="Физические параметры", body=phys_body, level=1))
    else:
        sections.append(
            ReportSection(
                title="Физические параметры",
                body="Расчет не выполнен: параметры потока не заданы.",
                level=1,
            )
        )

    # ── Section: Risk Assessment ──────────────────────────────────────────
    if result.risk is not None:
        risk = result.risk
        risk_body = (
            f"Уровень риска:             {display_label(RISK_LABELS, risk.risk_level)}\n"
            f"Отклонение частоты:        {risk.dominant_frequency_deviation:.4f}\n\n"
            f"Рекомендация:\n{risk.recommendation_text}\n\n"
            f"Учитываемые факторы:\n"
            + "\n".join(f"  - {factor}" for factor in risk.contributing_factors)
        )
        sections.append(ReportSection(title="Оценка риска", body=risk_body, level=1))
    else:
        sections.append(
            ReportSection(
                title="Оценка риска",
                body="Риск не оценен: физические параметры недоступны или fn не задана.",
                level=1,
            )
        )

    # ── Section: Validation (Experiment vs CFD) ───────────────────────────
    if result.validation is not None:
        val = result.validation
        mape_str = (
            f"{val.mape:.4f} %" if val.is_mape_valid and val.mape is not None else "нет данных"
        )
        val_body = (
            f"RMSE:      {val.rmse:.6g}\n"
            f"MAE:       {val.mae:.6g}\n"
            f"MAPE:      {mape_str}\n"
            f"Пирсон r:  {val.pearson_r:.6f}\n"
            f"Точек:     {len(val.coordinate_array)}"
        )
        sections.append(ReportSection(title="Сравнение эксперимента и CFD", body=val_body, level=1))

    # ── Section: Warnings ─────────────────────────────────────────────────
    if result.warnings:
        warn_body = "\n".join(f"  [{i + 1}] {w}" for i, w in enumerate(result.warnings))
        sections.append(ReportSection(title="Предупреждения", body=warn_body, level=1))

    sections.append(
        ReportSection(
            title="Ограничения и отказ от ответственности",
            body=(
                "Этот отчет предназначен для инженерного анализа и не заменяет "
                "квалифицированное обследование, оценку конструкции или действующие "
                "процедуры безопасности. Выводы ограничены качеством предоставленных "
                "данных и настройками анализа."
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
        title="Отчет об анализе IVA",
        subtitle=(
            f"Демонстрационные синтетические данные — {result.demo_title}"
            if result.is_demo and result.demo_title
            else f"Источник: {result.source_file_path.name}"
        ),
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
            "is_demo": str(result.is_demo).lower(),
            "demo_scenario_key": result.demo_scenario_key or "",
            "demo_title": result.demo_title or "",
        },
    )
