"""Vortex shedding frequency, velocity ratio, and frequency ratio calculations.

All inputs are in SI units.
"""

from __future__ import annotations

import logging

from iva.core.models.exceptions import PhysicsInputError

logger = logging.getLogger(__name__)

__all__ = [
    "calculate_shedding_frequency",
    "calculate_velocity_ratio",
    "calculate_frequency_ratio",
]


def calculate_shedding_frequency(
    strouhal_number: float,
    velocity_ms: float,
    diameter_m: float,
) -> float:
    """Return vortex shedding frequency ``fs = St * V / D`` in Hz.

    Numerical test:
        St=0.21, V=2.0 m/s, D=0.012 m → fs = 35.0 Hz.

    Parameters
    ----------
    strouhal_number:
        Dimensionless Strouhal number.  Must be > 0.
    velocity_ms:
        Mean flow velocity, m/s.  Must be > 0.
    diameter_m:
        Cylinder diameter, m.  Must be > 0.

    Raises
    ------
    PhysicsInputError
        If any parameter is non-positive.
    """
    if strouhal_number <= 0.0:
        raise PhysicsInputError(
            user_message="Число Струхаля должно быть больше нуля.",
            technical_details=f"strouhal_number={strouhal_number!r} is not > 0",
        )
    if velocity_ms <= 0.0:
        raise PhysicsInputError(
            user_message="Скорость потока должна быть больше нуля.",
            technical_details=f"velocity_ms={velocity_ms!r} is not > 0",
            recovery_hint="Введите положительное значение скорости (м/с).",
        )
    if diameter_m <= 0.0:
        raise PhysicsInputError(
            user_message="Диаметр цилиндра должен быть больше нуля.",
            technical_details=f"diameter_m={diameter_m!r} is not > 0",
            recovery_hint="Введите положительное значение диаметра (м).",
        )

    fs: float = strouhal_number * velocity_ms / diameter_m
    logger.debug(
        "Shedding frequency fs = %.4f Hz (St=%.4f, V=%.4f m/s, D=%.4f m)",
        fs,
        strouhal_number,
        velocity_ms,
        diameter_m,
    )
    return fs


def calculate_velocity_ratio(
    velocity_ms: float,
    natural_frequency_hz: float | None,
    diameter_m: float,
) -> float | None:
    """Return reduced (velocity) ratio ``Vr = V / (fn * D)``, or ``None``.

    Returns ``None`` when ``natural_frequency_hz`` is ``None`` (i.e. the
    user has not specified the structural natural frequency).

    Parameters
    ----------
    velocity_ms:
        Mean flow velocity, m/s.  Must be ≥ 0.
    natural_frequency_hz:
        Structural natural frequency, Hz.  Must be > 0 if not ``None``.
    diameter_m:
        Cylinder diameter, m.  Must be > 0.

    Raises
    ------
    PhysicsInputError
        If ``velocity_ms`` < 0, ``diameter_m`` ≤ 0, or
        ``natural_frequency_hz`` is provided but ≤ 0.
    """
    if natural_frequency_hz is None:
        return None

    if velocity_ms < 0.0:
        raise PhysicsInputError(
            user_message="Скорость потока не может быть отрицательной.",
            technical_details=f"velocity_ms={velocity_ms!r} < 0",
        )
    if natural_frequency_hz <= 0.0:
        raise PhysicsInputError(
            user_message="Собственная частота конструкции должна быть больше нуля.",
            technical_details=f"natural_frequency_hz={natural_frequency_hz!r} is not > 0",
            recovery_hint="Введите положительное значение собственной частоты (Гц).",
        )
    if diameter_m <= 0.0:
        raise PhysicsInputError(
            user_message="Диаметр цилиндра должен быть больше нуля.",
            technical_details=f"diameter_m={diameter_m!r} is not > 0",
        )

    vr: float = velocity_ms / (natural_frequency_hz * diameter_m)
    return vr


def calculate_frequency_ratio(
    shedding_frequency_hz: float,
    natural_frequency_hz: float | None,
) -> float | None:
    """Return frequency ratio ``fr = fs / fn``, or ``None``.

    Returns ``None`` when ``natural_frequency_hz`` is ``None``.

    Parameters
    ----------
    shedding_frequency_hz:
        Calculated vortex shedding frequency, Hz.  Must be ≥ 0.
    natural_frequency_hz:
        Structural natural frequency, Hz.  Must be > 0 if not ``None``.

    Raises
    ------
    PhysicsInputError
        If ``shedding_frequency_hz`` < 0 or ``natural_frequency_hz`` ≤ 0.
    """
    if natural_frequency_hz is None:
        return None

    if shedding_frequency_hz < 0.0:
        raise PhysicsInputError(
            user_message="Частота срыва вихрей не может быть отрицательной.",
            technical_details=f"shedding_frequency_hz={shedding_frequency_hz!r} < 0",
        )
    if natural_frequency_hz <= 0.0:
        raise PhysicsInputError(
            user_message="Собственная частота конструкции должна быть больше нуля.",
            technical_details=f"natural_frequency_hz={natural_frequency_hz!r} is not > 0",
            recovery_hint="Введите положительное значение собственной частоты (Гц).",
        )

    fr: float = shedding_frequency_hz / natural_frequency_hz
    return fr
