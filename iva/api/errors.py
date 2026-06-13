"""Unified error handling for the API — no tracebacks to frontend."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from iva.core.models.exceptions import IVAError, ValidationError

__all__ = ["register_error_handlers", "api_error_response"]


def api_error_response(
    status_code: int,
    code: str,
    message: str,
    details: str | None = None,
) -> JSONResponse:
    """Return a standardised error JSON response."""
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "details": details}},
    )


def register_error_handlers(app) -> None:  # type: ignore[no-untyped-def]
    """Register global exception handlers that never leak tracebacks."""

    @app.exception_handler(ValidationError)
    async def _validation_error(request: Request, exc: ValidationError) -> JSONResponse:
        return api_error_response(400, "VALIDATION_ERROR", exc.user_message)

    @app.exception_handler(IVAError)
    async def _iva_error(request: Request, exc: IVAError) -> JSONResponse:
        return api_error_response(500, "PIPELINE_ERROR", exc.user_message)

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        return api_error_response(500, "INTERNAL_ERROR", "Внутренняя ошибка сервера.")
