"""Unit tests for iva.core.physics.strouhal_calculator."""

from __future__ import annotations

import logging

import pytest

from iva.core.models.enums import GeometryType
from iva.core.models.exceptions import PhysicsInputError
from iva.core.physics.strouhal_calculator import get_strouhal_number


class TestSingleCylinder:
    """Tests for SINGLE_CYLINDER Strouhal interpolation."""

    def test_plausible_range(self) -> None:
        """Strouhal number for single cylinder at typical Re should be in [0.15, 0.25]."""
        st = get_strouhal_number(20000.0, GeometryType.SINGLE_CYLINDER)
        assert 0.15 <= st <= 0.25, f"St={st} out of expected range [0.15, 0.25]"

    def test_deterministic(self) -> None:
        """Same input always returns the same result."""
        st1 = get_strouhal_number(10000.0, GeometryType.SINGLE_CYLINDER)
        st2 = get_strouhal_number(10000.0, GeometryType.SINGLE_CYLINDER)
        assert st1 == st2

    def test_negative_re_raises(self) -> None:
        with pytest.raises(PhysicsInputError):
            get_strouhal_number(-100.0, GeometryType.SINGLE_CYLINDER)

    def test_out_of_range_low_re_clamps(self, caplog: pytest.LogCaptureFixture) -> None:
        """Re below table minimum should clamp and issue a WARNING."""
        with caplog.at_level(logging.WARNING):
            st = get_strouhal_number(10.0, GeometryType.SINGLE_CYLINDER)
        assert st is not None  # result still returned (clamped)
        assert any(
            "clamp" in r.message.lower() or "clamping" in r.message.lower() for r in caplog.records
        ), "Expected a clamping WARNING"

    def test_out_of_range_high_re_clamps(self, caplog: pytest.LogCaptureFixture) -> None:
        """Re above table maximum should clamp and issue a WARNING."""
        with caplog.at_level(logging.WARNING):
            st = get_strouhal_number(1e9, GeometryType.SINGLE_CYLINDER)
        assert st is not None
        assert any(
            "clamp" in r.message.lower() or "clamping" in r.message.lower() for r in caplog.records
        ), "Expected a clamping WARNING"

    def test_spacing_ratio_ignored_for_single(self) -> None:
        """Spacing ratio should be silently ignored for SINGLE_CYLINDER."""
        st_without = get_strouhal_number(10000.0, GeometryType.SINGLE_CYLINDER)
        st_with = get_strouhal_number(10000.0, GeometryType.SINGLE_CYLINDER, spacing_ratio=3.0)
        assert st_without == st_with


class TestTandem:
    """Tests for TANDEM Strouhal interpolation."""

    def test_missing_spacing_ratio_raises(self) -> None:
        with pytest.raises(PhysicsInputError):
            get_strouhal_number(10000.0, GeometryType.TANDEM, spacing_ratio=None)

    def test_plausible_value(self) -> None:
        st = get_strouhal_number(10000.0, GeometryType.TANDEM, spacing_ratio=2.5)
        assert 0.10 <= st <= 0.30, f"Tandem St={st} out of expected range"

    def test_deterministic(self) -> None:
        st1 = get_strouhal_number(10000.0, GeometryType.TANDEM, spacing_ratio=2.0)
        st2 = get_strouhal_number(10000.0, GeometryType.TANDEM, spacing_ratio=2.0)
        assert st1 == st2
