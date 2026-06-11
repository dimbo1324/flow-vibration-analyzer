"""Architecture boundary test: core/spectrum must not import from forbidden layers."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_SPECTRUM_PKG = Path(__file__).resolve().parents[4] / "iva" / "core" / "spectrum"

_FORBIDDEN_PREFIXES = (
    "iva.ui",
    "iva.app",
    "iva.infrastructure",
    "PySide6",
)


def _collect_imports(source: str) -> list[str]:
    tree = ast.parse(source)
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports


@pytest.mark.parametrize(
    "module_path",
    list(_SPECTRUM_PKG.glob("*.py")),
    ids=lambda p: p.name,
)
def test_no_forbidden_imports(module_path: Path) -> None:
    source = module_path.read_text(encoding="utf-8")
    imports = _collect_imports(source)
    violations = [
        imp for imp in imports if any(imp.startswith(prefix) for prefix in _FORBIDDEN_PREFIXES)
    ]
    assert not violations, f"{module_path.name} imports from forbidden layer(s): {violations}"
