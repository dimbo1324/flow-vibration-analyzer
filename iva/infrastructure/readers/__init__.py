"""File reader factory for the Industrial Vibration Analyzer.

Dispatches to the appropriate reader based on the file extension.
"""

from __future__ import annotations

from pathlib import Path

from iva.core.models.exceptions import UnsupportedFormatError
from iva.core.models.signal_data import RawFileData
from iva.infrastructure.readers.csv_reader import read_csv
from iva.infrastructure.readers.excel_reader import read_excel
from iva.infrastructure.readers.parquet_reader import read_parquet

__all__ = [
    "read_file",
    "read_csv",
    "read_parquet",
    "read_excel",
]

_EXTENSION_MAP: dict[str, str] = {
    ".csv": "csv",
    ".parquet": "parquet",
    ".xlsx": "xlsx",
}


def read_file(file_path: str) -> RawFileData:
    """Dispatch to the correct reader based on the file extension.

    Args:
        file_path: Absolute or relative path to the input file.

    Returns:
        A :class:`~iva.core.models.signal_data.RawFileData` instance.

    Raises:
        UnsupportedFormatError: The file extension is not supported.
        IVAFileNotFoundError: The file does not exist.
        FileReadError: The file exists but cannot be parsed.
    """
    ext = Path(file_path).suffix.lower()
    fmt = _EXTENSION_MAP.get(ext)

    if fmt is None:
        supported = ", ".join(sorted(_EXTENSION_MAP))
        raise UnsupportedFormatError(
            user_message=(
                f"The file format '{ext}' is not supported. " f"Supported formats: {supported}."
            ),
            technical_details=f"Extension '{ext}' not in {list(_EXTENSION_MAP)}",
            recovery_hint=f"Convert the file to one of: {supported}.",
        )

    if fmt == "csv":
        return read_csv(file_path)
    if fmt == "parquet":
        return read_parquet(file_path)
    return read_excel(file_path)
