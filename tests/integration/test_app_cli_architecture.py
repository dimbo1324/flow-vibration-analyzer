"""AST-based architecture boundary tests.

Verifies that ``iva/app/``, ``iva/cli/``, and ``iva/infrastructure/``
do not import forbidden modules (``iva.ui``, ``PySide6``, or ``PyQt5``).

These tests enforce the layer constraints from ``docs/02_architecture.md``.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Packages whose source files must never import the forbidden names
_RESTRICTED_PACKAGES = [
    _PROJECT_ROOT / "iva" / "app",
    _PROJECT_ROOT / "iva" / "cli",
    _PROJECT_ROOT / "iva" / "infrastructure",
]

_FORBIDDEN_MODULES = {"iva.ui", "PySide6", "PyQt5", "PyQt6", "PySide2"}


def _collect_python_files(directory: Path) -> list[Path]:
    """Return all .py files under *directory* recursively."""
    if not directory.exists():
        return []
    return list(directory.rglob("*.py"))


def _extract_imports(source: str) -> list[str]:
    """Return the top-level module names imported in *source*."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported.append(node.module)
    return imported


def _check_package(package_dir: Path) -> list[str]:
    """Return a list of violation strings found in *package_dir*."""
    violations: list[str] = []
    for py_file in _collect_python_files(package_dir):
        try:
            source = py_file.read_text(encoding="utf-8")
        except OSError:
            continue
        imports = _extract_imports(source)
        for imp in imports:
            for forbidden in _FORBIDDEN_MODULES:
                if imp == forbidden or imp.startswith(forbidden + "."):
                    rel = py_file.relative_to(_PROJECT_ROOT)
                    violations.append(f"{rel}: forbidden import '{imp}'")
    return violations


# ---------------------------------------------------------------------------
# Parametrised test
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "package_dir",
    _RESTRICTED_PACKAGES,
    ids=[p.relative_to(_PROJECT_ROOT).as_posix() for p in _RESTRICTED_PACKAGES],
)
def test_no_forbidden_imports(package_dir: Path) -> None:
    """No file in *package_dir* imports a forbidden UI module."""
    violations = _check_package(package_dir)
    assert (
        not violations
    ), f"Architecture violations in {package_dir.relative_to(_PROJECT_ROOT)}:\n" + "\n".join(
        f"  {v}" for v in violations
    )


def test_core_does_not_import_app_or_infrastructure() -> None:
    """iva/core/ must not import iva.app, iva.infrastructure, or iva.ui."""
    core_dir = _PROJECT_ROOT / "iva" / "core"
    forbidden_from_core = {"iva.app", "iva.infrastructure", "iva.ui", "PySide6"}
    violations: list[str] = []
    for py_file in _collect_python_files(core_dir):
        try:
            source = py_file.read_text(encoding="utf-8")
        except OSError:
            continue
        imports = _extract_imports(source)
        for imp in imports:
            for forbidden in forbidden_from_core:
                if imp == forbidden or imp.startswith(forbidden + "."):
                    rel = py_file.relative_to(_PROJECT_ROOT)
                    violations.append(f"{rel}: forbidden import '{imp}'")
    assert not violations, "Architecture violations in iva/core/:\n" + "\n".join(
        f"  {v}" for v in violations
    )
