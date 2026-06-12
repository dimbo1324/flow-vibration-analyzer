"""Safe JSON serialization for compact Stage 9 analysis sessions."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from iva.core.models.analysis_result import (
    AnalysisResult,
    PhysicsResult,
    RiskAssessment,
    SpectralPeak,
    SpectrumResult,
    ValidationResult,
)
from iva.core.models.enums import PeakInterpretation, RiskLevel, SignalRole, WindowType
from iva.core.models.exceptions import ValidationError
from iva.core.models.settings import PreprocessingSettings, SpectralSettings
from iva.core.models.signal_data import ProcessedSignalData, ValidatedSignalData

__all__ = [
    "VIBPROJ_SCHEMA_VERSION",
    "analysis_result_to_dict",
    "analysis_result_from_dict",
]

VIBPROJ_SCHEMA_VERSION = "1.0"
# Массивы прореживаются до этого числа точек перед записью в .vibproj: файл
# сессии должен оставаться компактным и быстрым для открытия. Исходный файл
# данных остаётся первоисточником для полного повторного анализа, поэтому
# потеря разрешения в сохранённой сессии безопасна. Значение _schema_version
# и машиночитаемые ключи менять нельзя без версионирования формата.
_MAX_STORED_POINTS = 5000


def analysis_result_to_dict(result: AnalysisResult) -> dict[str, Any]:
    """Convert an analysis result to a bounded, JSON-compatible mapping."""
    data: dict[str, Any] = {
        "_schema_version": VIBPROJ_SCHEMA_VERSION,
        "session_id": result.session_id,
        "completed_at": result.completed_at.isoformat(),
        "source_file_path": str(result.source_file_path),
        "source_file_md5": result.source_file_md5,
        "warnings": list(result.warnings),
        "is_demo": result.is_demo,
        "demo_scenario_key": result.demo_scenario_key,
        "demo_title": result.demo_title,
        "demo_description": result.demo_description,
        "validated_data": _validated_data_to_dict(result.validated_data),
        "processed_data": _processed_data_to_dict(result.processed_data),
        "spectrum": _spectrum_to_dict(result.spectrum),
        "physics": _physics_to_dict(result.physics),
        "risk": _risk_to_dict(result.risk),
        "validation": _validation_to_dict(result.validation),
    }
    return data


def analysis_result_from_dict(data: Mapping[str, Any]) -> AnalysisResult:
    """Reconstruct an analysis result from validated JSON data."""
    if data.get("_schema_version") != VIBPROJ_SCHEMA_VERSION:
        raise ValidationError(
            user_message=(
                f"Версия файла сеанса '{data.get('_schema_version', '')}' не поддерживается. "
                f"Ожидалась версия '{VIBPROJ_SCHEMA_VERSION}'."
            ),
            technical_details=f"_schema_version={data.get('_schema_version')!r}",
            recovery_hint="Создайте файл сеанса заново в текущей версии IVA.",
        )

    try:
        completed_at = datetime.fromisoformat(str(data["completed_at"]))
        if completed_at.tzinfo is None:
            completed_at = completed_at.replace(tzinfo=UTC)
        return AnalysisResult(
            session_id=str(data["session_id"]),
            completed_at=completed_at,
            source_file_path=Path(str(data["source_file_path"])),
            source_file_md5=str(data["source_file_md5"]),
            validated_data=_validated_data_from_dict(data.get("validated_data")),
            processed_data=_processed_data_from_dict(data.get("processed_data")),
            spectrum=_spectrum_from_dict(data.get("spectrum")),
            physics=_physics_from_dict(data.get("physics")),
            risk=_risk_from_dict(data.get("risk")),
            validation=_validation_from_dict(data.get("validation")),
            warnings=tuple(str(item) for item in data.get("warnings", [])),
            is_demo=bool(data.get("is_demo", False)),
            demo_scenario_key=_optional_text(data.get("demo_scenario_key")),
            demo_title=_optional_text(data.get("demo_title")),
            demo_description=_optional_text(data.get("demo_description")),
        )
    except ValidationError:
        raise
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise ValidationError(
            user_message="Файл сеанса поврежден или имеет неожиданную структуру.",
            technical_details=str(exc),
            recovery_hint="Выполните новый анализ и создайте файл сеанса повторно.",
        ) from exc


def _validated_data_to_dict(value: ValidatedSignalData | None) -> dict[str, Any] | None:
    if value is None:
        return None
    indices = _decimation_indices(min(len(value.time_array), len(value.signal_array)))
    return {
        "time_array": value.time_array[indices].tolist(),
        "signal_array": value.signal_array[indices].tolist(),
        "sampling_rate_hz": float(value.sampling_rate_hz),
        "duration_seconds": float(value.duration_seconds),
        "sample_count": int(value.sample_count),
        "signal_role": str(value.signal_role),
        "physical_unit": value.physical_unit,
        "missing_fraction": float(value.missing_fraction),
        "outlier_fraction": float(value.outlier_fraction),
        "warnings": list(value.warnings),
    }


def _validated_data_from_dict(raw: Any) -> ValidatedSignalData | None:  # noqa: ANN401
    if raw is None:
        return None
    data = _require_mapping(raw, "validated_data")
    return ValidatedSignalData(
        time_array=_float_array(data["time_array"]),
        signal_array=_float_array(data["signal_array"]),
        sampling_rate_hz=float(data["sampling_rate_hz"]),
        duration_seconds=float(data["duration_seconds"]),
        sample_count=int(data["sample_count"]),
        signal_role=SignalRole(str(data["signal_role"])),
        physical_unit=str(data["physical_unit"]),
        missing_fraction=float(data["missing_fraction"]),
        outlier_fraction=float(data["outlier_fraction"]),
        warnings=tuple(str(item) for item in data.get("warnings", [])),
    )


def _processed_data_to_dict(value: ProcessedSignalData | None) -> dict[str, Any] | None:
    if value is None:
        return None
    length = min(len(value.time_array), len(value.signal_cleaned), len(value.signal_filtered))
    indices = _decimation_indices(length)
    return {
        "time_array": value.time_array[indices].tolist(),
        "signal_cleaned": value.signal_cleaned[indices].tolist(),
        "signal_filtered": value.signal_filtered[indices].tolist(),
        "preprocessing_log": list(value.preprocessing_log),
        "applied_settings": {
            name: getattr(value.applied_settings, name)
            for name in PreprocessingSettings.__dataclass_fields__
        },
    }


def _processed_data_from_dict(raw: Any) -> ProcessedSignalData | None:  # noqa: ANN401
    if raw is None:
        return None
    data = _require_mapping(raw, "processed_data")
    settings = _require_mapping(data["applied_settings"], "applied_settings")
    return ProcessedSignalData(
        time_array=_float_array(data["time_array"]),
        signal_cleaned=_float_array(data["signal_cleaned"]),
        signal_filtered=_float_array(data["signal_filtered"]),
        preprocessing_log=tuple(str(item) for item in data.get("preprocessing_log", [])),
        applied_settings=PreprocessingSettings(**dict(settings)),
    )


def _spectrum_to_dict(value: SpectrumResult | None) -> dict[str, Any] | None:
    if value is None:
        return None
    length = min(len(value.frequencies), len(value.psd_values))
    indices = _decimation_indices(length)
    return {
        "frequencies": value.frequencies[indices].tolist(),
        "psd_values": value.psd_values[indices].tolist(),
        "rms_trend": _decimate_array(value.rms_trend),
        "rms_total": float(value.rms_total),
        "rms_in_band": _optional_number(value.rms_in_band),
        "dominant_peak": _peak_to_dict(value.dominant_peak),
        "all_peaks": [_peak_to_dict(peak) for peak in value.all_peaks],
        "applied_settings": {
            **{
                name: getattr(value.applied_settings, name)
                for name in SpectralSettings.__dataclass_fields__
                if name != "window_type"
            },
            "window_type": str(value.applied_settings.window_type),
        },
    }


def _spectrum_from_dict(raw: Any) -> SpectrumResult | None:  # noqa: ANN401
    if raw is None:
        return None
    data = _require_mapping(raw, "spectrum")
    settings_raw = dict(_require_mapping(data["applied_settings"], "applied_settings"))
    settings_raw["window_type"] = WindowType(str(settings_raw["window_type"]))
    peaks = tuple(_peak_from_dict(item) for item in data.get("all_peaks", []))
    dominant_raw = data.get("dominant_peak")
    return SpectrumResult(
        frequencies=_float_array(data["frequencies"]),
        psd_values=_float_array(data["psd_values"]),
        dominant_peak=_peak_from_dict(dominant_raw) if dominant_raw is not None else None,
        all_peaks=peaks,
        rms_total=float(data["rms_total"]),
        rms_in_band=_optional_float(data.get("rms_in_band")),
        rms_trend=_float_array(data.get("rms_trend", [])),
        applied_settings=SpectralSettings(**settings_raw),
    )


def _peak_to_dict(value: SpectralPeak | None) -> dict[str, Any] | None:
    if value is None:
        return None
    return {
        "frequency_hz": float(value.frequency_hz),
        "amplitude": float(value.amplitude),
        "width_hz_3db": float(value.width_hz_3db),
        "interpretation": str(value.interpretation),
        "confidence": float(value.confidence),
    }


def _peak_from_dict(raw: Any) -> SpectralPeak:  # noqa: ANN401
    data = _require_mapping(raw, "peak")
    return SpectralPeak(
        frequency_hz=float(data["frequency_hz"]),
        amplitude=float(data["amplitude"]),
        width_hz_3db=float(data["width_hz_3db"]),
        interpretation=PeakInterpretation(str(data["interpretation"])),
        confidence=float(data["confidence"]),
    )


def _physics_to_dict(value: PhysicsResult | None) -> dict[str, Any] | None:
    if value is None:
        return None
    return {
        "reynolds_number": float(value.reynolds_number),
        "strouhal_number": float(value.strouhal_number),
        "calculated_shedding_frequency_hz": float(value.calculated_shedding_frequency_hz),
        "velocity_ratio": _optional_number(value.velocity_ratio),
        "frequency_ratio": _optional_number(value.frequency_ratio),
        "kinematic_viscosity_m2s": float(value.kinematic_viscosity_m2s),
    }


def _physics_from_dict(raw: Any) -> PhysicsResult | None:  # noqa: ANN401
    if raw is None:
        return None
    data = _require_mapping(raw, "physics")
    return PhysicsResult(
        reynolds_number=float(data["reynolds_number"]),
        strouhal_number=float(data["strouhal_number"]),
        calculated_shedding_frequency_hz=float(data["calculated_shedding_frequency_hz"]),
        velocity_ratio=_optional_float(data.get("velocity_ratio")),
        frequency_ratio=_optional_float(data.get("frequency_ratio")),
        kinematic_viscosity_m2s=float(data["kinematic_viscosity_m2s"]),
    )


def _risk_to_dict(value: RiskAssessment | None) -> dict[str, Any] | None:
    if value is None:
        return None
    return {
        "risk_level": str(value.risk_level),
        "dominant_frequency_deviation": float(value.dominant_frequency_deviation),
        "recommendation_text": value.recommendation_text,
        "contributing_factors": list(value.contributing_factors),
    }


def _risk_from_dict(raw: Any) -> RiskAssessment | None:  # noqa: ANN401
    if raw is None:
        return None
    data = _require_mapping(raw, "risk")
    return RiskAssessment(
        risk_level=RiskLevel(str(data["risk_level"])),
        dominant_frequency_deviation=float(data["dominant_frequency_deviation"]),
        recommendation_text=str(data["recommendation_text"]),
        contributing_factors=tuple(str(item) for item in data.get("contributing_factors", [])),
    )


def _validation_to_dict(value: ValidationResult | None) -> dict[str, Any] | None:
    if value is None:
        return None
    length = min(len(value.coordinate_array), len(value.experiment_array), len(value.cfd_array))
    indices = _decimation_indices(length)
    return {
        "coordinate_array": value.coordinate_array[indices].tolist(),
        "experiment_array": value.experiment_array[indices].tolist(),
        "cfd_array": value.cfd_array[indices].tolist(),
        "rmse": float(value.rmse),
        "mae": float(value.mae),
        "mape": _optional_number(value.mape),
        "pearson_r": float(value.pearson_r),
        "is_mape_valid": bool(value.is_mape_valid),
    }


def _validation_from_dict(raw: Any) -> ValidationResult | None:  # noqa: ANN401
    if raw is None:
        return None
    data = _require_mapping(raw, "validation")
    return ValidationResult(
        coordinate_array=_float_array(data["coordinate_array"]),
        experiment_array=_float_array(data["experiment_array"]),
        cfd_array=_float_array(data["cfd_array"]),
        rmse=float(data["rmse"]),
        mae=float(data["mae"]),
        mape=_optional_float(data.get("mape")),
        pearson_r=float(data["pearson_r"]),
        is_mape_valid=bool(data["is_mape_valid"]),
    )


def _decimation_indices(length: int) -> NDArray[np.int64]:
    if length <= 0:
        return np.array([], dtype=np.int64)
    if length <= _MAX_STORED_POINTS:
        return np.arange(length, dtype=np.int64)
    return np.linspace(0, length - 1, _MAX_STORED_POINTS, dtype=np.int64)


def _decimate_array(values: NDArray[np.float64]) -> list[float]:
    array = np.asarray(values, dtype=np.float64)
    return array[_decimation_indices(len(array))].tolist()


def _require_mapping(raw: Any, label: str) -> Mapping[str, Any]:  # noqa: ANN401
    if not isinstance(raw, Mapping):
        raise TypeError(f"{label} must be an object")
    return raw


def _float_array(raw: Any) -> NDArray[np.float64]:  # noqa: ANN401
    array = np.asarray(raw, dtype=np.float64)
    if array.ndim != 1 or not np.all(np.isfinite(array)):
        raise ValueError("stored array must be one-dimensional and finite")
    return array


def _optional_number(value: float | None) -> float | None:
    return float(value) if value is not None else None


def _optional_float(value: Any) -> float | None:  # noqa: ANN401
    return float(value) if value is not None else None


def _optional_text(value: Any) -> str | None:  # noqa: ANN401
    return str(value) if value is not None else None
