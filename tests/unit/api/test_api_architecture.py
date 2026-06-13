"""Architecture boundary tests — api layer must not touch ui layer."""

from __future__ import annotations

import ast
from pathlib import Path


def _collect_imports(source: str) -> list[str]:
    """Return all top-level module names imported in *source*."""
    tree = ast.parse(source)
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.append(node.module)
    return names


def test_api_files_do_not_import_ui_or_pyside6() -> None:
    """No file under iva/api/ imports iva.ui or PySide6."""
    api_root = Path(__file__).resolve().parents[3] / "iva" / "api"
    assert api_root.exists(), f"iva/api/ not found at {api_root}"

    violations: list[str] = []
    for py_file in api_root.rglob("*.py"):
        source = py_file.read_text(encoding="utf-8")
        imports = _collect_imports(source)
        for imp in imports:
            if imp.startswith("iva.ui") or imp.startswith("PySide6"):
                violations.append(f"{py_file.name}: imports {imp!r}")

    assert not violations, "Architecture violation — api imports ui:\n" + "\n".join(violations)
