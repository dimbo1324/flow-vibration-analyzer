"""Profile comparison service — reads two CSV files and compares profiles.

Wraps :func:`iva.core.validation.compare` to provide a file-level API:
reads two CSV files (each with two columns: coordinate, value), converts
them to NumPy arrays, and returns a :class:`ValidationResult`.

CSV format expected::

    # Optional comment lines starting with '#' are skipped
    coordinate,value
    0.0,1.23
    0.1,1.45
    ...

Architecture rule: no numerical calculations here — only I/O and delegation.
Must NOT import from iva.ui or PySide6.
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path

import numpy as np

from iva.core.models.analysis_result import ValidationResult
from iva.core.models.exceptions import ValidationError
from iva.core.validation.experiment_vs_cfd import compare

logger = logging.getLogger(__name__)

__all__ = ["compare_profile_csv_files"]


def compare_profile_csv_files(
    experiment_path: str | Path,
    cfd_path: str | Path,
) -> ValidationResult:
    """Read two profile CSV files and return a :class:`ValidationResult`.

    Each CSV file must contain named ``coordinate`` and ``value`` columns.

    Args:
        experiment_path: Path to the experimental profile CSV.
        cfd_path: Path to the CFD profile CSV.

    Returns:
        :class:`ValidationResult` with error metrics.

    Raises:
        ValidationError: If a file cannot be read, is empty, or does not
            have the expected two-column format.
    """
    exp_path = Path(experiment_path)
    cfd_path_obj = Path(cfd_path)

    exp_coords, exp_values = _read_profile_csv(exp_path, "experiment")
    cfd_coords, cfd_values = _read_profile_csv(cfd_path_obj, "CFD")

    logger.info(
        "profile_comparison_service: exp=%d pts, cfd=%d pts",
        len(exp_coords),
        len(cfd_coords),
    )

    return compare(
        experiment=(exp_coords, exp_values),
        cfd_data=(cfd_coords, cfd_values),
    )


def _read_profile_csv(
    path: Path,
    label: str,
) -> tuple[np.ndarray, np.ndarray]:
    """Read a two-column profile CSV and return (coords, values) arrays."""
    if not path.exists():
        raise ValidationError(
            user_message=f"Profile file not found: '{path.name}'.",
            technical_details=f"Path does not exist: {path}",
            recovery_hint="Check the file path and try again.",
        )

    try:
        with open(path, encoding="utf-8-sig", newline="") as fh:
            lines = (line for line in fh if line.strip() and not line.lstrip().startswith("#"))
            reader = csv.DictReader(lines)
            field_map = {name.strip().lower(): name for name in (reader.fieldnames or [])}
            if not {"coordinate", "value"}.issubset(field_map):
                raise ValidationError(
                    user_message=(
                        f"Profile file '{path.name}' must contain "
                        "'coordinate' and 'value' columns."
                    ),
                    technical_details=f"columns={reader.fieldnames!r}",
                )
            coords: list[float] = []
            values: list[float] = []
            for row_number, row in enumerate(reader, start=2):
                try:
                    c = float(str(row[field_map["coordinate"]]).strip())
                    v = float(str(row[field_map["value"]]).strip())
                except (KeyError, TypeError, ValueError) as exc:
                    raise ValidationError(
                        user_message=(
                            f"Profile file '{path.name}' contains an invalid numeric "
                            f"value at row {row_number}."
                        ),
                        technical_details=str(exc),
                    ) from exc
                coords.append(c)
                values.append(v)
    except ValidationError:
        raise
    except OSError as exc:
        raise ValidationError(
            user_message=f"Cannot read profile file '{path.name}'.",
            technical_details=str(exc),
        ) from exc

    if not coords:
        raise ValidationError(
            user_message=f"Profile file '{path.name}' contains no valid numeric data.",
            technical_details=f"label={label}, path={path}",
            recovery_hint=(
                "Ensure the file has at least two numeric columns "
                "(coordinate, value) with no header."
            ),
        )

    return (
        np.asarray(coords, dtype=np.float64),
        np.asarray(values, dtype=np.float64),
    )
