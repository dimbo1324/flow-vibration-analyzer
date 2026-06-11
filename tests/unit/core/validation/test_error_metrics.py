"""Unit tests for iva.core.validation.error_metrics."""

from __future__ import annotations

import numpy as np
import pytest

from iva.core.models.exceptions import ValidationError
from iva.core.validation.error_metrics import (
    MAPE_DENOMINATOR_THRESHOLD,
    mae,
    mape,
    pearson_r,
    rmse,
)


class TestRmse:
    def test_identical_arrays(self) -> None:
        a = np.array([1.0, 2.0, 3.0])
        assert rmse(a, a.copy()) == 0.0

    def test_known_value(self) -> None:
        exp = np.array([1.0, 2.0, 3.0])
        cfd = np.array([2.0, 2.0, 2.0])
        # errors: [-1, 0, 1] → rmse = sqrt(2/3)
        expected = float(np.sqrt(2.0 / 3.0))
        assert abs(rmse(exp, cfd) - expected) < 1e-12

    def test_mismatched_lengths_raise(self) -> None:
        with pytest.raises(ValidationError):
            rmse(np.array([1.0, 2.0]), np.array([1.0]))

    def test_empty_raises(self) -> None:
        with pytest.raises(ValidationError):
            rmse(np.array([]), np.array([]))

    def test_non_finite_raises(self) -> None:
        with pytest.raises(ValidationError):
            rmse(np.array([1.0, np.nan]), np.array([1.0, 2.0]))


class TestMae:
    def test_identical_arrays(self) -> None:
        a = np.array([1.0, 2.0, 3.0])
        assert mae(a, a.copy()) == 0.0

    def test_known_value(self) -> None:
        exp = np.array([1.0, 2.0, 3.0])
        cfd = np.array([2.0, 2.0, 2.0])
        # |errors|: [1, 0, 1] → mae = 2/3
        expected = 2.0 / 3.0
        assert abs(mae(exp, cfd) - expected) < 1e-12

    def test_mismatched_lengths_raise(self) -> None:
        with pytest.raises(ValidationError):
            mae(np.array([1.0, 2.0]), np.array([1.0]))

    def test_empty_raises(self) -> None:
        with pytest.raises(ValidationError):
            mae(np.array([]), np.array([]))

    def test_non_finite_raises(self) -> None:
        with pytest.raises(ValidationError):
            mae(np.array([np.inf, 1.0]), np.array([1.0, 1.0]))


class TestMape:
    def test_identical_safe_arrays(self) -> None:
        a = np.array([1.0, 2.0, 3.0])
        result = mape(a, a.copy())
        assert result is not None
        assert abs(result) < 1e-10

    def test_known_value(self) -> None:
        exp = np.array([10.0, 20.0])
        cfd = np.array([11.0, 18.0])
        # |errors / exp|: [0.1, 0.1] → mape = 10.0 %
        result = mape(exp, cfd)
        assert result is not None
        assert abs(result - 10.0) < 1e-10

    def test_near_zero_denominator_returns_none(self) -> None:
        exp = np.array([0.0, 0.0, 0.0])
        cfd = np.array([1.0, 2.0, 3.0])
        result = mape(exp, cfd)
        assert result is None

    def test_constant_threshold(self) -> None:
        """All |exp| < MAPE_DENOMINATOR_THRESHOLD → None."""
        tiny = MAPE_DENOMINATOR_THRESHOLD * 0.5
        exp = np.array([tiny, tiny])
        cfd = np.array([1.0, 1.0])
        assert mape(exp, cfd) is None

    def test_mismatched_lengths_raise(self) -> None:
        with pytest.raises(ValidationError):
            mape(np.array([1.0]), np.array([1.0, 2.0]))


class TestPearsonR:
    def test_identical_arrays(self) -> None:
        a = np.array([1.0, 2.0, 3.0])
        assert abs(pearson_r(a, a.copy()) - 1.0) < 1e-12

    def test_perfectly_correlated(self) -> None:
        exp = np.array([1.0, 2.0, 3.0])
        cfd = 2.0 * exp + 5.0
        assert abs(pearson_r(exp, cfd) - 1.0) < 1e-12

    def test_anti_correlated(self) -> None:
        exp = np.array([1.0, 2.0, 3.0])
        cfd = -1.0 * exp
        assert abs(pearson_r(exp, cfd) + 1.0) < 1e-12

    def test_both_constant_returns_one(self) -> None:
        a = np.array([5.0, 5.0, 5.0])
        b = np.array([5.0, 5.0, 5.0])
        assert pearson_r(a, b) == 1.0

    def test_one_constant_raises(self) -> None:
        exp = np.array([1.0, 2.0, 3.0])
        cfd = np.array([5.0, 5.0, 5.0])
        with pytest.raises(ValidationError):
            pearson_r(exp, cfd)

    def test_mismatched_lengths_raise(self) -> None:
        with pytest.raises(ValidationError):
            pearson_r(np.array([1.0, 2.0]), np.array([1.0]))

    def test_empty_raises(self) -> None:
        with pytest.raises(ValidationError):
            pearson_r(np.array([]), np.array([]))
