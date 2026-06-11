# Changelog

All notable changes to this project are documented in this file.

## [1.0.0] — 2026-06-11

### Added
- Complete vibration analysis workflow: data loading, signal preprocessing, spectral
  analysis, physical calculations, resonance risk assessment
- PySide6 desktop application with dark engineering theme and seven workflow pages
- Command-line interface (CLI): `python -m iva.cli.main analyze`
- PDF and HTML report generation
- Analysis session save and load (`.vibproj`)
- Experiment vs. CFD profile comparison
- Full build and release toolchain: PyInstaller spec, Inno Setup script, PowerShell
  quality scripts (`lint.ps1`, `test.ps1`, `quality.ps1`)
- Test coverage >= 80% for `iva/core` (achieved 98%)
- Performance test: 60,000-row analysis completes in under 3 seconds
- System tests for key user scenarios from documentation/07_user_scenarios.md
- Edge-case tests from documentation/12_validation_and_verification.md
- Pre-commit configuration for automated code quality checks
- `RELEASE_CHECKLIST.md` — step-by-step release process
- `assets/iva_icon.ico` — placeholder application icon
- `documentation/screenshots/` — placeholder for application screenshots

### Technical stack
- Python 3.11+, PySide6, NumPy, SciPy, pandas, matplotlib, ReportLab

---

## [0.1.0] — Project start

- Created the initial repository foundation.
- Added the baseline Python project structure.
- Added initial configuration, requirements and documentation references.
