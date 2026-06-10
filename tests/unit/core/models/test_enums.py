"""Tests for domain enumerations."""

from __future__ import annotations

import iva.core.models as models
from iva.core.models.enums import (
    GeometryType,
    PeakInterpretation,
    RiskLevel,
    SignalRole,
    WindowType,
)


class TestSignalRole:
    def test_all_members_present(self) -> None:
        names = {m.name for m in SignalRole}
        assert names == {
            "ACCELERATION_X",
            "ACCELERATION_Y",
            "ACCELERATION_Z",
            "PRESSURE",
            "VELOCITY",
        }

    def test_values_are_strings(self) -> None:
        for member in SignalRole:
            assert isinstance(member.value, str)

    def test_stable_values(self) -> None:
        assert SignalRole.ACCELERATION_X == "acceleration_x"
        assert SignalRole.ACCELERATION_Y == "acceleration_y"
        assert SignalRole.ACCELERATION_Z == "acceleration_z"
        assert SignalRole.PRESSURE == "pressure"
        assert SignalRole.VELOCITY == "velocity"


class TestWindowType:
    def test_all_members_present(self) -> None:
        names = {m.name for m in WindowType}
        assert names == {"HANN", "HAMMING", "RECTANGULAR"}

    def test_stable_values(self) -> None:
        assert WindowType.HANN == "hann"
        assert WindowType.HAMMING == "hamming"
        assert WindowType.RECTANGULAR == "rectangular"


class TestPeakInterpretation:
    def test_all_members_present(self) -> None:
        names = {m.name for m in PeakInterpretation}
        assert names == {"VORTEX_SHEDDING", "HARMONIC", "STRUCTURAL", "UNKNOWN"}

    def test_stable_values(self) -> None:
        assert PeakInterpretation.VORTEX_SHEDDING == "vortex_shedding"
        assert PeakInterpretation.HARMONIC == "harmonic"
        assert PeakInterpretation.STRUCTURAL == "structural"
        assert PeakInterpretation.UNKNOWN == "unknown"


class TestGeometryType:
    def test_all_members_present(self) -> None:
        names = {m.name for m in GeometryType}
        assert names == {"SINGLE_CYLINDER", "TANDEM"}

    def test_stable_values(self) -> None:
        assert GeometryType.SINGLE_CYLINDER == "single_cylinder"
        assert GeometryType.TANDEM == "tandem"


class TestRiskLevel:
    def test_all_members_present(self) -> None:
        names = {m.name for m in RiskLevel}
        assert names == {"SAFE", "WATCH", "CRITICAL"}

    def test_stable_values(self) -> None:
        assert RiskLevel.SAFE == "safe"
        assert RiskLevel.WATCH == "watch"
        assert RiskLevel.CRITICAL == "critical"


class TestPackageLevelExports:
    def test_all_enums_importable_from_package(self) -> None:
        assert models.SignalRole is SignalRole
        assert models.WindowType is WindowType
        assert models.PeakInterpretation is PeakInterpretation
        assert models.GeometryType is GeometryType
        assert models.RiskLevel is RiskLevel
