"""Security-focused tests for upload handling."""

from __future__ import annotations

import pytest

from iva.api.services.upload_store import _UploadStore


@pytest.fixture()
def store() -> _UploadStore:
    return _UploadStore()


def _csv_bytes() -> bytes:
    return b"time_s,signal\n0.0,1.0\n"


def test_path_traversal_filename_sanitised(store: _UploadStore) -> None:
    """../../etc/passwd type filenames must be sanitised to just a basename."""
    meta = store.accept(_csv_bytes(), "../../etc/passwd.csv")
    assert ".." not in str(meta.saved_path)
    assert meta.original_name == "passwd.csv"
    store.delete(meta.file_id)


def test_path_traversal_with_backslash(store: _UploadStore) -> None:
    meta = store.accept(_csv_bytes(), r"..\..\windows\system32.csv")
    assert ".." not in meta.original_name
    store.delete(meta.file_id)


def test_response_dict_hides_server_path(store: _UploadStore) -> None:
    meta = store.accept(_csv_bytes(), "safe.csv")
    d = meta.to_response_dict()
    # Absolute path must never reach frontend
    for v in d.values():
        assert not str(v).startswith("/") or str(v).startswith("/20")  # ISO date starts with year
        assert "\\" not in str(v)
    store.delete(meta.file_id)


def test_extension_case_insensitive(store: _UploadStore) -> None:
    meta = store.accept(_csv_bytes(), "DATA.CSV")
    assert meta.extension == ".csv"
    store.delete(meta.file_id)


def test_txt_extension_allowed(store: _UploadStore) -> None:
    meta = store.accept(_csv_bytes(), "log.txt")
    assert meta.extension == ".txt"
    store.delete(meta.file_id)


def test_pdf_rejected(store: _UploadStore) -> None:
    with pytest.raises(ValueError, match="не поддерживается"):
        store.accept(b"%PDF-1.4", "report.pdf")


def test_zip_rejected(store: _UploadStore) -> None:
    with pytest.raises(ValueError, match="не поддерживается"):
        store.accept(b"PK\x03\x04", "archive.zip")
