"""Unit tests for iva.infrastructure.readers.csv_reader."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from iva.core.models.exceptions import IVAFileNotFoundError
from iva.infrastructure.readers.csv_reader import read_csv

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _write(content: str, suffix: str = ".csv") -> Path:
    """Write *content* to a named temporary file and return the Path."""
    fd, name = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(content)
    return Path(name)


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------


def test_read_csv_basic():
    """A well-formed CSV with a header row is parsed into a RawFileData."""
    p = _write("time_s,signal\n0.0,1.0\n0.001,1.1\n0.002,0.9\n")
    try:
        result = read_csv(str(p))
        assert result.file_format == "csv"
        assert "time_s" in result.column_names
        assert "signal" in result.column_names
        assert result.row_count == 3
        assert result.data is not None
    finally:
        p.unlink(missing_ok=True)


def test_read_csv_semicolon_delimiter():
    """CSV with semicolon delimiter is auto-detected and parsed correctly."""
    p = _write("time_s;signal\n0.0;1.0\n0.001;1.1\n0.002;0.9\n")
    try:
        result = read_csv(str(p))
        assert result.row_count == 3
        assert "time_s" in result.column_names
    finally:
        p.unlink(missing_ok=True)


def test_read_csv_comment_lines_stripped():
    """Lines beginning with '#' are stripped before parsing."""
    content = (
        "# This is a comment\n" "# Another comment\n" "time_s,signal\n" "0.0,1.0\n" "0.001,1.1\n"
    )
    p = _write(content)
    try:
        result = read_csv(str(p))
        assert result.row_count == 2
        assert "time_s" in result.column_names
    finally:
        p.unlink(missing_ok=True)


def test_read_csv_formula_injection_treated_as_string():
    """Values starting with = + - @ are not evaluated; they remain strings."""
    p = _write('time_s,signal\n0.0,"=1+1"\n0.001,"+2"\n0.002,"@foo"\n')
    try:
        result = read_csv(str(p))
        assert result.row_count == 3
        # The injected cells must NOT be numeric — they stay as strings.
        first_val = result.data.iloc[0]["signal"]
        assert str(first_val).startswith("=") or str(first_val) == "=1+1"
    finally:
        p.unlink(missing_ok=True)


def test_read_csv_no_time_column_warns():
    """A CSV with no time-like column header triggers logger.warning with 'time'."""
    from unittest.mock import patch

    p = _write("channel_a,channel_b\n1.0,2.0\n1.1,2.1\n")
    try:
        with patch("iva.infrastructure.readers.csv_reader.logger") as mock_logger:
            result = read_csv(str(p))
        assert result.row_count == 2
        calls = [str(c) for c in mock_logger.warning.call_args_list]
        assert any("time" in c.lower() for c in calls)
    finally:
        p.unlink(missing_ok=True)


def test_read_csv_file_not_found():
    """IVAFileNotFoundError is raised when the file does not exist."""
    with pytest.raises(IVAFileNotFoundError):
        read_csv("/nonexistent/path/data.csv")


def test_read_csv_returns_path_object():
    """RawFileData.file_path is a Path, not a plain string."""
    p = _write("time_s,signal\n0.0,1.0\n0.001,1.1\n")
    try:
        result = read_csv(str(p))
        assert isinstance(result.file_path, Path)
    finally:
        p.unlink(missing_ok=True)
