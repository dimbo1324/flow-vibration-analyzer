"""Edge-case tests from documentation/12_validation_and_verification.md.

Tests cover boundary conditions not already exercised in the per-module
test files: invalid physical inputs, empty/constant signals, non-monotonic
time, bad filter settings, and mismatched validation arrays.
"""

from __future__ import annotations

import numpy as np
import pytest

from iva.core.models.exceptions import (
    FilterConfigurationError,
    PhysicsInputError,
)

# ---------------------------------------------------------------------------
# Physical input validation
# ---------------------------------------------------------------------------


class TestPhysicsInputValidation:
    """Invalid physical parameters must raise PhysicsInputError."""

    def test_zero_diameter_raises_physics_input_error(self) -> None:
        from iva.core.physics.reynolds_calculator import calculate_reynolds_number

        with pytest.raises(PhysicsInputError):
            calculate_reynolds_number(
                velocity_ms=2.0, diameter_m=0.0, density_kgm3=998.0, dynamic_viscosity_pas=1.002e-3
            )

    def test_negative_diameter_raises_physics_input_error(self) -> None:
        from iva.core.physics.reynolds_calculator import calculate_reynolds_number

        with pytest.raises(PhysicsInputError):
            calculate_reynolds_number(
                velocity_ms=2.0,
                diameter_m=-0.01,
                density_kgm3=998.0,
                dynamic_viscosity_pas=1.002e-3,
            )

    def test_zero_density_raises_physics_input_error(self) -> None:
        from iva.core.physics.reynolds_calculator import calculate_reynolds_number

        with pytest.raises(PhysicsInputError):
            calculate_reynolds_number(
                velocity_ms=2.0, diameter_m=0.012, density_kgm3=0.0, dynamic_viscosity_pas=1.002e-3
            )

    def test_negative_viscosity_raises_physics_input_error(self) -> None:
        from iva.core.physics.reynolds_calculator import calculate_reynolds_number

        with pytest.raises(PhysicsInputError):
            calculate_reynolds_number(
                velocity_ms=2.0,
                diameter_m=0.012,
                density_kgm3=998.0,
                dynamic_viscosity_pas=-1e-3,
            )

    def test_zero_velocity_raises_physics_input_error(self) -> None:
        from iva.core.physics.vortex_frequency import calculate_shedding_frequency

        with pytest.raises(PhysicsInputError):
            calculate_shedding_frequency(strouhal_number=0.21, velocity_ms=0.0, diameter_m=0.012)

    def test_zero_diameter_in_vortex_raises(self) -> None:
        from iva.core.physics.vortex_frequency import calculate_shedding_frequency

        with pytest.raises(PhysicsInputError):
            calculate_shedding_frequency(strouhal_number=0.21, velocity_ms=2.0, diameter_m=0.0)


# ---------------------------------------------------------------------------
# Empty signal handling
# ---------------------------------------------------------------------------


class TestEmptyOrConstantSignal:
    """Empty and constant signals must be handled gracefully."""

    def test_remove_mean_constant_signal(self) -> None:
        """Constant signal after mean removal should be all zeros."""
        from iva.core.signal.preprocessor import remove_mean

        signal = np.full(1000, 5.0)
        result = remove_mean(signal)
        assert np.allclose(result, 0.0, atol=1e-10)

    def test_calculate_total_rms_constant_signal(self) -> None:
        """RMS of constant signal equals the absolute value."""
        from iva.core.spectrum.rms_calculator import calculate_total_rms

        signal = np.full(1000, 3.0)
        assert abs(calculate_total_rms(signal) - 3.0) < 1e-10

    def test_rms_zero_signal_returns_zero(self) -> None:
        from iva.core.spectrum.rms_calculator import calculate_total_rms

        signal = np.zeros(500)
        assert calculate_total_rms(signal) == pytest.approx(0.0)

    def test_outlier_detection_constant_signal_no_crash(self) -> None:
        """Outlier detector on a flat signal must not raise or divide by zero."""
        from iva.core.signal.outlier_detector import detect_outliers

        signal = np.full(1000, 2.5)
        # Should return a boolean mask of the same length without error
        mask = detect_outliers(signal, window_samples=51, threshold_sigma=4.0)
        assert mask.shape == signal.shape
        assert mask.dtype == bool

    def test_psd_short_signal_raises_insufficient_data(self) -> None:
        """Signal shorter than nperseg must raise InsufficientDataError."""
        from iva.core.models.exceptions import InsufficientDataError
        from iva.core.models.settings import SpectralSettings
        from iva.core.spectrum.psd_calculator import calculate_psd

        signal = np.sin(2 * np.pi * 10 * np.linspace(0, 0.1, 100))
        settings = SpectralSettings(segment_length_samples=1024)
        with pytest.raises(InsufficientDataError):
            calculate_psd(signal, sampling_rate_hz=1000.0, settings=settings)


# ---------------------------------------------------------------------------
# Non-monotonic time axis
# ---------------------------------------------------------------------------


class TestNonMonotonicTime:
    """Non-monotonic time axis must produce NonMonotonicTimeAxisError."""

    def test_non_monotonic_time_raises_validation_error(self, tmp_path) -> None:
        import csv

        from iva.core.models.enums import SignalRole
        from iva.core.models.signal_data import ColumnRoleAssignment
        from iva.infrastructure.readers import read_file
        from iva.infrastructure.validators.data_quality_checker import check_data_quality

        csv_file = tmp_path / "bad_time.csv"
        with open(csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["time_s", "signal"])
            # Non-monotonic: time goes backwards at row 3
            rows = [(0.0, 1.0), (0.001, 1.1), (0.0005, 0.9), (0.003, 1.2)]
            for t, s in rows:
                writer.writerow([t, s])

        raw = read_file(str(csv_file))
        ra = ColumnRoleAssignment(
            time_column="time_s",
            primary_signal_column="signal",
            signal_role=SignalRole.ACCELERATION_X,
            additional_columns={},
            sampling_rate_hz=1000.0,
        )
        from iva.core.models.exceptions import NonMonotonicTimeAxisError

        with pytest.raises(NonMonotonicTimeAxisError):
            check_data_quality(raw, ra)


# ---------------------------------------------------------------------------
# Bad filter settings
# ---------------------------------------------------------------------------


class TestBadFilterSettings:
    """Filter parameters outside valid range must raise FilterConfigurationError."""

    def test_low_cutoff_above_nyquist_raises(self) -> None:
        from iva.core.signal.filter import apply_bandpass_filter

        signal = np.random.default_rng(0).standard_normal(1000)
        # low_hz > Nyquist (500 Hz at fs=1000)
        with pytest.raises(FilterConfigurationError):
            apply_bandpass_filter(
                signal, sampling_rate_hz=1000.0, low_hz=600.0, high_hz=800.0, order=4
            )

    def test_low_cutoff_equals_high_cutoff_raises(self) -> None:
        from iva.core.signal.filter import apply_bandpass_filter

        signal = np.random.default_rng(1).standard_normal(1000)
        with pytest.raises(FilterConfigurationError):
            apply_bandpass_filter(
                signal, sampling_rate_hz=1000.0, low_hz=100.0, high_hz=100.0, order=4
            )

    def test_high_cutoff_above_nyquist_raises(self) -> None:
        from iva.core.signal.filter import apply_bandpass_filter

        signal = np.random.default_rng(2).standard_normal(1000)
        with pytest.raises(FilterConfigurationError):
            apply_bandpass_filter(
                signal, sampling_rate_hz=1000.0, low_hz=10.0, high_hz=600.0, order=4
            )


# ---------------------------------------------------------------------------
# Validation metrics — mismatched arrays
# ---------------------------------------------------------------------------


class TestValidationMetricsMismatched:
    """Metrics on arrays of different lengths must raise or handle gracefully."""

    def test_rmse_mismatched_arrays_raises(self) -> None:
        from iva.core.validation.error_metrics import rmse

        a = np.array([1.0, 2.0, 3.0])
        b = np.array([1.0, 2.0])
        with pytest.raises((ValueError, Exception)):
            rmse(a, b)

    def test_mae_mismatched_arrays_raises(self) -> None:
        from iva.core.validation.error_metrics import mae

        a = np.array([1.0, 2.0, 3.0])
        b = np.array([1.0, 2.0])
        with pytest.raises((ValueError, Exception)):
            mae(a, b)

    def test_pearson_r_identical_arrays_returns_one(self) -> None:
        from iva.core.validation.error_metrics import pearson_r

        a = np.linspace(1.0, 10.0, 50)
        result = pearson_r(a, a)
        assert abs(result - 1.0) < 1e-10

    def test_mape_with_zero_denominator_returns_none(self) -> None:
        from iva.core.validation.error_metrics import mape

        a = np.array([0.0, 0.0, 0.0])
        b = np.array([1.0, 2.0, 3.0])
        result = mape(a, b)
        assert result is None
