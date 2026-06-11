"""Excel (.xlsx) file reader for the Industrial Vibration Analyzer.

Uses openpyxl in read_only=True mode as required by
docs/18_security_and_data_privacy.md to prevent macro execution
and disable external link resolution.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from iva.core.models.exceptions import FileCorruptedError, FileReadError, IVAFileNotFoundError
from iva.core.models.signal_data import RawFileData
from iva.infrastructure.logging.app_logger import get_logger

logger = get_logger(__name__)


def _is_header_row(row: tuple[Any, ...]) -> bool:
    """Return True if the row appears to be a header (all non-numeric strings)."""
    has_string = False
    for cell in row:
        if cell is None:
            continue
        try:
            float(str(cell))
            return False  # numeric value → data row
        except (ValueError, TypeError):
            has_string = True
    return has_string


def read_excel(file_path: str, sheet_name: str | None = None) -> RawFileData:
    """Read an Excel .xlsx file and return a :class:`~iva.core.models.signal_data.RawFileData`.

    Opens the workbook in ``read_only=True, data_only=True`` mode (macros are
    never executed; formula results are read as cached values).

    Args:
        file_path: Absolute or relative path to the ``.xlsx`` file.
        sheet_name: Name of the worksheet to read.  If ``None``, the first
            worksheet is used.

    Returns:
        A populated :class:`RawFileData` instance.

    Raises:
        IVAFileNotFoundError: The file does not exist.
        FileReadError: The file exists but cannot be parsed, or the requested
            sheet does not exist.
    """
    import openpyxl  # imported here to keep the module importable even if openpyxl is absent

    path = Path(file_path)
    logger.debug("Excel read started: %s", path.name)

    if not path.exists():
        raise IVAFileNotFoundError(
            user_message="Input file was not found.",
            technical_details=f"Full path checked: {path}",
            recovery_hint="Check that the file path is correct and the file has not been moved.",
        )

    file_size = path.stat().st_size

    try:
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    except FileNotFoundError as exc:
        raise IVAFileNotFoundError(
            user_message="Input file was not found.",
            technical_details=str(exc),
        ) from exc
    except Exception as exc:
        raise FileCorruptedError(
            user_message="The Excel file could not be opened. "
            "It may be corrupted or in an unsupported format.",
            technical_details=str(exc),
            recovery_hint="Save the file again in .xlsx format and try once more.",
        ) from exc

    try:
        if sheet_name is None:
            ws = wb.worksheets[0]
            sheet_name = ws.title
        else:
            if sheet_name not in wb.sheetnames:
                raise FileReadError(
                    user_message=f"Sheet '{sheet_name}' was not found in the workbook.",
                    technical_details=f"Available sheets: {wb.sheetnames}",
                    recovery_hint="Check the sheet name and try again.",
                )
            ws = wb[sheet_name]

        rows: list[tuple[Any, ...]] = [tuple(cell.value for cell in row) for row in ws.iter_rows()]
    finally:
        wb.close()

    if not rows:
        raise FileReadError(
            user_message="The selected worksheet is empty.",
            technical_details=f"Sheet '{sheet_name}' contained no rows.",
        )

    # Determine header presence.
    first_row = rows[0]
    if _is_header_row(first_row):
        headers = [str(v) if v is not None else f"column_{i}" for i, v in enumerate(first_row)]
        data_rows = rows[1:]
    else:
        n_cols = len(first_row)
        headers = [f"column_{i}" for i in range(n_cols)]
        data_rows = rows

    try:
        df = pd.DataFrame(data_rows, columns=headers)
    except Exception as exc:
        raise FileReadError(
            user_message="The Excel worksheet could not be converted to a table.",
            technical_details=str(exc),
        ) from exc

    # Normalise dtypes to string for consistency with the CSV reader.  Genuinely
    # empty cells (openpyxl returns None) are preserved as pd.NA, while real
    # values are stringified.  Stringifying first and then restoring NA at the
    # originally-null positions avoids turning a legitimate textual "None" cell
    # into a missing value.
    for col in df.columns:
        series = df[col]
        is_null = series.isna()
        df[col] = series.astype(str)
        df.loc[is_null, col] = pd.NA

    column_names = tuple(str(c) for c in df.columns)
    column_dtypes = {col: str(df[col].dtype) for col in df.columns}
    row_count = len(df)

    logger.info(
        "Excel read completed: '%s' sheet='%s' — %d rows, %d columns",
        path.name,
        sheet_name,
        row_count,
        len(column_names),
    )

    return RawFileData(
        file_path=path,
        file_format="xlsx",
        column_names=column_names,
        column_dtypes=column_dtypes,
        row_count=row_count,
        file_size_bytes=file_size,
        data=df,
        read_timestamp=datetime.now(),
    )
