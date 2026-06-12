"""Координатор полного аналитического конвейера.

Это единственное место, где стадии из ``docs/09_processing_pipeline.md``
связываются в общий процесс. Координатор вызывает ``iva.core`` и
``iva.infrastructure``, но не выполняет численные расчёты самостоятельно.

Архитектурные правила:
- нельзя импортировать ``iva.ui`` или ``PySide6``;
- все формулы остаются в ``iva.core``.
"""

from __future__ import annotations

import hashlib
import time
import uuid
from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from iva.app.analysis_session import AnalysisSession
from iva.core.models.analysis_result import AnalysisResult, SpectrumResult
from iva.core.models.exceptions import IVAError, ProcessingError
from iva.core.models.settings import AnalysisSettings
from iva.core.physics.lock_in_risk import assess_risk
from iva.core.physics.physics_result_builder import build_physics_result
from iva.core.signal.preprocessor import preprocess_signal
from iva.core.spectrum.peak_finder import find_peaks, interpret_peaks
from iva.core.spectrum.psd_calculator import calculate_psd
from iva.core.spectrum.rms_calculator import (
    calculate_band_rms,
    calculate_rms_trend,
    calculate_total_rms,
)
from iva.infrastructure.logging.app_logger import get_logger
from iva.infrastructure.readers import read_file
from iva.infrastructure.validators.data_quality_checker import check_data_quality

logger = get_logger(__name__)

__all__ = ["run_pipeline"]


@contextmanager
def _timed_step(name: str) -> Generator[None, None, None]:
    """Записать в журнал длительность именованной стадии конвейера."""
    t0 = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - t0
        logger.info("%s completed in %.3f s", name, elapsed)


def _compute_md5(file_path: Path) -> str:
    """Вернуть MD5 содержимого файла для аудита воспроизводимости."""
    h = hashlib.md5()
    with open(file_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def run_pipeline(session: AnalysisSession) -> AnalysisResult:
    """Выполнить полный конвейер и вернуть ``AnalysisResult``.

    Steps (per docs/09_processing_pipeline.md):
        1. Validate session readiness.
        2. Read the source file.
        3. Validate data quality.
        4. Preprocess the signal.
        5. Compute PSD.
        6. Find spectral peaks.
        7. Compute RMS (total, band, trend).
        8. Assemble SpectrumResult.
        9. Physics calculations (if flow_parameters are set).
       10. Interpret peaks with physics context.
       11. Assess lock-in risk (if physics available).
       12. Assemble AnalysisResult.
       13. Store result in session.

    Args:
        session: The current analysis session.  Must satisfy
            ``session.is_ready_for_analysis()``.

    Returns:
        A fully populated :class:`AnalysisResult`.

    Raises:
        ProcessingError: If the session is not ready for analysis.
        IVAError: Any IVA-specific error from a pipeline step is logged and
            re-raised so the caller can handle it appropriately.
    """
    pipeline_start = time.perf_counter()

    # ВАЖНО: порядок шагов конвейера фиксирован и соответствует
    # docs/09_processing_pipeline.md. Нарушать его нельзя — например,
    # интерпретация пиков (шаг 10) выполняется ПОСЛЕ расчёта физики, иначе
    # частоту срыва вихрей (VORTEX_SHEDDING) невозможно сопоставить с пиком.
    # Координатор только вызывает модули core/ и infrastructure/ и сам не
    # выполняет никаких числовых расчётов.

    # ------------------------------------------------------------------ #
    # Шаг 1 — проверка готовности сеанса
    # ------------------------------------------------------------------ #
    if not session.is_ready_for_analysis():
        raise ProcessingError(
            user_message=(
                "Не удалось запустить анализ: не выбран исходный файл " "или не назначены столбцы."
            ),
            technical_details=(
                f"source_file_path={session.source_file_path}, "
                f"role_assignment={session.role_assignment}"
            ),
            recovery_hint="Выберите файл данных и назначьте роли столбцов перед запуском анализа.",
        )

    assert session.source_file_path is not None  # Сужение типа после проверки готовности.
    assert session.role_assignment is not None

    source_path = session.source_file_path
    settings: AnalysisSettings = session.settings
    warnings: list[str] = []
    if session.is_demo:
        warnings.extend(
            (
                "Демонстрационные синтетические данные",
                (
                    "Данные сгенерированы программно и предназначены только для "
                    "демонстрации работы приложения."
                ),
            )
        )

    logger.info("Pipeline started for '%s'", source_path.name)

    try:
        # ------------------------------------------------------------------ #
        # Шаг 2 — чтение файла
        # ------------------------------------------------------------------ #
        with _timed_step("File read"):
            raw_data = read_file(str(source_path))
        session.raw_data = raw_data

        # Хэш исходника фиксируется до изменения состояния и входит в аудит.
        with _timed_step("MD5 hash"):
            source_md5 = _compute_md5(source_path)
        logger.info("Source file MD5: %s", source_md5)

        # ------------------------------------------------------------------ #
        # Шаг 3 — структурная проверка и качество данных
        # ------------------------------------------------------------------ #
        with _timed_step("Data quality check"):
            validated_data = check_data_quality(raw_data, session.role_assignment)
        warnings.extend(validated_data.warnings)

        # ------------------------------------------------------------------ #
        # Шаг 4 — предобработка сигнала
        # ------------------------------------------------------------------ #
        with _timed_step("Signal preprocessing"):
            processed_data = preprocess_signal(validated_data, settings.preprocessing)

        # ------------------------------------------------------------------ #
        # Шаг 5 — расчёт PSD
        # ------------------------------------------------------------------ #
        with _timed_step("PSD calculation"):
            frequencies, psd_values = calculate_psd(
                processed_data.signal_filtered,
                validated_data.sampling_rate_hz,
                settings.spectral,
            )

        # ------------------------------------------------------------------ #
        # Шаг 6 — поиск спектральных пиков
        # ------------------------------------------------------------------ #
        with _timed_step("Peak detection"):
            raw_peaks = find_peaks(frequencies, psd_values, settings.spectral)

        # ------------------------------------------------------------------ #
        # Шаг 7 — расчёты RMS
        # ------------------------------------------------------------------ #
        with _timed_step("RMS calculation"):
            rms_total = calculate_total_rms(processed_data.signal_filtered)

            rms_in_band: float | None = None
            if (
                settings.spectral.rms_band_low_hz is not None
                and settings.spectral.rms_band_high_hz is not None
            ):
                rms_in_band = calculate_band_rms(
                    frequencies,
                    psd_values,
                    settings.spectral.rms_band_low_hz,
                    settings.spectral.rms_band_high_hz,
                )

            rms_trend = calculate_rms_trend(
                processed_data.signal_filtered,
                validated_data.sampling_rate_hz,
                settings.spectral.rms_window_seconds,
            )

        # ------------------------------------------------------------------ #
        # Шаг 8 — предварительная подготовка SpectrumResult. Интерпретация
        # пиков отложена до появления физического контекста.
        # ------------------------------------------------------------------ #
        # Только после физики можно отличить VORTEX_SHEDDING от неизвестного пика.

        # ------------------------------------------------------------------ #
        # Шаг 9 — физические расчёты, если заданы параметры потока
        # ------------------------------------------------------------------ #
        physics_result = None
        if settings.flow_parameters is not None:
            with _timed_step("Physics calculations"):
                try:
                    physics_result = build_physics_result(settings.flow_parameters)
                except IVAError as exc:
                    logger.error("Physics calculation failed: %s", exc)
                    warnings.append(f"Расчет физических параметров пропущен: {exc.user_message}")

        # ------------------------------------------------------------------ #
        # Шаг 10 — интерпретация пиков с физическим контекстом
        # ------------------------------------------------------------------ #
        with _timed_step("Peak interpretation"):
            interpreted_peaks = interpret_peaks(raw_peaks, physics_result)

        dominant_peak = interpreted_peaks[0] if interpreted_peaks else None

        spectrum_result = SpectrumResult(
            frequencies=frequencies,
            psd_values=psd_values,
            dominant_peak=dominant_peak,
            all_peaks=tuple(interpreted_peaks),
            rms_total=rms_total,
            rms_in_band=rms_in_band,
            rms_trend=rms_trend,
            applied_settings=settings.spectral,
        )

        # ------------------------------------------------------------------ #
        # Шаг 11 — оценка риска; без физики она намеренно пропускается
        # ------------------------------------------------------------------ #
        risk_assessment = None
        if physics_result is not None:
            with _timed_step("Risk assessment"):
                risk_assessment = assess_risk(physics_result, spectrum_result)

        # ------------------------------------------------------------------ #
        # Шаг 12 — сборка единого результата для CLI, UI и отчётов
        # ------------------------------------------------------------------ #
        session_id = str(uuid.uuid4())
        completed_at = datetime.now(UTC)

        result = AnalysisResult(
            session_id=session_id,
            completed_at=completed_at,
            source_file_path=source_path,
            source_file_md5=source_md5,
            validated_data=validated_data,
            processed_data=processed_data,
            spectrum=spectrum_result,
            physics=physics_result,
            risk=risk_assessment,
            validation=None,
            warnings=tuple(warnings),
            is_demo=session.is_demo,
            demo_scenario_key=session.demo_scenario_key,
            demo_title=session.demo_title,
            demo_description=session.demo_description,
        )

    except IVAError:
        logger.error("Pipeline failed with IVAError", exc_info=True)
        raise
    except Exception as exc:
        logger.error("Pipeline failed with unexpected error: %s", exc, exc_info=True)
        raise ProcessingError(
            user_message="Во время анализа произошла непредвиденная ошибка.",
            technical_details=str(exc),
        ) from exc

    total_elapsed = time.perf_counter() - pipeline_start
    logger.info(
        "Analysis completed: session %s, %.3f s total",
        session_id,
        total_elapsed,
    )

    # ------------------------------------------------------------------ #
    # Шаг 13 — атомарная публикация результата в состоянии сеанса
    # ------------------------------------------------------------------ #
    session.result = result
    session.warnings = list(warnings)

    return result
