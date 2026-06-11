"""Regression tests for the pre-commit trailing-whitespace hook."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "strip_trailing_whitespace.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("strip_trailing_whitespace", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_clean_file_removes_only_trailing_horizontal_whitespace(tmp_path):
    module = _load_module()
    sample = tmp_path / "sample.txt"
    sample.write_bytes(b"keep  middle \r\ntrim-me\t\nlast line")

    assert module.clean_file(sample) is True
    assert sample.read_bytes() == b"keep  middle\r\ntrim-me\nlast line"


def test_clean_file_does_not_rewrite_clean_content(tmp_path):
    module = _load_module()
    sample = tmp_path / "clean.txt"
    original = b"first\r\nsecond\n"
    sample.write_bytes(original)

    assert module.clean_file(sample) is False
    assert sample.read_bytes() == original


def test_clean_file_preserves_markdown_hard_break(tmp_path):
    module = _load_module()
    sample = tmp_path / "document.md"
    sample.write_bytes(b"hard break  \nordinary trailing space \n")

    assert module.clean_file(sample) is True
    assert sample.read_bytes() == b"hard break  \nordinary trailing space\n"
