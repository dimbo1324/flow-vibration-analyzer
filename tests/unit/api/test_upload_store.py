"""Unit tests for the upload store."""

from __future__ import annotations

import pytest

from iva.api.services.upload_store import _UploadStore


@pytest.fixture()
def store() -> _UploadStore:
    return _UploadStore()


def _csv_bytes() -> bytes:
    return b"time_s,signal\n0.0,1.0\n0.001,2.0\n"


def test_accept_valid_csv(store: _UploadStore) -> None:
    meta = store.accept(_csv_bytes(), "test.csv")
    assert meta.extension == ".csv"
    assert meta.size_bytes == len(_csv_bytes())
    assert meta.original_name == "test.csv"
    assert len(meta.sha256) == 64


def test_accept_stores_in_memory(store: _UploadStore) -> None:
    meta = store.accept(_csv_bytes(), "data.csv")
    assert store.get(meta.file_id) is meta


def test_accept_saves_file_on_disk(store: _UploadStore) -> None:
    meta = store.accept(_csv_bytes(), "disk.csv")
    assert meta.saved_path.exists()
    # cleanup
    store.delete(meta.file_id)


def test_reject_unsupported_extension(store: _UploadStore) -> None:
    with pytest.raises(ValueError, match="не поддерживается"):
        store.accept(b"data", "bad.exe")


def test_reject_oversized_file(store: _UploadStore, monkeypatch: pytest.MonkeyPatch) -> None:
    import iva.api.services.upload_store as mod

    monkeypatch.setattr(mod, "_MAX_UPLOAD_BYTES", 10)
    with pytest.raises(ValueError, match="превышает"):
        store.accept(b"x" * 20, "large.csv")


def test_delete_removes_file(store: _UploadStore) -> None:
    meta = store.accept(_csv_bytes(), "del.csv")
    path = meta.saved_path
    assert path.exists()
    removed = store.delete(meta.file_id)
    assert removed is True
    assert not path.exists()
    assert store.get(meta.file_id) is None


def test_delete_unknown_returns_false(store: _UploadStore) -> None:
    assert store.delete("nonexistent-id") is False


def test_to_response_dict_no_absolute_path(store: _UploadStore) -> None:
    meta = store.accept(_csv_bytes(), "resp.csv")
    d = meta.to_response_dict()
    assert "saved_path" not in d
    assert "file_id" in d
    store.delete(meta.file_id)
