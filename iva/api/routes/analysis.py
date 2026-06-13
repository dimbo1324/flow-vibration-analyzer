"""Analysis endpoints for file-based (non-demo) analysis.

POST /api/analysis/upload          — run analysis on a previously uploaded file
GET  /api/analysis/{analysis_id}   — retrieve a stored analysis result
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from iva.api.errors import api_error_response
from iva.api.limiter import limiter
from iva.api.schemas.upload import UploadAnalysisRequest
from iva.api.services.analysis_service import analysis_service
from iva.core.models.exceptions import IVAError, ValidationError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.post("/upload")
@limiter.limit("30/minute")
async def run_upload_analysis(request: Request, body: UploadAnalysisRequest) -> JSONResponse:
    """Run the analysis pipeline on a previously uploaded file."""
    role_dict = body.role_assignment.model_dump()
    settings_dict = body.settings.model_dump()

    # Flatten nested FlowParametersRequest → plain dict for the service layer
    if body.settings.flow_parameters is not None:
        settings_dict["flow_parameters"] = body.settings.flow_parameters.model_dump()
    else:
        settings_dict["flow_parameters"] = {}

    try:
        stored = analysis_service.run_from_upload(
            file_id=body.file_id,
            role_assignment_dict=role_dict,
            settings_dict=settings_dict,
        )
    except ValueError as exc:
        return api_error_response(404, "FILE_NOT_FOUND", str(exc))
    except ValidationError as exc:
        return api_error_response(400, "VALIDATION_ERROR", exc.user_message)
    except IVAError as exc:
        return api_error_response(500, "PIPELINE_ERROR", exc.user_message)
    except Exception:  # noqa: BLE001
        logger.exception("run_upload_analysis: unexpected error")
        return api_error_response(500, "INTERNAL_ERROR", "Внутренняя ошибка сервера.")

    return JSONResponse(content=stored.payload)


@router.get("/{analysis_id}")
async def get_analysis(analysis_id: str) -> JSONResponse:
    """Retrieve a stored analysis result by ID."""
    stored = analysis_service.get(analysis_id)
    if stored is None:
        return api_error_response(404, "ANALYSIS_NOT_FOUND", "Результат анализа не найден.")
    return JSONResponse(content=stored.payload)
