"""Public API for the IVA experiment-vs-CFD validation layer.

All functions operate on NumPy arrays.  No imports from ``iva.ui``,
``iva.app``, or ``iva.infrastructure`` are permitted inside this package.
"""

from __future__ import annotations

from iva.core.validation.error_metrics import (
    MAPE_DENOMINATOR_THRESHOLD,
    mae,
    mape,
    pearson_r,
    rmse,
)
from iva.core.validation.experiment_vs_cfd import compare

__all__ = [
    "rmse",
    "mae",
    "mape",
    "pearson_r",
    "compare",
    "MAPE_DENOMINATOR_THRESHOLD",
]
