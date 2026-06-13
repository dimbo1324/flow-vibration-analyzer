"""In-process upload store for managing uploaded files.

Files are written to out/web/uploads/ and metadata is kept in memory.
The store survives the lifetime of the server process; restart clears it.

Architecture rules:
- No PySide6 imports.
- No scientific calculations.
- Paths returned to callers are absolute; paths sent to the frontend MUST NOT
  include absolute server paths (the route layer strips them).
"""

from __future__ import annotations

import hashlib
import os
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock

__all__ = ["UploadedFileMeta", "upload_store"]

# Configurable cap — default 100 MB
_MAX_UPLOAD_BYTES: int = int(os.environ.get("IVA_WEB_MAX_UPLOAD_MB", "100")) * 1024 * 1024

# Where uploaded files land
_UPLOAD_DIR = Path("out") / "web" / "uploads"

# Allowed extensions (lower-case)
ALLOWED_EXTENSIONS: frozenset[str] = frozenset({".csv", ".txt", ".xlsx", ".parquet"})


@dataclass
class UploadedFileMeta:
    """Metadata for one uploaded file stored in the upload store."""

    file_id: str
    original_name: str  # sanitised — no path components
    saved_path: Path  # absolute server path (never sent to frontend)
    size_bytes: int
    extension: str
    uploaded_at: datetime
    sha256: str

    def to_response_dict(self) -> dict:  # type: ignore[type-arg]
        """Return a frontend-safe dict (no absolute paths)."""
        return {
            "file_id": self.file_id,
            "original_name": self.original_name,
            "size_bytes": self.size_bytes,
            "extension": self.extension,
            "uploaded_at": self.uploaded_at.isoformat(),
        }


class _UploadStore:
    """Thread-safe in-memory store for uploaded-file metadata."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._store: dict[str, UploadedFileMeta] = {}

    # ------------------------------------------------------------------
    # Write path
    # ------------------------------------------------------------------

    def accept(
        self,
        data: bytes,
        original_filename: str,
    ) -> UploadedFileMeta:
        """Validate *data*, persist it, and return metadata.

        Args:
            data: Raw bytes of the uploaded file.
            original_filename: Browser-supplied name (may be unsafe — sanitised here).

        Returns:
            Metadata for the stored file.

        Raises:
            ValueError: Extension not allowed or file too large.
        """
        if len(data) > _MAX_UPLOAD_BYTES:
            max_mb = _MAX_UPLOAD_BYTES // (1024 * 1024)
            raise ValueError(f"Файл превышает допустимый размер {max_mb} МБ.")

        # Sanitise filename: take only the basename, strip path separators
        safe_name = Path(original_filename).name.replace("..", "").strip()
        if not safe_name:
            safe_name = "upload"

        ext = Path(safe_name).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            supported = ", ".join(sorted(ALLOWED_EXTENSIONS))
            raise ValueError(
                f"Формат файла '{ext}' не поддерживается. " f"Поддерживаемые форматы: {supported}."
            )

        file_id = str(uuid.uuid4())
        sha256 = hashlib.sha256(data).hexdigest()

        _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        saved_path = _UPLOAD_DIR / f"{file_id}{ext}"
        saved_path.write_bytes(data)

        meta = UploadedFileMeta(
            file_id=file_id,
            original_name=safe_name,
            saved_path=saved_path.resolve(),
            size_bytes=len(data),
            extension=ext,
            uploaded_at=datetime.now(tz=UTC),
            sha256=sha256,
        )

        with self._lock:
            self._store[file_id] = meta

        return meta

    # ------------------------------------------------------------------
    # Read path
    # ------------------------------------------------------------------

    def get(self, file_id: str) -> UploadedFileMeta | None:
        """Return metadata for *file_id*, or None if unknown."""
        with self._lock:
            return self._store.get(file_id)

    def delete(self, file_id: str) -> bool:
        """Remove metadata and the file on disk. Returns True if found."""
        with self._lock:
            meta = self._store.pop(file_id, None)
        if meta is None:
            return False
        try:
            meta.saved_path.unlink(missing_ok=True)
        except OSError:
            pass
        return True

    def preview(self, file_id: str, max_rows: int = 10) -> dict | None:  # type: ignore[type-arg]
        """Return column names and first *max_rows* rows for *file_id*.

        Returns None if the file is unknown. Raises on read failure.
        """
        meta = self.get(file_id)
        if meta is None:
            return None

        import pandas as pd

        ext = meta.extension
        try:
            if ext in {".csv", ".txt"}:
                df = pd.read_csv(meta.saved_path, nrows=max_rows)
            elif ext in {".xlsx"}:
                df = pd.read_excel(meta.saved_path, nrows=max_rows)
            elif ext == ".parquet":
                df = pd.read_parquet(meta.saved_path)
                df = df.head(max_rows)
            else:
                raise ValueError(f"Cannot preview extension '{ext}'")
        except Exception as exc:
            raise RuntimeError(f"Preview failed: {exc}") from exc

        # Replace NaN with None for JSON safety
        rows = df.where(df.notna(), other=None).to_dict(orient="records")
        return {
            "columns": list(df.columns),
            "rows": rows,
            "total_preview_rows": len(rows),
        }


# Module-level singleton
upload_store = _UploadStore()
