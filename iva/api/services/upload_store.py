"""In-process хранилище загруженных файлов.

Файлы сохраняются в out/web/uploads/, метаданные хранятся в памяти.
Хранилище живёт весь процесс сервера — перезапуск очищает его.

Архитектурные ограничения:
- PySide6 не импортируется.
- Научные вычисления не выполняются.
- Серверные абсолютные пути никогда не передаются фронтенду.
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

# Максимальный размер файла; настраивается через переменную среды.
_MAX_UPLOAD_BYTES: int = int(os.environ.get("IVA_WEB_MAX_UPLOAD_MB", "100")) * 1024 * 1024

# Каталог для сохранения загруженных файлов (внутри out/, который исключён из .git).
_UPLOAD_DIR = Path("out") / "web" / "uploads"

# Допустимые расширения файлов (в нижнем регистре).
ALLOWED_EXTENSIONS: frozenset[str] = frozenset({".csv", ".txt", ".xlsx", ".parquet"})

# Magic bytes for binary formats.
_XLSX_MAGIC = b"PK"  # XLSX is a ZIP archive
_PARQUET_MAGIC = b"PAR1"


def _validate_content_bytes(data: bytes, ext: str) -> None:
    """Check file content matches the declared extension.

    Raises:
        ValueError: Content is inconsistent with the declared extension.
    """
    if ext in {".csv", ".txt"}:
        sample = data[:4096]
        for encoding in ("utf-8", "cp1251", "latin-1"):
            try:
                sample.decode(encoding)
                return
            except UnicodeDecodeError:
                continue
        raise ValueError(
            "Файл не является текстовым. Убедитесь, что файл имеет формат CSV или TXT."
        )
    elif ext == ".xlsx":
        if not data[:2] == _XLSX_MAGIC:
            raise ValueError("Файл не является корректным Excel-файлом (.xlsx).")
    elif ext == ".parquet":
        if len(data) < 8 or data[:4] != _PARQUET_MAGIC or data[-4:] != _PARQUET_MAGIC:
            raise ValueError("Файл не является корректным Parquet-файлом.")


@dataclass
class UploadedFileMeta:
    """Метаданные одного загруженного файла."""

    file_id: str
    original_name: str  # санированное имя без компонентов пути
    saved_path: Path  # абсолютный путь на сервере — никогда не возвращается фронтенду
    size_bytes: int
    extension: str
    uploaded_at: datetime
    sha256: str

    def to_response_dict(self) -> dict[str, str | int]:
        """Вернуть безопасный для фронтенда словарь (без абсолютных путей)."""
        return {
            "file_id": self.file_id,
            "original_name": self.original_name,
            "size_bytes": self.size_bytes,
            "extension": self.extension,
            "uploaded_at": self.uploaded_at.isoformat(),
        }


class _UploadStore:
    """Потокобезопасное in-memory хранилище метаданных загруженных файлов."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._store: dict[str, UploadedFileMeta] = {}

    def accept(
        self,
        data: bytes,
        original_filename: str,
    ) -> UploadedFileMeta:
        """Проверить *data*, сохранить файл на диск и вернуть метаданные.

        Args:
            data: Байты загруженного файла.
            original_filename: Имя файла от браузера (может быть небезопасным — санируется здесь).

        Returns:
            Метаданные сохранённого файла.

        Raises:
            ValueError: Расширение не разрешено или файл слишком большой.
        """
        if len(data) > _MAX_UPLOAD_BYTES:
            max_mb = _MAX_UPLOAD_BYTES // (1024 * 1024)
            raise ValueError(f"Файл превышает допустимый размер {max_mb} МБ.")

        # Берём только basename: убираем компоненты пути и двойные точки.
        safe_name = Path(original_filename).name.replace("..", "").strip()
        if not safe_name:
            safe_name = "upload"

        ext = Path(safe_name).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            supported = ", ".join(sorted(ALLOWED_EXTENSIONS))
            raise ValueError(
                f"Формат файла '{ext}' не поддерживается. Поддерживаемые форматы: {supported}."
            )

        _validate_content_bytes(data, ext)

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

    def get(self, file_id: str) -> UploadedFileMeta | None:
        """Вернуть метаданные по *file_id* или None, если файл неизвестен."""
        with self._lock:
            return self._store.get(file_id)

    def delete(self, file_id: str) -> bool:
        """Удалить метаданные и файл на диске. Возвращает True, если файл был найден."""
        with self._lock:
            meta = self._store.pop(file_id, None)
        if meta is None:
            return False
        try:
            meta.saved_path.unlink(missing_ok=True)
        except OSError:
            pass
        return True

    def preview(self, file_id: str, max_rows: int = 10) -> dict[str, object] | None:
        """Вернуть имена столбцов и первые *max_rows* строк файла.

        Возвращает None, если файл не найден. Генерирует исключение при ошибке чтения.
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
                raise ValueError(f"Предпросмотр расширения '{ext}' не поддерживается.")
        except Exception as exc:
            raise RuntimeError(f"Предпросмотр не удался: {exc}") from exc

        # NaN заменяем на None для корректной сериализации в JSON.
        rows = df.where(df.notna(), other=None).to_dict(orient="records")
        return {
            "columns": list(df.columns),
            "rows": rows,
            "total_preview_rows": len(rows),
        }


# Синглтон уровня модуля.
upload_store = _UploadStore()
