"""Session save/load endpoints.

POST /api/sessions/export/{analysis_id}  — save .vibproj, return file download
POST /api/sessions/import               — upload .vibproj, return compact summary
"""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from iva.api.errors import api_error_response
from iva.api.services.analysis_service import analysis_service
from iva.api.utils import validate_resource_id
from iva.app.session_service import load_saved_session, save_current_session
from iva.core.models.exceptions import ExportError, ValidationError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/sessions", tags=["sessions"])

_SESSIONS_DIR = Path("out") / "web" / "sessions"


@router.post("/export/{analysis_id}", response_model=None)
async def export_session(analysis_id: str) -> FileResponse | JSONResponse:
    """Create a .vibproj from a completed analysis and stream it to the browser."""
    stored = analysis_service.get(analysis_id)
    if stored is None:
        return api_error_response(404, "ANALYSIS_NOT_FOUND", "Результат анализа не найден.")

    try:
        validate_resource_id(analysis_id)
    except ValueError:
        return api_error_response(400, "INVALID_ID", "Некорректный идентификатор.")

    sessions_dir = (_SESSIONS_DIR / analysis_id).resolve()
    sessions_dir.mkdir(parents=True, exist_ok=True)
    dest = sessions_dir / "session.vibproj"

    try:
        save_current_session(stored.session, dest)
    except ExportError as exc:
        return api_error_response(500, "EXPORT_ERROR", exc.user_message)
    except Exception:  # noqa: BLE001
        logger.exception("export_session: unexpected error")
        return api_error_response(500, "INTERNAL_ERROR", "Ошибка при сохранении сессии.")

    safe_name = f"iva_session_{analysis_id[:8]}.vibproj"
    return FileResponse(
        path=str(dest),
        media_type="application/json",
        filename=safe_name,
        headers={"Content-Disposition": f'attachment; filename="{safe_name}"'},
    )


@router.post("/import", response_model=None)
async def import_session(file: UploadFile) -> JSONResponse:
    """Accept a .vibproj upload and return a compact session summary."""
    if file.filename is None:
        return api_error_response(400, "NO_FILE", "Файл не выбран.")

    ext = Path(file.filename).suffix.lower()
    if ext != ".vibproj":
        return api_error_response(
            400,
            "INVALID_FORMAT",
            "Ожидается файл .vibproj.",
        )

    data = await file.read()
    if len(data) > 50 * 1024 * 1024:  # 50 MB cap for session files
        return api_error_response(400, "FILE_TOO_LARGE", "Файл сессии слишком большой.")

    # Write to a temp file, load it, then discard
    with tempfile.NamedTemporaryFile(suffix=".vibproj", delete=False) as tmp:
        tmp.write(data)
        tmp_path = Path(tmp.name)

    try:
        session = load_saved_session(tmp_path)
    except ValidationError as exc:
        tmp_path.unlink(missing_ok=True)
        return api_error_response(400, "INVALID_SESSION", exc.user_message)
    except Exception:  # noqa: BLE001
        logger.exception("import_session: parse error")
        tmp_path.unlink(missing_ok=True)
        return api_error_response(
            400,
            "INVALID_SESSION",
            "Не удалось разобрать файл сессии. Убедитесь, что файл не повреждён.",
        )
    finally:
        tmp_path.unlink(missing_ok=True)

    # Build compact summary — avoid exposing server paths
    result = session.result
    summary: dict[str, object] = {}
    if result is not None:
        from iva.api.serializers.analysis_serializer import serialize_analysis_result

        summary = serialize_analysis_result(result)

    source_file_name: str | None = None
    if session.source_file_path is not None:
        source_file_name = session.source_file_path.name

    return JSONResponse(
        content={
            "status": "loaded",
            "is_demo": session.is_demo,
            "demo_title": session.demo_title,
            "demo_description": session.demo_description,
            "source_file_name": source_file_name,
            "source_file_available": False,  # uploaded .vibproj never has access to original file
            "has_result": result is not None,
            "result": summary,
            "warnings": (
                ["Файл исходных данных недоступен. Для повторного анализа загрузите файл заново."]
                if source_file_name
                else []
            ),
        }
    )
