"""Unit tests for iva.core.validation.experiment_vs_cfd."""

from __future__ import annotations

import numpy as np
import pytest

from iva.core.models.analysis_result import ValidationResult
from iva.core.models.exceptions import ValidationError
from iva.core.validation.error_metrics import MAPE_DENOMINATOR_THRESHOLD
from iva.core.validation.experiment_vs_cfd import compare


def _make_pair(
    x_start: float = 0.0,
    x_end: float = 1.0,
    n: int = 50,
    offset: float = 0.0,
) -> tuple[np.ndarray, np.ndarray]:
    x = np.linspace(x_start, x_end, n)
    y = np.sin(2 * np.pi * x) + offset
    return x, y


class TestCompare:
    def test_identical_profiles(self) -> None:
        """Identical experiment and CFD → RMSE≈0, MAE≈0, pearson_r≈1."""
        pair = _make_pair()
        result = compare(pair, pair)
        assert result.rmse < 1e-10
        assert result.mae < 1e-10
        assert abs(result.pearson_r - 1.0) < 1e-10

    def test_different_grids(self) -> None:
        """Different coordinate grids should be handled by interpolation."""
        exp = _make_pair(0.0, 1.0, 100)
        cfd = _make_pair(0.0, 1.0, 60)
        result = compare(exp, cfd)
        assert isinstance(result, ValidationResult)

    def test_returns_validation_result(self) -> None:
        pair = _make_pair()
        result = compare(pair, pair)
        assert isinstance(result, ValidationResult)

    def test_no_overlap_raises(self) -> None:
        """Disjoint coordinate ranges → ValidationError."""
        exp = _make_pair(0.0, 1.0)
        cfd = _make_pair(2.0, 3.0)
        with pytest.raises(ValidationError):
            compare(exp, cfd)

    def test_unsorted_coords_handled(self) -> None:
        """Unsorted coordinate arrays should be sorted before comparison."""
        x = np.array([0.5, 0.0, 1.0, 0.25, 0.75])
        y = np.sin(x)
        pair_sorted = _make_pair(0.0, 1.0, 50)
        result = compare((x, y), pair_sorted)
        assert isinstance(result, ValidationResult)

    def test_mape_none_when_denominator_small(self) -> None:
        """Profile near zero → mape=None, is_mape_valid=False."""
        tiny = MAPE_DENOMINATOR_THRESHOLD * 0.1
        x = np.linspace(0, 1, 20)
        # Use a non-constant tiny signal so pearson_r is defined
        y_exp = np.linspace(tiny, tiny * 2, 20)
        y_cfd = np.ones(20)
        result = compare((x, y_exp), (x, y_cfd))
        assert result.mape is None
        assert result.is_mape_valid is False

    def test_is_mape_valid_true_for_normal_data(self) -> None:
        pair = _make_pair(offset=10.0)
        result = compare(pair, pair)
        assert result.is_mape_valid is True

    def test_empty_arrays_raise(self) -> None:
        with pytest.raises(ValidationError):
            compare((np.array([]), np.array([])), _make_pair())

    def test_non_finite_raises(self) -> None:
        x = np.array([0.0, 0.5, 1.0])
        y = np.array([1.0, np.nan, 3.0])
        with pytest.raises(ValidationError):
            compare((x, y), _make_pair())

    def test_coordinate_array_in_result(self) -> None:
        pair = _make_pair()
        result = compare(pair, pair)
        assert len(result.coordinate_array) > 0
