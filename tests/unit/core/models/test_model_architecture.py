"""Architecture boundary test: iva/core/models/ must not import forbidden modules."""

from __future__ import annotations

import ast
from pathlib import Path

_MODELS_DIR = Path(__file__).resolve().parents[4] / "iva" / "core" / "models"

_FORBIDDEN = ("iva.ui", "iva.app", "iva.infrastructure", "PySide6")


def _collect_imports(source: str) -> list[str]:
    """Return all top-level module names referenced in import statements."""
    tree = ast.parse(source)
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.append(node.module)
    return modules


def _python_files() -> list[Path]:
    return list(_MODELS_DIR.glob("*.py"))


class TestModelArchitectureBoundaries:
    def test_no_forbidden_imports(self) -> None:
        violations: list[str] = []
        for path in _python_files():
            source = path.read_text(encoding="utf-8")
            imports = _collect_imports(source)
            for imp in imports:
                for forbidden in _FORBIDDEN:
                    if imp == forbidden or imp.startswith(forbidden + "."):
                        violations.append(f"{path.name}: imports '{imp}'")
        assert violations == [], "Architecture boundary violated:\n" + "\n".join(violations)

    def test_models_dir_has_python_files(self) -> None:
        assert len(_python_files()) > 0, f"No Python files found in {_MODELS_DIR}"
