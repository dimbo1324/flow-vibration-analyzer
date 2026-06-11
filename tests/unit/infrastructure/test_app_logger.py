"""Tests for iva.infrastructure.logging.app_logger."""

from __future__ import annotations

import datetime
import logging
from pathlib import Path

import pytest

from iva.infrastructure.logging.app_logger import (
    _cleanup_old_logs,
    configure_file_logging,
    get_logger,
)


def test_get_logger_returns_logger() -> None:
    logger = get_logger("test.module")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test.module"


def test_no_handler_duplication(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("IVA_OUT_DIR", str(tmp_path))
    log_dir = tmp_path / "logs"

    # Remove pre-existing handlers on the iva root logger so this test
    # starts from a clean state.
    root = logging.getLogger("iva")
    for h in list(root.handlers):
        root.removeHandler(h)

    configure_file_logging(log_dir=log_dir)
    configure_file_logging(log_dir=log_dir)  # second call — should be a no-op

    file_handlers = [h for h in root.handlers if isinstance(h, logging.FileHandler)]
    # At most one file handler (deduplication must work)
    assert len(file_handlers) <= 1


def test_configure_file_logging_writes_to_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    log_dir = tmp_path / "logs"

    # Start from clean state
    root = logging.getLogger("iva")
    for h in list(root.handlers):
        root.removeHandler(h)

    configure_file_logging(log_dir=log_dir)
    logger = get_logger("test.write")
    logger.info("test message")

    # Flush all handlers
    for h in logging.getLogger("iva").handlers:
        h.flush()

    log_files = list(log_dir.glob("iva_*.log"))
    assert len(log_files) >= 1


def test_cleanup_only_removes_old_iva_logs(tmp_path: Path) -> None:
    old_log = tmp_path / "iva_2020-01-01.log"
    old_log.write_text("old")

    unrelated = tmp_path / "other_file.txt"
    unrelated.write_text("keep")

    recent_log = tmp_path / f"iva_{datetime.date.today()}.log"
    recent_log.write_text("recent")

    _cleanup_old_logs(tmp_path, keep_days=30)

    assert not old_log.exists(), "Old IVA log should have been deleted"
    assert unrelated.exists(), "Unrelated file must not be deleted"
    assert recent_log.exists(), "Recent IVA log must not be deleted"


def test_cleanup_leaves_non_date_iva_files(tmp_path: Path) -> None:
    """Files that don't match the iva_YYYY-MM-DD.log pattern are skipped."""
    odd_log = tmp_path / "iva_crash_20200101.log"
    odd_log.write_text("crash dump")

    _cleanup_old_logs(tmp_path, keep_days=30)

    assert odd_log.exists(), "Non-date IVA log should not be deleted"
