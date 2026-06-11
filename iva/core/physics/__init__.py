"""Public API for the IVA physics calculation layer.

All functions accept SI-unit inputs and return typed results from
``iva.core.models``.  No imports from ``iva.ui``, ``iva.app``, or
``iva.infrastructure`` are permitted inside this package.
"""

from __future__ import annotations

from iva.core.physics.lock_in_risk import assess_risk
from iva.core.physics.physics_result_builder import build_physics_result
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

__all__ = [
    "calculate_reynolds_number",
    "calculate_kinematic_viscosity",
    "get_strouhal_number",
    "calculate_shedding_frequency",
    "calculate_velocity_ratio",
    "calculate_frequency_ratio",
    "build_physics_result",
    "assess_risk",
]
