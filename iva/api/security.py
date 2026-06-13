"""CORS configuration for the API."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from iva.api.settings import get_cors_origins

__all__ = ["configure_cors"]


def configure_cors(app: FastAPI) -> None:
    """Attach CORSMiddleware with explicit allowed origins (no wildcard)."""
    origins = get_cors_origins()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Accept"],
    )
