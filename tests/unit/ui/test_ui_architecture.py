"""AST-based architecture boundary tests for iva/ui/."""

from __future__ import annotations

import ast
from pathlib import Path

# Modules that must NOT appear in iva/app/, iva/cli/, or iva/core/
FORBIDDEN_IN_APP_CLI_CORE = ["PySide6", "iva.ui"]

# Core calculation modules that the ui/ layer must not import directly
# (it must go through iva.app instead)
FORBIDDEN_CORE_CALCS_IN_UI = [
    "iva.core.signal.preprocessor",
    "iva.core.spectrum.psd_calculator",
    "iva.core.spectrum.peak_finder",
    "iva.core.spectrum.rms_calculator",
    "iva.core.physics.reynolds_calculator",
    "iva.core.physics.strouhal_calculator",
    "iva.core.physics.vortex_frequency",
    "iva.core.physics.lock_in_risk",
]


def _get_imports(filepath: Path) -> list[str]:
    try:
        tree = ast.parse(filepath.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


def _py_files(directory: str) -> list[Path]:
    p = Path(directory)
    if not p.exists():
        return []
    return list(p.rglob("*.py"))


def test_app_does_not_import_pyside6_or_ui() -> None:
    for f in _py_files("iva/app"):
        imports = _get_imports(f)
        for imp in imports:
            for forbidden in FORBIDDEN_IN_APP_CLI_CORE:
                assert not imp.startswith(
                    forbidden
                ), f"{f}: forbidden import '{imp}' (must not import {forbidden})"


def test_cli_does_not_import_ui() -> None:
    for f in _py_files("iva/cli"):
        imports = _get_imports(f)
        for imp in imports:
            assert not imp.startswith(
                "iva.ui"
            ), f"{f}: forbidden import '{imp}' (cli must not import iva.ui)"


def test_core_does_not_import_ui_or_app() -> None:
    for f in _py_files("iva/core"):
        imports = _get_imports(f)
        for imp in imports:
            assert not imp.startswith(
                "iva.ui"
            ), f"{f}: forbidden import '{imp}' (core must not import iva.ui)"
            assert not imp.startswith(
                "iva.app"
            ), f"{f}: forbidden import '{imp}' (core must not import iva.app)"


def test_ui_does_not_call_core_calculations_directly() -> None:
    for f in _py_files("iva/ui"):
        imports = _get_imports(f)
        for imp in imports:
            for forbidden in FORBIDDEN_CORE_CALCS_IN_UI:
                assert not imp.startswith(forbidden), (
                    f"{f}: forbidden direct core import '{imp}' "
                    f"(ui must go through iva.app, not {forbidden})"
                )
