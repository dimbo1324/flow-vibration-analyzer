"""Shared schema types."""

from __future__ import annotations

from pydantic import BaseModel

__all__ = ["ErrorDetail", "ErrorResponse"]


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
