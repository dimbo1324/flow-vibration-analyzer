"""Unit tests for iva.core.physics.reynolds_calculator."""

from __future__ import annotations

import pytest

from iva.core.models.exceptions import PhysicsInputError
from iva.core.physics.reynolds_calculator import (
    calculate_kinematic_viscosity,
    calculate_reynolds_number,
)


class TestCalculateReynoldsNumber:
    """Tests for calculate_reynolds_number."""

    def test_analytical_value(self) -> None:
        """V=2.0 m/s, D=0.012 m, rho=998 kg/m³, mu=1.002e-3 Pa·s → Re ≈ 23904."""
        re = calculate_reynolds_number(
            velocity_ms=2.0,
            diameter_m=0.012,
            density_kgm3=998.0,
            dynamic_viscosity_pas=1.002e-3,
        )
        expected = 998.0 * 2.0 * 0.012 / 1.002e-3  # ≈ 23904.19
        assert abs(re - expected) / expected < 1e-3, f"Expected Re ≈ {expected:.1f}, got {re:.1f}"

    def test_diameter_zero_raises(self) -> None:
        with pytest.raises(PhysicsInputError):
            calculate_reynolds_number(
                velocity_ms=1.0,
                diameter_m=0.0,
                density_kgm3=1.0,
                dynamic_viscosity_pas=1e-3,
            )

    def test_diameter_negative_raises(self) -> None:
        with pytest.raises(PhysicsInputError):
            calculate_reynolds_number(
                velocity_ms=1.0,
                diameter_m=-0.01,
                density_kgm3=1.0,
                dynamic_viscosity_pas=1e-3,
            )

    def test_density_zero_raises(self) -> None:
        with pytest.raises(PhysicsInputError):
            calculate_reynolds_number(
                velocity_ms=1.0,
                diameter_m=0.01,
                density_kgm3=0.0,
                dynamic_viscosity_pas=1e-3,
            )

    def test_density_negative_raises(self) -> None:
        with pytest.raises(PhysicsInputError):
            calculate_reynolds_number(
                velocity_ms=1.0,
                diameter_m=0.01,
                density_kgm3=-1.0,
                dynamic_viscosity_pas=1e-3,
            )

    def test_viscosity_zero_raises(self) -> None:
        with pytest.raises(PhysicsInputError):
            calculate_reynolds_number(
                velocity_ms=1.0,
                diameter_m=0.01,
                density_kgm3=1.0,
                dynamic_viscosity_pas=0.0,
            )

    def test_viscosity_negative_raises(self) -> None:
        with pytest.raises(PhysicsInputError):
            calculate_reynolds_number(
                velocity_ms=1.0,
                diameter_m=0.01,
                density_kgm3=1.0,
                dynamic_viscosity_pas=-1e-3,
            )

    def test_negative_velocity_raises(self) -> None:
        with pytest.raises(PhysicsInputError):
            calculate_reynolds_number(
                velocity_ms=-1.0,
                diameter_m=0.01,
                density_kgm3=1.0,
                dynamic_viscosity_pas=1e-3,
            )

    def test_zero_velocity_allowed(self) -> None:
        """Zero velocity is physically valid (stagnant flow)."""
        re = calculate_reynolds_number(
            velocity_ms=0.0,
            diameter_m=0.01,
            density_kgm3=1.0,
            dynamic_viscosity_pas=1e-3,
        )
        assert re == 0.0


class TestCalculateKinematicViscosity:
    """Tests for calculate_kinematic_viscosity."""

    def test_formula(self) -> None:
        nu = calculate_kinematic_viscosity(rho=998.0, mu=1.002e-3)
        assert abs(nu - 1.002e-3 / 998.0) < 1e-15

    def test_rho_zero_raises(self) -> None:
        with pytest.raises(PhysicsInputError):
            calculate_kinematic_viscosity(rho=0.0, mu=1e-3)

    def test_rho_negative_raises(self) -> None:
        with pytest.raises(PhysicsInputError):
            calculate_kinematic_viscosity(rho=-1.0, mu=1e-3)

    def test_mu_zero_raises(self) -> None:
        with pytest.raises(PhysicsInputError):
            calculate_kinematic_viscosity(rho=1.0, mu=0.0)

    def test_mu_negative_raises(self) -> None:
        with pytest.raises(PhysicsInputError):
            calculate_kinematic_viscosity(rho=1.0, mu=-1e-3)
