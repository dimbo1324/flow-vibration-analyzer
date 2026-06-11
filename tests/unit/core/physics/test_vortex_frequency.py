"""Unit tests for iva.core.physics.vortex_frequency."""

from __future__ import annotations

import pytest

from iva.core.models.exceptions import PhysicsInputError
from iva.core.physics.vortex_frequency import (
    calculate_frequency_ratio,
    calculate_shedding_frequency,
    calculate_velocity_ratio,
)


class TestCalculateSheddingFrequency:
    """Tests for calculate_shedding_frequency."""

    def test_analytical_value(self) -> None:
        """St=0.21, V=2.0 m/s, D=0.012 m → fs = 35.0 Hz."""
        fs = calculate_shedding_frequency(strouhal_number=0.21, velocity_ms=2.0, diameter_m=0.012)
        assert abs(fs - 35.0) < 1e-9

    def test_diameter_zero_raises(self) -> None:
        with pytest.raises(PhysicsInputError):
            calculate_shedding_frequency(0.21, 2.0, 0.0)

    def test_diameter_negative_raises(self) -> None:
        with pytest.raises(PhysicsInputError):
            calculate_shedding_frequency(0.21, 2.0, -0.01)

    def test_velocity_zero_raises(self) -> None:
        with pytest.raises(PhysicsInputError):
            calculate_shedding_frequency(0.21, 0.0, 0.012)

    def test_velocity_negative_raises(self) -> None:
        with pytest.raises(PhysicsInputError):
            calculate_shedding_frequency(0.21, -1.0, 0.012)

    def test_strouhal_zero_raises(self) -> None:
        with pytest.raises(PhysicsInputError):
            calculate_shedding_frequency(0.0, 2.0, 0.012)


class TestCalculateVelocityRatio:
    """Tests for calculate_velocity_ratio."""

    def test_formula(self) -> None:
        vr = calculate_velocity_ratio(velocity_ms=2.0, natural_frequency_hz=40.0, diameter_m=0.012)
        assert vr is not None
        expected = 2.0 / (40.0 * 0.012)  # ≈ 4.1667
        assert abs(vr - expected) < 1e-9

    def test_returns_none_when_fn_is_none(self) -> None:
        vr = calculate_velocity_ratio(velocity_ms=2.0, natural_frequency_hz=None, diameter_m=0.012)
        assert vr is None

    def test_fn_zero_raises(self) -> None:
        with pytest.raises(PhysicsInputError):
            calculate_velocity_ratio(velocity_ms=2.0, natural_frequency_hz=0.0, diameter_m=0.012)

    def test_fn_negative_raises(self) -> None:
        with pytest.raises(PhysicsInputError):
            calculate_velocity_ratio(velocity_ms=2.0, natural_frequency_hz=-10.0, diameter_m=0.012)

    def test_diameter_zero_raises(self) -> None:
        with pytest.raises(PhysicsInputError):
            calculate_velocity_ratio(velocity_ms=2.0, natural_frequency_hz=40.0, diameter_m=0.0)

    def test_negative_velocity_raises(self) -> None:
        with pytest.raises(PhysicsInputError):
            calculate_velocity_ratio(velocity_ms=-1.0, natural_frequency_hz=40.0, diameter_m=0.012)


class TestCalculateFrequencyRatio:
    """Tests for calculate_frequency_ratio."""

    def test_formula(self) -> None:
        fr = calculate_frequency_ratio(shedding_frequency_hz=35.0, natural_frequency_hz=40.0)
        assert fr is not None
        assert abs(fr - 35.0 / 40.0) < 1e-9

    def test_returns_none_when_fn_is_none(self) -> None:
        fr = calculate_frequency_ratio(shedding_frequency_hz=35.0, natural_frequency_hz=None)
        assert fr is None

    def test_fn_zero_raises(self) -> None:
        with pytest.raises(PhysicsInputError):
            calculate_frequency_ratio(shedding_frequency_hz=35.0, natural_frequency_hz=0.0)

    def test_fn_negative_raises(self) -> None:
        with pytest.raises(PhysicsInputError):
            calculate_frequency_ratio(shedding_frequency_hz=35.0, natural_frequency_hz=-10.0)

    def test_negative_fs_raises(self) -> None:
        with pytest.raises(PhysicsInputError):
            calculate_frequency_ratio(shedding_frequency_hz=-1.0, natural_frequency_hz=40.0)
