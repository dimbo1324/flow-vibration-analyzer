"""Strouhal number lookup and interpolation from tabulated engineering data.

Tables are loaded once from ``config/strouhal_tables.toml`` and cached for
the lifetime of the process.

All values in ``config/strouhal_tables.toml`` are a conservative engineering
baseline (Blevins-style + dissertation data) and are NOT final physical truth.
Out-of-range Reynolds numbers are clamped to the nearest boundary value with
a WARNING log entry.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

import numpy as np

from iva.core.models.enums import GeometryType
from iva.core.models.exceptions import PhysicsInputError

logger = logging.getLogger(__name__)

__all__ = ["get_strouhal_number"]

# Path to the TOML config relative to this file's package root
_CONFIG_PATH = Path(__file__).resolve().parents[3] / "config" / "strouhal_tables.toml"


@lru_cache(maxsize=1)
def _load_tables() -> dict:  # type: ignore[type-arg]
    """Load and cache the Strouhal lookup tables from TOML."""
    try:
        import tomllib  # Python 3.11+
    except ImportError:  # pragma: no cover
        import tomli as tomllib  # type: ignore[no-redef]

    with open(_CONFIG_PATH, "rb") as fh:
        return tomllib.load(fh)


def get_strouhal_number(
    reynolds_number: float,
    geometry_type: GeometryType,
    spacing_ratio: float | None = None,
) -> float:
    """Return the Strouhal number for the given flow conditions.

    For ``SINGLE_CYLINDER``: 1-D linear interpolation on a Reynolds-number
    table (Blevins-style conservative baseline).

    For ``TANDEM``: 2-D interpolation on a (Re, L/D) grid using
    ``scipy.interpolate.RegularGridInterpolator``.  Out-of-range inputs are
    clamped to the nearest boundary with a WARNING log.

    Parameters
    ----------
    reynolds_number:
        Dimensionless Reynolds number.  Must be ≥ 0.
    geometry_type:
        Cylinder configuration — ``SINGLE_CYLINDER`` or ``TANDEM``.
    spacing_ratio:
        Centre-to-centre spacing divided by cylinder diameter (L/D).
        Required for ``TANDEM``; ignored for ``SINGLE_CYLINDER``.

    Returns
    -------
    float
        Strouhal number St (dimensionless).

    Raises
    ------
    PhysicsInputError
        If ``reynolds_number`` is negative, or if ``geometry_type`` is
        ``TANDEM`` but ``spacing_ratio`` is not provided.
    """
    if reynolds_number < 0.0:
        raise PhysicsInputError(
            user_message="Число Рейнольдса не может быть отрицательным.",
            technical_details=f"reynolds_number={reynolds_number!r} < 0",
            recovery_hint="Проверьте входные параметры течения.",
        )

    tables = _load_tables()

    if geometry_type == GeometryType.SINGLE_CYLINDER:
        st = _interp_single(reynolds_number, tables)
    elif geometry_type == GeometryType.TANDEM:
        if spacing_ratio is None:
            raise PhysicsInputError(
                user_message=(
                    "Для конфигурации 'тандем' необходимо задать "
                    "относительное расстояние между цилиндрами (L/D)."
                ),
                technical_details="spacing_ratio is None for TANDEM geometry",
                recovery_hint=(
                    "Введите значение spacing_ratio = cylinder_spacing_m / cylinder_diameter_m."
                ),
            )
        st = _interp_tandem(reynolds_number, spacing_ratio, tables)
    else:
        raise PhysicsInputError(
            user_message=f"Неизвестный тип геометрии: {geometry_type}.",
            technical_details=f"geometry_type={geometry_type!r}",
        )

    logger.debug(
        "Strouhal number St = %.4f (Re=%.2e, geometry=%s)", st, reynolds_number, geometry_type
    )
    return st


def _clamp(value: float, lo: float, hi: float, name: str) -> float:
    """Clamp ``value`` to ``[lo, hi]``, warning if clamping occurs."""
    if value < lo:
        logger.warning(
            "Parameter '%s'=%.4g is below table range [%.4g, %.4g]; clamping to %.4g.",
            name,
            value,
            lo,
            hi,
            lo,
        )
        return lo
    if value > hi:
        logger.warning(
            "Parameter '%s'=%.4g is above table range [%.4g, %.4g]; clamping to %.4g.",
            name,
            value,
            lo,
            hi,
            hi,
        )
        return hi
    return value


def _interp_single(re: float, tables: dict) -> float:  # type: ignore[type-arg]
    sc = tables["single_cylinder"]
    re_table = np.array(sc["reynolds"], dtype=np.float64)
    st_table = np.array(sc["strouhal"], dtype=np.float64)

    re_clamped = _clamp(re, float(re_table[0]), float(re_table[-1]), "reynolds_number")
    st: float = float(np.interp(re_clamped, re_table, st_table))
    return st


def _interp_tandem(re: float, sr: float, tables: dict) -> float:  # type: ignore[type-arg]
    from scipy.interpolate import RegularGridInterpolator

    td = tables["tandem"]
    re_table = np.array(td["reynolds"], dtype=np.float64)
    sr_table = np.array(td["spacing_ratios"], dtype=np.float64)
    st_grid = np.array(td["strouhal"], dtype=np.float64)  # shape (len(re), len(sr))

    re_clamped = _clamp(re, float(re_table[0]), float(re_table[-1]), "reynolds_number")
    sr_clamped = _clamp(sr, float(sr_table[0]), float(sr_table[-1]), "spacing_ratio")

    interp = RegularGridInterpolator(
        (re_table, sr_table),
        st_grid,
        method="linear",
        bounds_error=False,
        fill_value=None,
    )
    st: float = float(interp([[re_clamped, sr_clamped]])[0])
    return st
