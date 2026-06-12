"""Typed built-in scenarios for product demonstrations and teaching."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from iva.core.models.enums import GeometryType, SignalRole, WindowType
from iva.core.models.exceptions import ValidationError
from iva.core.models.flow_parameters import FlowParameters
from iva.core.models.settings import PreprocessingSettings, SpectralSettings
from iva.core.synthetic.generators import (
    generate_clean_sine,
    generate_noisy_sine,
    generate_risk_scenario,
    generate_with_gaps,
    generate_with_harmonics,
    generate_with_outliers,
)

__all__ = [
    "DemoScenario",
    "list_demo_scenarios",
    "get_demo_scenario",
    "generate_demo_signal",
]

DemoGeneratorKind = Literal["clean", "noisy", "harmonics", "outliers", "gaps", "risk"]


@dataclass(frozen=True)
class DemoScenario:
    """Configuration and Russian presentation metadata for one demo scenario."""

    key: str
    title_ru: str
    description_ru: str
    expected_peak_hz: float | None
    sampling_rate_hz: float
    duration_s: float
    signal_role: SignalRole
    flow_parameters: FlowParameters
    preprocessing_settings: PreprocessingSettings
    spectral_settings: SpectralSettings
    generator_kind: DemoGeneratorKind


_SAMPLING_RATE_HZ = 1000.0
_DURATION_S = 8.0


def _flow_parameters(natural_frequency_hz: float) -> FlowParameters:
    return FlowParameters(
        cylinder_diameter_m=0.010,
        mean_flow_velocity_ms=2.0,
        fluid_density_kgm3=998.0,
        dynamic_viscosity_pas=0.001002,
        natural_frequency_hz=natural_frequency_hz,
        damping_ratio=0.02,
        cylinder_spacing_m=None,
        geometry_type=GeometryType.SINGLE_CYLINDER,
    )


def _preprocessing() -> PreprocessingSettings:
    return PreprocessingSettings(
        remove_mean=True,
        remove_outliers=True,
        outlier_window_samples=21,
        outlier_threshold_sigma=4.0,
        fill_gaps=True,
        max_gap_ms=50.0,
        apply_bandpass_filter=True,
        filter_low_hz=5.0,
        filter_high_hz=200.0,
        filter_order=4,
    )


def _spectral() -> SpectralSettings:
    return SpectralSettings(
        window_type=WindowType.HANN,
        segment_length_samples=1024,
        overlap_fraction=0.5,
        peak_detection_threshold_db=10.0,
        peak_min_width_hz=0.5,
        rms_band_low_hz=5.0,
        rms_band_high_hz=200.0,
        rms_window_seconds=1.0,
    )


_SCENARIOS: tuple[DemoScenario, ...] = (
    DemoScenario(
        key="clean_40hz",
        title_ru="Чистый сигнал 40 Гц",
        description_ru="Чистая синусоида для быстрого знакомства со спектром и расчетным циклом.",
        expected_peak_hz=40.0,
        sampling_rate_hz=_SAMPLING_RATE_HZ,
        duration_s=_DURATION_S,
        signal_role=SignalRole.ACCELERATION_X,
        flow_parameters=_flow_parameters(60.0),
        preprocessing_settings=_preprocessing(),
        spectral_settings=_spectral(),
        generator_kind="clean",
    ),
    DemoScenario(
        key="noisy_40hz",
        title_ru="Сигнал 40 Гц с шумом",
        description_ru="Синусоида с гауссовым шумом, имитирующая типовую запись датчика.",
        expected_peak_hz=40.0,
        sampling_rate_hz=_SAMPLING_RATE_HZ,
        duration_s=_DURATION_S,
        signal_role=SignalRole.ACCELERATION_X,
        flow_parameters=_flow_parameters(60.0),
        preprocessing_settings=_preprocessing(),
        spectral_settings=_spectral(),
        generator_kind="noisy",
    ),
    DemoScenario(
        key="harmonics_40hz",
        title_ru="Сигнал с гармониками",
        description_ru="Основной тон 40 Гц и гармоники около 80 и 120 Гц.",
        expected_peak_hz=40.0,
        sampling_rate_hz=_SAMPLING_RATE_HZ,
        duration_s=_DURATION_S,
        signal_role=SignalRole.ACCELERATION_X,
        flow_parameters=_flow_parameters(60.0),
        preprocessing_settings=_preprocessing(),
        spectral_settings=_spectral(),
        generator_kind="harmonics",
    ),
    DemoScenario(
        key="outliers_40hz",
        title_ru="Сигнал с выбросами",
        description_ru="Сигнал 40 Гц с одиночными импульсными выбросами для демонстрации очистки.",
        expected_peak_hz=40.0,
        sampling_rate_hz=_SAMPLING_RATE_HZ,
        duration_s=_DURATION_S,
        signal_role=SignalRole.ACCELERATION_X,
        flow_parameters=_flow_parameters(60.0),
        preprocessing_settings=_preprocessing(),
        spectral_settings=_spectral(),
        generator_kind="outliers",
    ),
    DemoScenario(
        key="gaps_40hz",
        title_ru="Сигнал с пропусками",
        description_ru=(
            "Сигнал 40 Гц с пропущенными отсчетами для демонстрации заполнения разрывов."
        ),
        expected_peak_hz=40.0,
        sampling_rate_hz=_SAMPLING_RATE_HZ,
        duration_s=_DURATION_S,
        signal_role=SignalRole.ACCELERATION_X,
        flow_parameters=_flow_parameters(60.0),
        preprocessing_settings=_preprocessing(),
        spectral_settings=_spectral(),
        generator_kind="gaps",
    ),
    DemoScenario(
        key="critical_risk",
        title_ru="Опасный режим: близко к резонансу",
        description_ru=(
            "Частота срыва близка к собственной частоте конструкции, "
            "поэтому расчет показывает повышенный риск."
        ),
        expected_peak_hz=40.5,
        sampling_rate_hz=_SAMPLING_RATE_HZ,
        duration_s=_DURATION_S,
        signal_role=SignalRole.ACCELERATION_X,
        flow_parameters=_flow_parameters(40.0),
        preprocessing_settings=_preprocessing(),
        spectral_settings=_spectral(),
        generator_kind="risk",
    ),
)


def list_demo_scenarios() -> tuple[DemoScenario, ...]:
    """Return all built-in scenarios in stable display order."""
    return _SCENARIOS


def get_demo_scenario(key: str) -> DemoScenario:
    """Return a scenario by key or raise a user-facing validation error."""
    for scenario in _SCENARIOS:
        if scenario.key == key:
            return scenario
    raise ValidationError(
        user_message=f"Неизвестный демонстрационный сценарий: '{key}'.",
        technical_details=f"Known scenario keys: {[item.key for item in _SCENARIOS]}",
        recovery_hint="Выберите сценарий из списка доступных демонстраций.",
    )


def generate_demo_signal(
    key: str,
) -> tuple[DemoScenario, dict[str, NDArray[np.float64]]]:
    """Generate the two standard demo columns for a built-in scenario."""
    scenario = get_demo_scenario(key)
    common = (
        scenario.duration_s,
        scenario.sampling_rate_hz,
        1.0,
    )
    if scenario.generator_kind == "clean":
        time_s, signal = generate_clean_sine(40.0, *common)
    elif scenario.generator_kind == "noisy":
        time_s, signal = generate_noisy_sine(40.0, *common, snr_db=15.0, seed=42)
    elif scenario.generator_kind == "harmonics":
        time_s, signal = generate_with_harmonics(40.0, *common, n_harmonics=3)
    elif scenario.generator_kind == "outliers":
        time_s, signal = generate_clean_sine(40.0, *common)
        signal = generate_with_outliers(signal, n_outliers=20, magnitude=6.0, seed=42)
    elif scenario.generator_kind == "gaps":
        time_s, signal = generate_clean_sine(40.0, *common)
        signal = generate_with_gaps(signal, gap_fraction=0.02, seed=42)
    else:
        time_s, signal = generate_risk_scenario(40.5, 40.0, *common, seed=42)
    return scenario, {"time_s": time_s, "signal": signal}
