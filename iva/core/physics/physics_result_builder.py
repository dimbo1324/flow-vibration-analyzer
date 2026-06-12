"""Сборка полного PhysicsResult из проверенных FlowParameters.

Модуль является единственной точкой сборки физических расчётов и делегирует
формулы специализированным калькуляторам. Оценка риска выполняется позже в
``lock_in_risk.assess_risk`` и намеренно не смешивается с вычислением величин.
"""

from __future__ import annotations

import logging

from iva.core.models.analysis_result import PhysicsResult
from iva.core.models.enums import GeometryType
from iva.core.models.exceptions import PhysicsInputError
from iva.core.models.flow_parameters import FlowParameters
from iva.core.physics.reynolds_calculator import (
    calculate_kinematic_viscosity,
    calculate_reynolds_number,
)
from iva.core.physics.strouhal_calculator import get_strouhal_number
from iva.core.physics.vortex_frequency import (
    calculate_frequency_ratio,
    calculate_shedding_frequency,
    calculate_velocity_ratio,
)

logger = logging.getLogger(__name__)

__all__ = ["build_physics_result"]


def build_physics_result(flow_parameters: FlowParameters) -> PhysicsResult:
    """Рассчитать физические характеристики потока и вернуть PhysicsResult.

    Required fields (raises PhysicsInputError if any are None or invalid):
    - ``cylinder_diameter_m``
    - ``mean_flow_velocity_ms``
    - ``fluid_density_kgm3``
    - ``dynamic_viscosity_pas``
    - ``geometry_type``

    Optional fields (used when present):
    - ``natural_frequency_hz`` — enables velocity_ratio and frequency_ratio
    - ``cylinder_spacing_m``   — required for TANDEM geometry

    Parameters
    ----------
    flow_parameters:
        User-supplied flow and geometry parameters (all SI units).

    Returns
    -------
    PhysicsResult
        Fully populated dimensionless and dimensional flow characterisation.

    Raises
    ------
    PhysicsInputError
        If any required field is missing or physically invalid, or if
        TANDEM geometry is selected but ``cylinder_spacing_m`` is not set.
    """
    # Обязательные поля проверяются до любой формулы, чтобы частичный результат
    # никогда не покидал слой core.
    _require_field(flow_parameters.cylinder_diameter_m, "cylinder_diameter_m")
    _require_field(flow_parameters.mean_flow_velocity_ms, "mean_flow_velocity_ms")
    _require_field(flow_parameters.fluid_density_kgm3, "fluid_density_kgm3")
    _require_field(flow_parameters.dynamic_viscosity_pas, "dynamic_viscosity_pas")
    _require_field(flow_parameters.geometry_type, "geometry_type")

    # После проверки mypy и формулы могут считать эти значения не-None.
    diameter: float = flow_parameters.cylinder_diameter_m  # type: ignore[assignment]
    velocity: float = flow_parameters.mean_flow_velocity_ms  # type: ignore[assignment]
    density: float = flow_parameters.fluid_density_kgm3  # type: ignore[assignment]
    viscosity: float = flow_parameters.dynamic_viscosity_pas  # type: ignore[assignment]
    geometry: GeometryType = flow_parameters.geometry_type  # type: ignore[assignment]

    # Для тандемной схемы отношение шага определяет выбор таблицы Струхаля.
    spacing_ratio: float | None = None
    if geometry == GeometryType.TANDEM:
        if flow_parameters.cylinder_spacing_m is None:
            raise PhysicsInputError(
                user_message=(
                    "Для конфигурации 'тандем' необходимо задать расстояние "
                    "между цилиндрами (cylinder_spacing_m)."
                ),
                technical_details="cylinder_spacing_m is None for TANDEM geometry",
                recovery_hint="Введите значение расстояния между цилиндрами (м).",
            )
        spacing_ratio = flow_parameters.cylinder_spacing_m / diameter

    # Формулы выполняются в порядке, описанном в научной методологии.
    nu = calculate_kinematic_viscosity(density, viscosity)
    re = calculate_reynolds_number(velocity, diameter, density, viscosity)
    st = get_strouhal_number(re, geometry, spacing_ratio)
    fs = calculate_shedding_frequency(st, velocity, diameter)

    fn = flow_parameters.natural_frequency_hz
    vr = calculate_velocity_ratio(velocity, fn, diameter)
    fr = calculate_frequency_ratio(fs, fn)

    logger.info(
        "PhysicsResult built: Re=%.2e, St=%.4f, fs=%.4f Hz, Vr=%s, fr=%s",
        re,
        st,
        fs,
        f"{vr:.4f}" if vr is not None else "None",
        f"{fr:.4f}" if fr is not None else "None",
    )

    return PhysicsResult(
        reynolds_number=re,
        strouhal_number=st,
        calculated_shedding_frequency_hz=fs,
        velocity_ratio=vr,
        frequency_ratio=fr,
        kinematic_viscosity_m2s=nu,
    )


# ---------------------------------------------------------------------------
# Вспомогательная проверка обязательных полей
# ---------------------------------------------------------------------------


def _require_field(value: object, name: str) -> None:
    if value is None:
        raise PhysicsInputError(
            user_message=f"Обязательный параметр '{name}' не задан.",
            technical_details=f"FlowParameters.{name} is None",
            recovery_hint=f"Введите значение '{name}' в форму параметров течения.",
        )
