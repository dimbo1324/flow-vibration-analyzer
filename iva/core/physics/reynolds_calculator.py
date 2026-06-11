"""Reynolds number calculation for cylindrical flow geometries.

All inputs and outputs are in SI units.
"""

from __future__ import annotations

import logging

from iva.core.models.exceptions import PhysicsInputError

logger = logging.getLogger(__name__)

__all__ = [
    "calculate_kinematic_viscosity",
    "calculate_reynolds_number",
]


def calculate_kinematic_viscosity(rho: float, mu: float) -> float:
    """Return kinematic viscosity ``nu = mu / rho`` in m²/s.

    Parameters
    ----------
    rho:
        Fluid density, kg/m³.  Must be strictly positive.
    mu:
        Dynamic viscosity, Pa·s.  Must be strictly positive.

    Raises
    ------
    PhysicsInputError
        If ``rho`` or ``mu`` are non-positive.
    """
    if rho <= 0.0:
        raise PhysicsInputError(
            user_message="Плотность жидкости должна быть больше нуля.",
            technical_details=f"rho={rho!r} is not > 0",
            recovery_hint="Введите положительное значение плотности (кг/м³).",
        )
    if mu <= 0.0:
        raise PhysicsInputError(
            user_message="Динамическая вязкость должна быть больше нуля.",
            technical_details=f"mu={mu!r} is not > 0",
            recovery_hint="Введите положительное значение динамической вязкости (Па·с).",
        )
    nu: float = mu / rho
    return nu


def calculate_reynolds_number(
    velocity_ms: float,
    diameter_m: float,
    density_kgm3: float,
    dynamic_viscosity_pas: float,
) -> float:
    """Return the Reynolds number ``Re = rho * V * D / mu``.

    Numerical test:
        V=2.0 m/s, D=0.012 m, rho=998 kg/m³, mu=1.002e-3 Pa·s → Re ≈ 23904.

    Parameters
    ----------
    velocity_ms:
        Mean flow velocity, m/s.  Must be ≥ 0.
    diameter_m:
        Cylinder diameter, m.  Must be strictly positive.
    density_kgm3:
        Fluid density, kg/m³.  Must be strictly positive.
    dynamic_viscosity_pas:
        Dynamic viscosity, Pa·s.  Must be strictly positive.

    Raises
    ------
    PhysicsInputError
        If any of the positivity constraints are violated, or if
        ``velocity_ms`` is negative.
    """
    if velocity_ms < 0.0:
        raise PhysicsInputError(
            user_message="Скорость потока не может быть отрицательной.",
            technical_details=f"velocity_ms={velocity_ms!r} < 0",
            recovery_hint="Введите неотрицательное значение скорости (м/с).",
        )
    if diameter_m <= 0.0:
        raise PhysicsInputError(
            user_message="Диаметр цилиндра должен быть больше нуля.",
            technical_details=f"diameter_m={diameter_m!r} is not > 0",
            recovery_hint="Введите положительное значение диаметра (м).",
        )
    if density_kgm3 <= 0.0:
        raise PhysicsInputError(
            user_message="Плотность жидкости должна быть больше нуля.",
            technical_details=f"density_kgm3={density_kgm3!r} is not > 0",
            recovery_hint="Введите положительное значение плотности (кг/м³).",
        )
    if dynamic_viscosity_pas <= 0.0:
        raise PhysicsInputError(
            user_message="Динамическая вязкость должна быть больше нуля.",
            technical_details=f"dynamic_viscosity_pas={dynamic_viscosity_pas!r} is not > 0",
            recovery_hint="Введите положительное значение динамической вязкости (Па·с).",
        )

    re: float = density_kgm3 * velocity_ms * diameter_m / dynamic_viscosity_pas
    logger.info("Reynolds number Re = %.2e", re)
    return re
