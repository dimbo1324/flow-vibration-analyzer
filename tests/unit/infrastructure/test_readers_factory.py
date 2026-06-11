"""Unit tests for iva.infrastructure.readers (factory read_file)."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from iva.core.models.exceptions import UnsupportedFormatError
from iva.infrastructure.readers import read_file


def _write_csv(content: str) -> Path:
    fd, name = tempfile.mkstemp(suffix=".csv")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(content)
    return Path(name)


def _write_parquet(df: pd.DataFrame) -> Path:
    fd, name = tempfile.mkstemp(suffix=".parquet")
    os.close(fd)
    p = Path(name)
    df.to_parquet(p, index=False)
    return p


def test_read_file_csv_dispatched():
    """read_file dispatches .csv extension to the CSV reader."""
    p = _write_csv("time_s,signal\n0.0,1.0\n0.001,1.1\n")
    try:
        result = read_file(str(p))
        assert result.file_format == "csv"
    finally:
        p.unlink(missing_ok=True)


def test_read_file_parquet_dispatched():
    """read_file dispatches .parquet extension to the Parquet reader."""
    df = pd.DataFrame({"time_s": [0.0, 0.001], "signal": [1.0, 1.1]})
    p = _write_parquet(df)
    try:
        result = read_file(str(p))
        assert result.file_format == "parquet"
    finally:
        p.unlink(missing_ok=True)


def test_read_file_unsupported_extension():
    """UnsupportedFormatError is raised for an unknown file extension."""
    with pytest.raises(UnsupportedFormatError):
        read_file("/some/path/file.txt")
