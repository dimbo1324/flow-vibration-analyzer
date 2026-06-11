"""Smoke-level tests for Stage 1 — project foundation."""

import importlib
import sys

import pytest


def test_version_is_correct() -> None:
    from iva.__version__ import __version__

    assert __version__ == "0.1.0"


def test_iva_package_exposes_version() -> None:
    import iva

    assert iva.__version__ == "0.1.0"


def test_main_runs_without_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    import main

    monkeypatch.setattr(sys, "argv", ["main.py", "--smoke-test"])
    assert main.main() == 0


def test_iva_package_is_importable() -> None:
    importlib.import_module("iva")
