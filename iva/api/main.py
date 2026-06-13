"""FastAPI application entry point for Industrial Vibration Analyzer.

Architecture rules (enforced by tests/unit/api/test_api_architecture.py):
- MUST NOT import PySide6 or iva.ui anywhere in iva.api.
- All scientific calculations remain in iva.core.
- Error responses never include Python tracebacks.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from iva.api.errors import api_error_response, register_error_handlers
from iva.api.limiter import limiter
from iva.api.routes.analysis import router as analysis_router
from iva.api.routes.demo import router as demo_router
from iva.api.routes.files import router as files_router
from iva.api.routes.health import router as health_router
from iva.api.routes.reports import router as reports_router
from iva.api.routes.sessions import router as sessions_router
from iva.api.security import configure_cors

app = FastAPI(
    title="Industrial Vibration Analyzer API",
    description="Web API for the IVA vibration analysis backend.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.state.limiter = limiter


async def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return api_error_response(429, "RATE_LIMITED", "Слишком много запросов. Повторите позже.")


app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)  # type: ignore[arg-type]

configure_cors(app)
register_error_handlers(app)

app.include_router(health_router)
app.include_router(demo_router)
app.include_router(files_router)
app.include_router(analysis_router)
app.include_router(reports_router)
app.include_router(sessions_router)
