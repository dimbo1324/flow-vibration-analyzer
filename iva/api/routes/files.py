"""File upload endpoints.

POST /api/files/upload              — accept and store an uploaded file
GET  /api/files/{file_id}/preview   — return first N rows and column names
DELETE /api/files/{file_id}         — remove stored file
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, UploadFile
from fastapi.responses import JSONResponse

from iva.api.errors import api_error_response
from iva.api.services.upload_store import upload_store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/files", tags=["files"])


@router.post("/upload", response_model=None)
async def upload_file(file: UploadFile) -> JSONResponse:
    """Accept a multipart file upload, validate and store it."""
    if file.filename is None:
        return api_error_response(400, "NO_FILE", "Файл не выбран.")

    data = await file.read()
    logger.info(
        "upload_file: received '%s' (%d bytes)",
        file.filename,
        len(data),
    )

    try:
        meta = upload_store.accept(data, file.filename)
    except ValueError as exc:
        return api_error_response(400, "UPLOAD_REJECTED", str(exc))
    except Exception:  # noqa: BLE001
        logger.exception("upload_file: unexpected error")
        return api_error_response(500, "INTERNAL_ERROR", "Внутренняя ошибка при загрузке файла.")

    return JSONResponse(content=meta.to_response_dict(), status_code=201)


@router.get("/{file_id}/preview", response_model=None)
async def preview_file(file_id: str, rows: int = 20) -> JSONResponse:
    """Return column names and the first *rows* rows of an uploaded file."""
    capped = min(max(rows, 1), 100)
    try:
        result = upload_store.preview(file_id, max_rows=capped)
    except RuntimeError as exc:
        return api_error_response(422, "PREVIEW_ERROR", str(exc))

    if result is None:
        return api_error_response(404, "FILE_NOT_FOUND", "Файл не найден.")

    return JSONResponse(content=result)


@router.delete("/{file_id}")
async def delete_file(file_id: str) -> JSONResponse:
    """Remove an uploaded file from the store and disk."""
    removed = upload_store.delete(file_id)
    if not removed:
        return api_error_response(404, "FILE_NOT_FOUND", "Файл не найден.")
    return JSONResponse(content={"deleted": file_id}, status_code=200)
