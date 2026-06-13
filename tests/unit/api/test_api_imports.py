"""Test that iva.api can be imported without PySide6 or iva.ui."""

from __future__ import annotations

import sys


def test_api_main_importable() -> None:
    """iva.api.main must import without errors."""
    import iva.api.main  # noqa: F401

    assert iva.api.main.app is not None


def test_api_does_not_import_pyside6() -> None:
    """iva.api must not pull in PySide6."""
    # Snapshot sys.modules *before* importing the API so that PySide6 modules
    # already present (e.g. loaded by UI tests earlier in the suite) do not
    # produce false positives.
    before = set(sys.modules)

    import iva.api.main  # noqa: F401
    import iva.api.routes.demo  # noqa: F401
    import iva.api.routes.health  # noqa: F401
    import iva.api.serializers.analysis_serializer  # noqa: F401

    added = set(sys.modules) - before
    pyside_added = [m for m in added if "PySide6" in m]
    assert not pyside_added, f"PySide6 was imported as a side-effect of iva.api: {pyside_added}"


def test_api_does_not_import_iva_ui() -> None:
    """iva.api must not pull in iva.ui."""
    before = set(sys.modules)

    import iva.api.main  # noqa: F401

    added = set(sys.modules) - before
    ui_added = [m for m in added if m.startswith("iva.ui")]
    assert not ui_added, f"iva.ui was imported as a side-effect of iva.api: {ui_added}"
