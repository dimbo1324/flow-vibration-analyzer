"""Тесты состава безопасной диагностики проекта."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "scripts"
sys.path.insert(0, str(_SCRIPTS_DIR))

import diagnose_project  # noqa: E402


def test_collect_reports_version_docs_and_automation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("IVA_OUT_DIR", str(tmp_path / "out"))
    monkeypatch.setattr(
        diagnose_project,
        "_git_info",
        lambda: {"branch": "test", "status": "", "last_commit": "abc test"},
    )
    monkeypatch.setattr(diagnose_project, "_pkg_version", lambda _name: "test-version")

    report = "\n".join(diagnose_project.collect())

    assert "App version: 1.0.0" in report
    assert "docs/ present       : yes" in report
    assert "documentation/ stale: absent" in report
    assert "iva.ps1" in report
    assert "lib/IvaDevTools.psm1" in report
    assert "Latest workflow" in report


def test_main_writes_timestamped_report(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    out_dir = tmp_path / "out"
    monkeypatch.setenv("IVA_OUT_DIR", str(out_dir))
    monkeypatch.setattr(
        diagnose_project,
        "_git_info",
        lambda: {"branch": "test", "status": "", "last_commit": "abc test"},
    )
    monkeypatch.setattr(diagnose_project, "_pkg_version", lambda _name: "test-version")

    diagnose_project.main()

    reports = list((out_dir / "diagnostics").glob("*_diagnostics.txt"))
    assert len(reports) == 1
    assert "App version: 1.0.0" in reports[0].read_text(encoding="utf-8")
