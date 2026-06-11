"""CSV file reader for the Industrial Vibration Analyzer.

Reads a CSV file into a :class:`~iva.core.models.signal_data.RawFileData`
container.  Handles automatic detection of delimiter, encoding and header row.
Comment lines starting with ``#`` are skipped before parsing.

Security note: values starting with ``=``, ``+``, ``-``, ``@`` are treated as
plain strings by pandas (no formula evaluation) because we pass no special
option — pandas does not evaluate spreadsheet formulas.
"""

from __future__ import annotations

import csv
import io
from datetime import datetime
from pathlib import Path

import pandas as pd

from iva.core.models.exceptions import FileReadError, IVAFileNotFoundError
from iva.core.models.signal_data import RawFileData
from iva.infrastructure.logging.app_logger import get_logger

logger = get_logger(__name__)

# Column name patterns that indicate a time axis.
_TIME_COLUMN_HINTS = frozenset({"time", "t", "timestamp", "seconds", "time_s"})
_CANDIDATE_ENCODINGS = ("utf-8", "cp1251", "latin-1")
_CANDIDATE_DELIMITERS = (",", ";", "\t")


def _detect_encoding(file_path: Path) -> str:
    """Try candidate encodings and return the first that decodes successfully."""
    for enc in _CANDIDATE_ENCODINGS:
        try:
            file_path.read_text(encoding=enc)
            return enc
        except (UnicodeDecodeError, LookupError):
            continue
    return "utf-8"  # last-resort default


def _detect_delimiter(sample: str) -> str:
    """Use csv.Sniffer to detect delimiter; fall back to comma."""
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters="".join(_CANDIDATE_DELIMITERS))
        return dialect.delimiter
    except csv.Error:
        return ","


def _has_header(sample: str, delimiter: str) -> bool:
    """Return True if the sample looks like it has a header row."""
    try:
        return csv.Sniffer().has_header(sample)
    except csv.Error:
        # Fall back: check if first row values are non-numeric strings.
        first_line = sample.splitlines()[0] if sample else ""
        for field in first_line.split(delimiter):
            field = field.strip().strip('"')
            try:
                float(field)
                return False  # a number — likely data, not header
            except ValueError:
                pass
        return True


def _strip_comments(text: str) -> str:
    """Remove lines starting with '#' and return the remaining text."""
    lines = [line for line in text.splitlines() if not line.lstrip().startswith("#")]
    return "\n".join(lines)


def read_csv(file_path: str) -> RawFileData:
    """Read a CSV file and return a :class:`~iva.core.models.signal_data.RawFileData`.

    Args:
        file_path: Absolute or relative path to the CSV file.

    Returns:
        A populated :class:`RawFileData` instance.

    Raises:
        IVAFileNotFoundError: The file does not exist.
        FileReadError: The file exists but cannot be parsed.
    """
    path = Path(file_path)
    logger.debug("CSV read started: %s", path.name)

    if not path.exists():
        raise IVAFileNotFoundError(
            user_message="Input file was not found.",
            technical_details=f"Full path checked: {path}",
            recovery_hint="Check that the file path is correct and the file has not been moved.",
        )

    file_size = path.stat().st_size

    try:
        encoding = _detect_encoding(path)
        raw_text = path.read_text(encoding=encoding, errors="replace")
    except OSError as exc:
        raise FileReadError(
            user_message="The CSV file could not be read. "
            "Check the file encoding, delimiter and table structure.",
            technical_details=str(exc),
        ) from exc

    # ``errors="replace"`` substitutes undecodable bytes with U+FFFD rather than
    # failing.  If any appear, the detected encoding is likely wrong; warn so the
    # silent substitution does not masquerade as clean data.
    if "�" in raw_text:
        logger.warning(
            "CSV reader: replacement characters were introduced while decoding "
            "'%s' with encoding '%s'; the file encoding may be incorrect.",
            path.name,
            encoding,
        )

    cleaned_text = _strip_comments(raw_text)

    # Use the first 8 KB as a sample for dialect detection.
    sample = cleaned_text[:8192]
    delimiter = _detect_delimiter(sample)
    header_present = _has_header(sample, delimiter)
    header_row: int | None = 0 if header_present else None

    try:
        df = pd.read_csv(
            io.StringIO(cleaned_text),
            sep=delimiter,
            header=header_row,
            dtype=str,  # read everything as string first, then let caller convert
            skipinitialspace=True,
        )
    except Exception as exc:
        raise FileReadError(
            user_message="The CSV file could not be read. "
            "Check the file encoding, delimiter and table structure.",
            technical_details=f"pandas error: {exc}",
        ) from exc

    if not header_present:
        df.columns = [f"column_{i}" for i in range(len(df.columns))]
    else:
        df.columns = [str(c).strip() for c in df.columns]

    column_names = tuple(str(c) for c in df.columns)
    column_dtypes = {col: str(df[col].dtype) for col in df.columns}
    row_count = len(df)

    # Warn if no obvious time-like column is present.
    lower_cols = {c.lower() for c in column_names}
    if not lower_cols.intersection(_TIME_COLUMN_HINTS):
        logger.warning(
            "CSV reader: no obvious time column found in '%s'. " "Expected one of: %s",
            path.name,
            ", ".join(sorted(_TIME_COLUMN_HINTS)),
        )

    logger.info(
        "CSV read completed: '%s' — %d rows, %d columns, encoding=%s, delimiter=%r",
        path.name,
        row_count,
        len(column_names),
        encoding,
        delimiter,
    )

    return RawFileData(
        file_path=path,
        file_format="csv",
        column_names=column_names,
        column_dtypes=column_dtypes,
        row_count=row_count,
        file_size_bytes=file_size,
        data=df,
        read_timestamp=datetime.now(),
    )
