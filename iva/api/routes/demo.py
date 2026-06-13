"""Demo analysis endpoints.

POST /api/analysis/demo  — run a built-in demo scenario
GET  /api/demo-scenarios — list available scenarios
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from iva.api.errors import api_error_response
from iva.api.limiter import limiter
from iva.api.schemas.demo import DemoRequest, DemoScenarioItem, DemoScenariosResponse
from iva.api.serializers.analysis_serializer import serialize_analysis_result
from iva.app.analysis_runner import AnalysisRunner
from iva.app.demo_service import create_demo_session, list_available_demo_scenarios
from iva.core.models.exceptions import IVAError, ValidationError
from iva.core.synthetic.demo_scenarios import list_demo_scenarios

router = APIRouter()

_VALID_KEYS: frozenset[str] = frozenset(s.key for s in list_demo_scenarios())


@router.get("/api/demo-scenarios", response_model=DemoScenariosResponse)
async def get_demo_scenarios() -> DemoScenariosResponse:
    """Return all available demo scenario metadata."""
    scenarios = list_available_demo_scenarios()
    items = [
        DemoScenarioItem(
            key=s.key,
            title_ru=s.title_ru,
            description_ru=s.description_ru,
            expected_peak_hz=s.expected_peak_hz,
        )
        for s in scenarios
    ]
    return DemoScenariosResponse(items=items)


@router.post("/api/analysis/demo")
@limiter.limit("60/minute")
async def run_demo_analysis(request: Request, body: DemoRequest) -> JSONResponse:
    """Run a built-in demo scenario and return the full analysis result."""
    if body.scenario_key not in _VALID_KEYS:
        return api_error_response(
            404,
            "UNKNOWN_SCENARIO",
            "Сценарий не найден",
        )

    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            session = create_demo_session(body.scenario_key, output_dir=Path(tmp_dir))
            result = AnalysisRunner().run(session)
            payload = serialize_analysis_result(result)
    except ValidationError as exc:
        return api_error_response(400, "VALIDATION_ERROR", exc.user_message)
    except IVAError as exc:
        return api_error_response(500, "PIPELINE_ERROR", exc.user_message)
    except Exception:  # noqa: BLE001
        return api_error_response(500, "INTERNAL_ERROR", "Внутренняя ошибка сервера.")

    return JSONResponse(content=payload)
