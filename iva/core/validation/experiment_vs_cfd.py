"""Experiment-versus-CFD profile comparison (Algorithm 11).

Accepts two (coordinates, values) pairs sampled on potentially different grids,
interpolates both to a common grid, and returns a ``ValidationResult`` with all
error metrics.
"""

from __future__ import annotations

import logging

import numpy as np
from numpy.typing import NDArray

from iva.core.models.analysis_result import ValidationResult
from iva.core.models.exceptions import ValidationError
from iva.core.validation.error_metrics import mae, mape, pearson_r, rmse

logger = logging.getLogger(__name__)

__all__ = ["compare"]


def compare(
    experiment: tuple[NDArray[np.float64], NDArray[np.float64]],
    cfd_data: tuple[NDArray[np.float64], NDArray[np.float64]],
) -> ValidationResult:
    """Compare an experimental profile with a CFD profile on a common grid.

    Parameters
    ----------
    experiment:
        ``(exp_coords, exp_values)`` — 1-D arrays of equal length.
    cfd_data:
        ``(cfd_coords, cfd_values)`` — 1-D arrays of equal length.

    Returns
    -------
    ValidationResult
        Frozen dataclass with the interpolated arrays and all error metrics.

    Raises
    ------
    ValidationError
        If any array is not 1-D, is empty, has non-finite values, its pair
        arrays differ in length, or the coordinate ranges do not overlap.
    """
    exp_x, exp_y = _coerce_and_validate_pair(experiment, "experiment")
    cfd_x, cfd_y = _coerce_and_validate_pair(cfd_data, "cfd")

    # Sort by coordinate (handle unsorted grids gracefully)
    exp_order = np.argsort(exp_x)
    cfd_order = np.argsort(cfd_x)
    exp_x, exp_y = exp_x[exp_order], exp_y[exp_order]
    cfd_x, cfd_y = cfd_x[cfd_order], cfd_y[cfd_order]

    # Find overlapping range
    left = max(float(exp_x[0]), float(cfd_x[0]))
    right = min(float(exp_x[-1]), float(cfd_x[-1]))

    if left >= right:
        raise ValidationError(
            user_message=(
                "Диапазоны координат экспериментальных и расчётных данных " "не перекрываются."
            ),
            technical_details=(
                f"exp range=[{exp_x[0]:.4g}, {exp_x[-1]:.4g}], "
                f"cfd range=[{cfd_x[0]:.4g}, {cfd_x[-1]:.4g}]; "
                f"overlap=[{left:.4g}, {right:.4g}]"
            ),
            recovery_hint=(
                "Убедитесь, что координатные диапазоны экспериментальных "
                "и расчётных профилей совпадают."
            ),
        )

    n_points = min(len(exp_x), len(cfd_x))
    common_grid: NDArray[np.float64] = np.linspace(left, right, n_points)

    exp_interp: NDArray[np.float64] = np.interp(common_grid, exp_x, exp_y)
    cfd_interp: NDArray[np.float64] = np.interp(common_grid, cfd_x, cfd_y)

    rmse_val = rmse(exp_interp, cfd_interp)
    mae_val = mae(exp_interp, cfd_interp)
    mape_val = mape(exp_interp, cfd_interp)

    # pearson_r is undefined when one array is constant — treat as NaN (0.0) and log.
    try:
        pr_val = pearson_r(exp_interp, cfd_interp)
    except ValidationError:
        pr_val = float("nan")
        logger.warning(
            "Pearson r is undefined (one or both arrays are constant); "
            "storing NaN in ValidationResult."
        )

    logger.info(
        "Validation: RMSE=%.4g, MAE=%.4g, MAPE=%s, r=%.4f",
        rmse_val,
        mae_val,
        f"{mape_val:.2f}%" if mape_val is not None else "None",
        pr_val,
    )

    return ValidationResult(
        coordinate_array=common_grid,
        experiment_array=exp_interp,
        cfd_array=cfd_interp,
        rmse=rmse_val,
        mae=mae_val,
        mape=mape_val,
        pearson_r=pr_val,
        is_mape_valid=mape_val is not None,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _coerce_and_validate_pair(
    pair: tuple[NDArray[np.float64], NDArray[np.float64]],
    name: str,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    coords = np.asarray(pair[0], dtype=np.float64)
    values = np.asarray(pair[1], dtype=np.float64)

    for arr, label in ((coords, f"{name}_coords"), (values, f"{name}_values")):
        if arr.ndim != 1:
            raise ValidationError(
                user_message=f"Массив '{label}' должен быть одномерным.",
                technical_details=f"{label}.ndim={arr.ndim}",
            )
        if len(arr) == 0:
            raise ValidationError(
                user_message=f"Массив '{label}' не может быть пустым.",
                technical_details=f"{label} has length 0",
            )
        if not np.all(np.isfinite(arr)):
            raise ValidationError(
                user_message=f"Массив '{label}' содержит нечисловые значения (NaN или Inf).",
                technical_details=f"Non-finite values in {label}",
            )

    if len(coords) != len(values):
        raise ValidationError(
            user_message=(
                f"Длины массивов координат и значений для '{name}' не совпадают "
                f"({len(coords)} и {len(values)})."
            ),
            technical_details=f"{name}: len(coords)={len(coords)} != len(values)={len(values)}",
        )

    return coords, values
