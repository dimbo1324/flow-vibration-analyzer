"""Checks that product-facing errors are presented in Russian."""

from __future__ import annotations

from pathlib import Path

import pytest

from iva.core.models.exceptions import IVAFileNotFoundError, UnsupportedFormatError
from iva.infrastructure.readers import read_file
from iva.infrastructure.readers.csv_reader import read_csv


def test_unsupported_format_error_is_russian() -> None:
    with pytest.raises(UnsupportedFormatError) as caught:
        read_file("measurement.unsupported")

    error = caught.value
    assert "не поддерживается" in error.user_message
    assert error.recovery_hint is not None
    assert "Преобразуйте файл" in error.recovery_hint


def test_localized_error_has_no_replacement_character() -> None:
    with pytest.raises(UnsupportedFormatError) as caught:
        read_file("measurement.unsupported")
    assert "�" not in caught.value.user_message


def test_missing_file_error_is_russian(tmp_path: Path) -> None:
    with pytest.raises(IVAFileNotFoundError) as caught:
        read_csv(str(tmp_path / "missing.csv"))
    assert "Входной файл не найден" in caught.value.user_message
    assert "Проверьте путь" in (caught.value.recovery_hint or "")
