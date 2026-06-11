"""Scalar error metrics for experiment-vs-CFD comparison (Algorithm 11).

All functions expect 1-D NumPy arrays of equal length, pre-interpolated to a
common coordinate grid by ``experiment_vs_cfd.compare``.
"""

from __future__ import annotations

import logging

import numpy as np
from numpy.typing import NDArray

from iva.core.models.exceptions import ValidationError

logger = logging.getLogger(__name__)

__all__ = [
    "MAPE_DENOMINATOR_THRESHOLD",
    "rmse",
    "mae",
    "mape",
    "pearson_r",
]

# Protect MAPE from near-zero denominators (in the physical unit of the signal).
MAPE_DENOMINATOR_THRESHOLD: float = 1e-6


# ---------------------------------------------------------------------------
# Internal validation helper
# ---------------------------------------------------------------------------


def _validate_metric_inputs(
    experiment: NDArray[np.float64],
    cfd: NDArray[np.float64],
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Validate and coerce both arrays; raise ValidationError on any violation."""
    exp = np.asarray(experiment, dtype=np.float64)
    cfd_ = np.asarray(cfd, dtype=np.float64)

    if exp.ndim != 1 or cfd_.ndim != 1:
        raise ValidationError(
            user_message="Массивы данных должны быть одномерными.",
            technical_details=f"experiment.ndim={exp.ndim}, cfd.ndim={cfd_.ndim}",
        )
    if len(exp) == 0 or len(cfd_) == 0:
        raise ValidationError(
            user_message="Массивы данных не могут быть пустыми.",
            technical_details="One or both arrays have length 0",
        )
    if len(exp) != len(cfd_):
        raise ValidationError(
            user_message=(
                f"Длины массивов не совпадают: эксперимент={len(exp)}, " f"расчёт={len(cfd_)}."
            ),
            technical_details=f"len(experiment)={len(exp)} != len(cfd)={len(cfd_)}",
            recovery_hint="Убедитесь, что данные интерполированы на общую сетку.",
        )
    if not (np.all(np.isfinite(exp)) and np.all(np.isfinite(cfd_))):
        raise ValidationError(
            user_message="Массивы данных содержат нечисловые значения (NaN или Inf).",
            technical_details="Non-finite values detected in experiment or cfd array",
            recovery_hint="Проверьте входные данные на наличие пропусков и выбросов.",
        )
    return exp, cfd_


# ---------------------------------------------------------------------------
# Metric functions
# ---------------------------------------------------------------------------


def rmse(
    experiment: NDArray[np.float64],
    cfd: NDArray[np.float64],
) -> float:
    """Root mean square error: ``sqrt(mean((experiment - cfd)**2))``.

    Raises
    ------
    ValidationError
        If inputs fail validation.
    """
    exp, cfd_ = _validate_metric_inputs(experiment, cfd)
    result: float = float(np.sqrt(np.mean((exp - cfd_) ** 2)))
    return result


def mae(
    experiment: NDArray[np.float64],
    cfd: NDArray[np.float64],
) -> float:
    """Mean absolute error: ``mean(abs(experiment - cfd))``.

    Raises
    ------
    ValidationError
        If inputs fail validation.
    """
    exp, cfd_ = _validate_metric_inputs(experiment, cfd)
    result: float = float(np.mean(np.abs(exp - cfd_)))
    return result


def mape(
    experiment: NDArray[np.float64],
    cfd: NDArray[np.float64],
) -> float | None:
    """Mean absolute percentage error, or ``None`` if denominators are near zero.

    Returns ``None`` when no element of ``experiment`` satisfies
    ``abs(experiment[i]) >= MAPE_DENOMINATOR_THRESHOLD``.

    Formula (on the valid subset):
    ``100 * mean(abs((experiment - cfd) / experiment))``.

    Raises
    ------
    ValidationError
        If inputs fail validation.
    """
    exp, cfd_ = _validate_metric_inputs(experiment, cfd)
    mask = np.abs(exp) >= MAPE_DENOMINATOR_THRESHOLD
    if not np.any(mask):
        logger.debug("MAPE: all experiment values below threshold — returning None.")
        return None
    result: float = float(100.0 * np.mean(np.abs((exp[mask] - cfd_[mask]) / exp[mask])))
    return result


def pearson_r(
    experiment: NDArray[np.float64],
    cfd: NDArray[np.float64],
) -> float:
    """Pearson correlation coefficient between *experiment* and *cfd*.

    Special cases:

    * Both arrays are identical constants → returns 1.0.
    * Only one array is constant (undefined correlation) → raises ValidationError.

    Raises
    ------
    ValidationError
        If inputs fail validation, or if exactly one array is constant.
    """
    exp, cfd_ = _validate_metric_inputs(experiment, cfd)

    exp_std = float(np.std(exp))
    cfd_std = float(np.std(cfd_))

    if exp_std == 0.0 and cfd_std == 0.0:
        # Both identical constants: perfect correlation by convention.
        return 1.0

    if exp_std == 0.0 or cfd_std == 0.0:
        raise ValidationError(
            user_message=(
                "Не удалось вычислить коэффициент Пирсона: один из массивов " "является константой."
            ),
            technical_details=(
                f"experiment std={exp_std}, cfd std={cfd_std}; "
                "correlation is undefined when only one array is constant."
            ),
        )

    result: float = float(np.corrcoef(exp, cfd_)[0, 1])
    return result
