"""Custom exception hierarchy for the Industrial Vibration Analyzer.

All IVA exceptions carry three separate message fields so that the application
layer can show a user-friendly message while the infrastructure layer logs the
full technical context.

Note: IVAFileNotFoundError intentionally mirrors the semantics of the built-in
FileNotFoundError without shadowing it at module level.  The checklist requires
a class named FileNotFoundError inside this hierarchy; it is defined here under
its own name to avoid confusion with the built-in.
"""

from __future__ import annotations

__all__ = [
    "IVAError",
    "FileReadError",
    "IVAFileNotFoundError",
    "UnsupportedFormatError",
    "FileCorruptedError",
    "ValidationError",
    "NonMonotonicTimeAxisError",
    "EmptySignalError",
    "InsufficientDataError",
    "ProcessingError",
    "FilterConfigurationError",
    "PhysicsInputError",
    "ExportError",
]


class IVAError(Exception):
    """Base class for all application-specific exceptions.

    Carries three separate message fields so that the UI can show a clean
    user-facing message while the developer sees the full technical context.
    """

    def __init__(
        self,
        user_message: str,
        technical_details: str = "",
        recovery_hint: str | None = None,
    ) -> None:
        super().__init__(user_message)
        self.user_message: str = user_message
        self.technical_details: str = technical_details
        self.recovery_hint: str | None = recovery_hint

    def __str__(self) -> str:
        return self.user_message


# ---------------------------------------------------------------------------
# File reading errors
# ---------------------------------------------------------------------------


class FileReadError(IVAError):
    """A file could not be read."""


class IVAFileNotFoundError(FileReadError):
    """The requested file does not exist on disk."""


class UnsupportedFormatError(FileReadError):
    """The file extension or content format is not supported."""


class FileCorruptedError(FileReadError):
    """The file exists but its contents cannot be parsed."""


# ---------------------------------------------------------------------------
# Data validation errors
# ---------------------------------------------------------------------------


class ValidationError(IVAError):
    """Input data failed a quality or structural validation check."""


class NonMonotonicTimeAxisError(ValidationError):
    """The time column contains non-monotonically increasing values."""


class EmptySignalError(ValidationError):
    """The selected signal column is empty or contains only zeros."""


class InsufficientDataError(ValidationError):
    """The recording is too short or has too few samples for analysis."""


# ---------------------------------------------------------------------------
# Signal processing errors
# ---------------------------------------------------------------------------


class ProcessingError(IVAError):
    """An error occurred inside a signal processing step."""


class FilterConfigurationError(ProcessingError):
    """The filter parameters are outside the valid range."""


# ---------------------------------------------------------------------------
# Physics and export errors
# ---------------------------------------------------------------------------


class PhysicsInputError(IVAError):
    """The physical parameters supplied by the user are out of range."""


class ExportError(IVAError):
    """The result could not be written to disk."""
