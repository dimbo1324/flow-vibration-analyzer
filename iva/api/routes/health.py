"""Health check endpoint."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from iva.__version__ import __version__

router = APIRouter()


@router.get("/api/health")
async def health() -> JSONResponse:
    """Return a simple liveness response."""
    return JSONResponse(
        {
            "status": "ok",
            "app": "Industrial Vibration Analyzer",
            "version": __version__,
        }
    )
