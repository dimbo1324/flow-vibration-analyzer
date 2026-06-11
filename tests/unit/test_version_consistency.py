"""Version consistency tests — iva/__version__.py is the single source of truth."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

from iva.__version__ import __version__

ROOT = Path(__file__).resolve().parents[2]


def test_iva_version_is_1_0_0():
    assert __version__ == "1.0.0"


def test_pyproject_version_matches():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project_version = data.get("project", {}).get("version")
    # Skip if dynamic versioning is used
    if project_version is not None:
        assert project_version == __version__


def test_defaults_toml_has_no_stale_app_version():
    text = (ROOT / "config" / "defaults.toml").read_text(encoding="utf-8")
    assert "0.1.0" not in text, "config/defaults.toml must not contain stale 0.1.0 version"


def test_build_installer_reads_version_from_version_file():
    # build_installer.py should read version from iva/__version__.py, not hardcode a different one
    text = (ROOT / "scripts" / "build_installer.py").read_text(encoding="utf-8")
    assert "__version__" in text
    assert "/DMyAppVersion={version}" in text


def test_installer_version_is_not_hardcoded():
    text = (ROOT / "scripts" / "installer.iss").read_text(encoding="utf-8")
    assert not re.search(r'^#define MyAppVersion\s+"', text, flags=re.MULTILINE)
    assert "#ifndef MyAppVersion" in text
