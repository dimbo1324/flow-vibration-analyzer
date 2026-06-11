# IVA Release Checklist

Use this checklist before each release.

## Pre-release

- [ ] All tests pass: `python -m pytest`
- [ ] Coverage >= 80%: `python -m pytest --cov=iva/core --cov-fail-under=80`
- [ ] Lint clean: `python -m black --check . && python -m ruff check . && python -m mypy iva main.py`
- [ ] Version updated in `iva/__version__.py`
- [ ] `CHANGELOG.md` updated with release notes
- [ ] `docs/DEVELOPMENT_CHECKLIST.md` Stage items reviewed

## Build

- [ ] Run: `python scripts/build_installer.py`
- [ ] PyInstaller executable built: `dist/IVA/IVA.exe`
- [ ] Inno Setup installer built: `dist/release/IVA_Setup_{version}.exe`

## Windows validation

- [ ] Install on clean Windows 11 machine
- [ ] Launch application: `IVA.exe`
- [ ] Open demo data: `data/examples/example_clean_sine.csv`
- [ ] Run analysis and verify results
- [ ] Check all 7 pages work correctly
- [ ] Export PDF report
- [ ] Save and load `.vibproj` session
- [ ] Run CLI: `python -m iva.cli.main analyze --help`
- [ ] Verify uninstall via Programs and Features

## Release

- [ ] Tag: `git tag v{version}`
- [ ] Push tag: `git push origin v{version}`
- [ ] Archive installer in safe location
- [ ] Update GitHub release notes

## PowerShell quality check shortcut

```powershell
.\scripts\quality.ps1
```
