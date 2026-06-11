"""Unit tests for iva.core.physics.physics_result_builder."""

from __future__ import annotations

import pytest

from iva.core.models.analysis_result import PhysicsResult
from iva.core.models.enums import GeometryType
from iva.core.models.exceptions import PhysicsInputError
from iva.core.models.flow_parameters import FlowParameters
from iva.core.physics.physics_result_builder import build_physics_result

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_SINGLE_COMPLETE = FlowParameters(
    cylinder_diameter_m=0.012,
    mean_flow_velocity_ms=2.0,
    fluid_density_kgm3=998.0,
    dynamic_viscosity_pas=1.002e-3,
    geometry_type=GeometryType.SINGLE_CYLINDER,
    natural_frequency_hz=40.0,
)

_SINGLE_NO_FN = FlowParameters(
    cylinder_diameter_m=0.012,
    mean_flow_velocity_ms=2.0,
    fluid_density_kgm3=998.0,
    dynamic_viscosity_pas=1.002e-3,
    geometry_type=GeometryType.SINGLE_CYLINDER,
    natural_frequency_hz=None,
)

_TANDEM_COMPLETE = FlowParameters(
    cylinder_diameter_m=0.012,
    mean_flow_velocity_ms=2.0,
    fluid_density_kgm3=998.0,
    dynamic_viscosity_pas=1.002e-3,
    geometry_type=GeometryType.TANDEM,
    natural_frequency_hz=40.0,
    cylinder_spacing_m=0.030,  # L/D = 2.5
)

_TANDEM_NO_SPACING = FlowParameters(
    cylinder_diameter_m=0.012,
    mean_flow_velocity_ms=2.0,
    fluid_density_kgm3=998.0,
    dynamic_viscosity_pas=1.002e-3,
    geometry_type=GeometryType.TANDEM,
    cylinder_spacing_m=None,
)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestBuildPhysicsResult:

    def test_returns_physics_result(self) -> None:
        result = build_physics_result(_SINGLE_COMPLETE)
        assert isinstance(result, PhysicsResult)

    def test_reynolds_number_plausible(self) -> None:
        result = build_physics_result(_SINGLE_COMPLETE)
        # Re = 998 * 2.0 * 0.012 / 1.002e-3 ≈ 23904
        assert abs(result.reynolds_number - 23904.0) / 23904.0 < 0.01

    def test_strouhal_plausible(self) -> None:
        result = build_physics_result(_SINGLE_COMPLETE)
        assert 0.15 <= result.strouhal_number <= 0.25

    def test_shedding_frequency_plausible(self) -> None:
        result = build_physics_result(_SINGLE_COMPLETE)
        assert result.calculated_shedding_frequency_hz > 0.0

    def test_kinematic_viscosity_set(self) -> None:
        result = build_physics_result(_SINGLE_COMPLETE)
        expected_nu = 1.002e-3 / 998.0
        assert abs(result.kinematic_viscosity_m2s - expected_nu) < 1e-15

    def test_velocity_ratio_not_none_with_fn(self) -> None:
        result = build_physics_result(_SINGLE_COMPLETE)
        assert result.velocity_ratio is not None

    def test_frequency_ratio_not_none_with_fn(self) -> None:
        result = build_physics_result(_SINGLE_COMPLETE)
        assert result.frequency_ratio is not None

    def test_velocity_ratio_none_without_fn(self) -> None:
        result = build_physics_result(_SINGLE_NO_FN)
        assert result.velocity_ratio is None

    def test_frequency_ratio_none_without_fn(self) -> None:
        result = build_physics_result(_SINGLE_NO_FN)
        assert result.frequency_ratio is None

    def test_tandem_with_spacing(self) -> None:
        result = build_physics_result(_TANDEM_COMPLETE)
        assert isinstance(result, PhysicsResult)
        assert result.strouhal_number > 0.0

    def test_tandem_without_spacing_raises(self) -> None:
        with pytest.raises(PhysicsInputError):
            build_physics_result(_TANDEM_NO_SPACING)

    def test_missing_diameter_raises(self) -> None:
        fp = FlowParameters(
            cylinder_diameter_m=None,
            mean_flow_velocity_ms=2.0,
            fluid_density_kgm3=998.0,
            dynamic_viscosity_pas=1.002e-3,
            geometry_type=GeometryType.SINGLE_CYLINDER,
        )
        with pytest.raises(PhysicsInputError):
            build_physics_result(fp)

    def test_missing_velocity_raises(self) -> None:
        fp = FlowParameters(
            cylinder_diameter_m=0.012,
            mean_flow_velocity_ms=None,
            fluid_density_kgm3=998.0,
            dynamic_viscosity_pas=1.002e-3,
            geometry_type=GeometryType.SINGLE_CYLINDER,
        )
        with pytest.raises(PhysicsInputError):
            build_physics_result(fp)
