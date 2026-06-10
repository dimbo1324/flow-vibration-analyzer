"""Tests for the IVA custom exception hierarchy."""

from __future__ import annotations

import pytest

from iva.core.models.exceptions import (
    EmptySignalError,
    ExportError,
    FileCorruptedError,
    FileReadError,
    FilterConfigurationError,
    InsufficientDataError,
    IVAError,
    IVAFileNotFoundError,
    NonMonotonicTimeAxisError,
    PhysicsInputError,
    ProcessingError,
    UnsupportedFormatError,
    ValidationError,
)


class TestIVAError:
    def test_stores_user_message(self) -> None:
        err = IVAError("Something went wrong")
        assert err.user_message == "Something went wrong"

    def test_str_returns_user_message(self) -> None:
        err = IVAError("User-facing text")
        assert str(err) == "User-facing text"

    def test_stores_technical_details(self) -> None:
        err = IVAError("msg", technical_details="Stack trace here")
        assert err.technical_details == "Stack trace here"

    def test_stores_recovery_hint(self) -> None:
        err = IVAError("msg", recovery_hint="Try again with a different file.")
        assert err.recovery_hint == "Try again with a different file."

    def test_recovery_hint_defaults_to_none(self) -> None:
        err = IVAError("msg")
        assert err.recovery_hint is None

    def test_technical_details_defaults_to_empty_string(self) -> None:
        err = IVAError("msg")
        assert err.technical_details == ""

    def test_is_exception(self) -> None:
        with pytest.raises(IVAError):
            raise IVAError("boom")


class TestFileReadErrorHierarchy:
    def test_file_read_error_is_iva_error(self) -> None:
        assert issubclass(FileReadError, IVAError)

    def test_iva_file_not_found_is_file_read_error(self) -> None:
        assert issubclass(IVAFileNotFoundError, FileReadError)

    def test_unsupported_format_is_file_read_error(self) -> None:
        assert issubclass(UnsupportedFormatError, FileReadError)

    def test_file_corrupted_is_file_read_error(self) -> None:
        assert issubclass(FileCorruptedError, FileReadError)

    def test_all_carry_user_message(self) -> None:
        for cls in (IVAFileNotFoundError, UnsupportedFormatError, FileCorruptedError):
            err = cls("test message")
            assert str(err) == "test message"


class TestValidationErrorHierarchy:
    def test_validation_error_is_iva_error(self) -> None:
        assert issubclass(ValidationError, IVAError)

    def test_non_monotonic_is_validation_error(self) -> None:
        assert issubclass(NonMonotonicTimeAxisError, ValidationError)

    def test_empty_signal_is_validation_error(self) -> None:
        assert issubclass(EmptySignalError, ValidationError)

    def test_insufficient_data_is_validation_error(self) -> None:
        assert issubclass(InsufficientDataError, ValidationError)


class TestProcessingErrorHierarchy:
    def test_processing_error_is_iva_error(self) -> None:
        assert issubclass(ProcessingError, IVAError)

    def test_filter_configuration_is_processing_error(self) -> None:
        assert issubclass(FilterConfigurationError, ProcessingError)


class TestOtherErrors:
    def test_physics_input_error_is_iva_error(self) -> None:
        assert issubclass(PhysicsInputError, IVAError)

    def test_export_error_is_iva_error(self) -> None:
        assert issubclass(ExportError, IVAError)
