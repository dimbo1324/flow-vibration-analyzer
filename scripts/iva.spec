# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Industrial Vibration Analyzer (IVA)
# Build with: pyinstaller scripts/iva.spec
# Run from repository root directory.

import sys
from pathlib import Path

ROOT = Path(".").resolve()

# Icon (optional — include only if file exists)
icon_path = ROOT / "assets" / "iva_icon.ico"
icon = str(icon_path) if icon_path.exists() else None

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / "config" / "defaults.toml"), "config"),
        (str(ROOT / "config" / "example_config.json"), "config"),
        (str(ROOT / "config" / "strouhal_tables.toml"), "config"),
        (str(ROOT / "data" / "examples"), "data/examples"),
    ],
    hiddenimports=[
        # SciPy
        "scipy.integrate",
        "scipy.interpolate",
        "scipy.signal",
        "scipy.stats",
        # pandas
        "pandas",
        "pandas.io.formats.style",
        # pyarrow
        "pyarrow",
        # openpyxl
        "openpyxl",
        # matplotlib
        "matplotlib",
        "matplotlib.backends.backend_qtagg",
        "matplotlib.backends.backend_agg",
        # PySide6 modules
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        "PySide6.QtPrintSupport",
        # reportlab (for PDF)
        "reportlab",
        "reportlab.platypus",
        "reportlab.lib",
        "reportlab.lib.pagesizes",
        "reportlab.lib.styles",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="IVA",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="IVA",
)
