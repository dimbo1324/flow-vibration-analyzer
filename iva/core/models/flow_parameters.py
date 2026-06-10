"""Flow and geometry parameter container.

All values are in SI units.  Optional fields default to ``None`` so that the
application can hold a partially completed form without raising errors before
the user has finished data entry.
"""

from __future__ import annotations

from dataclasses import dataclass

from iva.core.models.enums import GeometryType

__all__ = ["FlowParameters"]


@dataclass(frozen=True)
class FlowParameters:
    """Physical parameters of the flow and geometry entered by the user.

    Mandatory fields (cylinder_diameter_m, mean_flow_velocity_ms,
    fluid_density_kgm3, dynamic_viscosity_pas) must be provided for the
    physics calculation step.  The remaining fields are optional and only
    affect risk assessment and tandem-cylinder Strouhal estimation.
    """

    cylinder_diameter_m: float | None = None
    mean_flow_velocity_ms: float | None = None
    fluid_density_kgm3: float | None = None
    dynamic_viscosity_pas: float | None = None
    natural_frequency_hz: float | None = None
    damping_ratio: float | None = None
    cylinder_spacing_m: float | None = None
    geometry_type: GeometryType | None = None
