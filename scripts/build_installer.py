#!/usr/bin/env python
"""IVA release build script.

Usage:
    python scripts/build_installer.py
    python scripts/build_installer.py --skip-tests
    python scripts/build_installer.py --check-only

Reads version from iva/__version__.py, optionally runs tests, builds a
PyInstaller executable, and (on Windows with Inno Setup) builds the installer.
"""

from __future__ import annotations

import argparse
import importlib.util
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read_version() -> str:
    """Read version from iva/__version__.py."""
    spec = importlib.util.spec_from_file_location("__version__", ROOT / "iva" / "__version__.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return str(module.__version__)  # type: ignore[union-attr]


def run_command(command: list[str], description: str) -> None:
    """Run a subprocess command, raising SystemExit on failure."""
    print(f"\n[BUILD] {description}")
    print(f"  Command: {' '.join(command)}")
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode != 0:
        print(f"  FAILED (exit code {result.returncode})")
        sys.exit(result.returncode)
    print("  OK")


def find_iscc() -> Path | None:
    """Find Inno Setup ISCC compiler on Windows."""
    if platform.system() != "Windows":
        return None
    candidates = [
        Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"),
        Path(r"C:\Program Files\Inno Setup 6\ISCC.exe"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    found = shutil.which("ISCC")
    if found:
        return Path(found)
    return None


def copy_installer(version: str) -> Path:
    """Report on the built installer in dist/release/."""
    src = ROOT / "dist" / "release" / f"IVA_Setup_{version}.exe"
    if not src.exists():
        print(f"  WARNING: Expected installer not found at {src}")
        return src
    print(f"  Installer: {src}")
    print(f"  Size: {src.stat().st_size / 1024 / 1024:.1f} MB")
    return src


def check_environment(version: str) -> None:
    """Print environment information and tool availability."""
    print(f"\n[CHECK] IVA v{version} build environment")
    print(f"  Platform: {platform.system()} {platform.architecture()[0]}")
    print(f"  Python: {sys.version}")

    pyinstaller_path = shutil.which("pyinstaller")
    if pyinstaller_path:
        print(f"  PyInstaller: {pyinstaller_path} — available")
    else:
        print("  PyInstaller: NOT FOUND (install with: pip install -r requirements-build.txt)")

    iscc = find_iscc()
    if iscc:
        print(f"  Inno Setup ISCC: {iscc} — available")
    else:
        print("  Inno Setup ISCC: NOT FOUND (download from https://jrsoftware.org/isinfo.php)")


def main() -> int:
    parser = argparse.ArgumentParser(description="IVA release build script")
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip running tests before building (for debugging the build process only)",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Check environment availability only — do not build",
    )
    args = parser.parse_args()

    version = read_version()
    print(f"\n=== IVA Release Build v{version} ===")

    check_environment(version)

    if args.check_only:
        print("\n[CHECK] Environment check complete.")
        return 0

    # Step 1: Run tests
    if not args.skip_tests:
        run_command(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/unit/",
                "tests/integration/",
                "-q",
                "--tb=short",
                "-m",
                "not performance",
            ],
            "Running unit and integration tests",
        )
    else:
        print("\n[BUILD] WARNING: Tests skipped (--skip-tests).")

    # Step 2: PyInstaller
    if not shutil.which("pyinstaller"):
        print("\n[BUILD] WARNING: pyinstaller not found. Install with: pip install pyinstaller")
        print("  Skipping executable build.")
    else:
        run_command(
            [
                "pyinstaller",
                "scripts/iva.spec",
                "--distpath",
                "dist",
                "--workpath",
                "build",
            ],
            "Building PyInstaller executable",
        )

    # Step 3: Inno Setup (Windows only)
    iscc = find_iscc()
    if iscc is None:
        print("\n[BUILD] NOTE: Inno Setup (ISCC) not found.")
        if platform.system() != "Windows":
            print("  Installer build requires Windows + Inno Setup 6.")
        else:
            print("  Install Inno Setup 6 from https://jrsoftware.org/isinfo.php")
        print("  Skipping installer build.")
    else:
        (ROOT / "dist" / "release").mkdir(parents=True, exist_ok=True)
        run_command(
            [str(iscc), f"/DMyAppVersion={version}", "scripts/installer.iss"],
            "Building Inno Setup installer",
        )
        copy_installer(version)

    print(f"\n=== Build complete: IVA v{version} ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
