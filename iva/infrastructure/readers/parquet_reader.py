"""Parquet file reader for the Industrial Vibration Analyzer."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from iva.core.models.exceptions import FileCorruptedError, FileReadError, IVAFileNotFoundError
from iva.core.models.signal_data import RawFileData
from iva.infrastructure.logging.app_logger import get_logger

logger = get_logger(__name__)

_LARGE_FILE_THRESHOLD_BYTES = 100 * 1024 * 1024  # 100 MB


def read_parquet(file_path: str) -> RawFileData:
    """Read a Parquet file and return a :class:`~iva.core.models.signal_data.RawFileData`.

    Args:
        file_path: Absolute or relative path to the Parquet file.

    Returns:
        A populated :class:`RawFileData` instance.

    Raises:
        IVAFileNotFoundError: The file does not exist.
        FileReadError: The file exists but cannot be parsed.
    """
    path = Path(file_path)
    logger.debug("Parquet read started: %s", path.name)

    if not path.exists():
        raise IVAFileNotFoundError(
            user_message="Input file was not found.",
            technical_details=f"Full path checked: {path}",
            recovery_hint="Check that the file path is correct and the file has not been moved.",
        )

    file_size = path.stat().st_size

    if file_size > _LARGE_FILE_THRESHOLD_BYTES:
        logger.warning(
            "Parquet file '%s' is %.1f MB — reading may be slow.",
            path.name,
            file_size / (1024 * 1024),
        )

    try:
        df = pd.read_parquet(path, engine="pyarrow")
    except FileNotFoundError as exc:
        raise IVAFileNotFoundError(
            user_message="Input file was not found.",
            technical_details=str(exc),
        ) from exc
    except Exception as exc:
        exc_str = str(exc).lower()
        if "corrupt" in exc_str or "invalid" in exc_str or "magic" in exc_str:
            raise FileCorruptedError(
                user_message="The Parquet file appears to be corrupted "
                "or is not a valid Parquet file.",
                technical_details=str(exc),
            ) from exc
        raise FileReadError(
            user_message="The Parquet file could not be read.",
            technical_details=str(exc),
        ) from exc

    column_names = tuple(str(c) for c in df.columns)
    column_dtypes = {col: str(df[col].dtype) for col in df.columns}
    row_count = len(df)

    logger.info(
        "Parquet read completed: '%s' — %d rows, %d columns",
        path.name,
        row_count,
        len(column_names),
    )

    return RawFileData(
        file_path=path,
        file_format="parquet",
        column_names=column_names,
        column_dtypes=column_dtypes,
        row_count=row_count,
        file_size_bytes=file_size,
        data=df,
        read_timestamp=datetime.now(),
    )
