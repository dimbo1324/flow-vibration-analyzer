"""API configuration via environment variables."""

from __future__ import annotations

import os

__all__ = ["get_cors_origins"]

_DEFAULT_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


def get_cors_origins() -> list[str]:
    """Return CORS allowed origins list.

    Uses IVA_API_CORS_ORIGINS env var (comma-separated) or the default
    development origins (localhost:5173 only — no wildcard).
    """
    raw = os.environ.get("IVA_API_CORS_ORIGINS", "").strip()
    if raw:
        return [o.strip() for o in raw.split(",") if o.strip()]
    return list(_DEFAULT_ORIGINS)
