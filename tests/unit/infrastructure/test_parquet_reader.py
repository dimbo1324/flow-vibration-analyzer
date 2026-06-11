"""Unit tests for iva.infrastructure.readers.parquet_reader."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd
import pytest

from iva.core.models.exceptions import IVAFileNotFoundError
from iva.infrastructure.readers.parquet_reader import read_parquet


def _write_parquet(df: pd.DataFrame) -> Path:
    fd, name = tempfile.mkstemp(suffix=".parquet")
    import os

    os.close(fd)
    p = Path(name)
    df.to_parquet(p, index=False)
    return p


def test_read_parquet_basic():
    """A valid parquet file is read and returned as RawFileData."""
    df = pd.DataFrame({"time_s": [0.0, 0.001, 0.002], "signal": [1.0, 1.1, 0.9]})
    p = _write_parquet(df)
    try:
        result = read_parquet(str(p))
        assert result.file_format == "parquet"
        assert result.row_count == 3
        assert "time_s" in result.column_names
        assert "signal" in result.column_names
        assert isinstance(result.file_path, Path)
    finally:
        p.unlink(missing_ok=True)


def test_read_parquet_file_not_found():
    """IVAFileNotFoundError is raised for a missing parquet file."""
    with pytest.raises(IVAFileNotFoundError):
        read_parquet("/nonexistent/file.parquet")


def test_read_parquet_large_file_warning(tmp_path, monkeypatch):
    """A file larger than the threshold triggers logger.warning."""
    from unittest.mock import patch

    from iva.infrastructure.readers import parquet_reader

    monkeypatch.setattr(parquet_reader, "_LARGE_FILE_THRESHOLD_BYTES", 1)

    df = pd.DataFrame({"time_s": [0.0, 0.001], "signal": [1.0, 1.1]})
    p = tmp_path / "big.parquet"
    df.to_parquet(p, index=False)

    with patch("iva.infrastructure.readers.parquet_reader.logger") as mock_logger:
        result = read_parquet(str(p))

    assert result.row_count == 2
    calls = [str(c) for c in mock_logger.warning.call_args_list]
    assert any("mb" in c.lower() or "slow" in c.lower() for c in calls)
