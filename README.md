# Flow Vibration Analyzer

**Industrial Vibration Analyzer (IVA)**

## What is IVA?

Industrial Vibration Analyzer (IVA) is an engineering desktop application for Windows 11, designed for
the analysis of vibrations, pressure pulsations and flow-induced oscillations in heat exchanger
equipment. It targets engineers, researchers and students working with hydrodynamic and vibration data
from sensors, PIV/LDV measurement systems and CFD simulations.

IVA automates the standard analysis workflow: data import, signal preprocessing, spectral analysis,
physical coefficient calculation (Reynolds number, Strouhal number, vortex shedding frequency),
resonance risk assessment, comparison with CFD results, and structured report generation.

Future stages will add full signal processing, spectral analysis, physical calculations, visualisation
and PDF/CSV reporting. Stage 1 establishes the repository foundation only — no analysis pipeline is
implemented yet.

## Requirements

- Python 3.11 or later
- Windows 11 (64-bit) — primary target platform
- 4 GB RAM minimum (8 GB recommended)
- Git
- A virtual environment is strongly recommended

## Installation

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```bash
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

## Run Application

```bash
python main.py
```

Expected output at Stage 1:

```
Industrial Vibration Analyzer foundation is ready.
No analysis pipeline is implemented yet.
```

## Run Tests and Checks

```bash
python -m pytest
python -m black --check .
python -m ruff check .
python -m mypy iva main.py
```

## Developer Tooling

### Format code

```bash
python scripts/format_code.py
```

Runs `black` and `ruff --fix` across the whole repository.

### Full quality check

```bash
python scripts/check_project.py
```

Runs smoke test, compile check, pytest, black, ruff, and mypy in sequence.
Exits with a non-zero code on the first failure.

### Pre-commit hooks

Install once after cloning:

```bash
pip install pre-commit
pre-commit install
```

Run manually against all files:

```bash
pre-commit run --all-files
```

Hooks run automatically before every `git commit` and enforce formatting,
linting and type checking without manual intervention.

### Makefile (Unix / Git Bash)

```
make format      # format_code.py
make check       # check_project.py
make test        # pytest
make typecheck   # mypy iva main.py
make lint        # ruff check .
```

On Windows, use the Python scripts directly.

## Project Structure

```
flow-vibration-analyzer/
├─ iva/                  # Main Python application package
│  ├─ __version__.py     # Single source of version truth
│  ├─ ui/                # PySide6 desktop UI (future stages)
│  ├─ app/               # Application coordination and session state (future stages)
│  ├─ core/              # Pure calculation and domain logic (future stages)
│  └─ infrastructure/    # File I/O, logging, export adapters (future stages)
├─ tests/                # Automated tests
├─ scripts/              # Utility and build scripts
├─ documentation/        # Full project documentation (23 files, read-only)
├─ config/               # Application configuration
│  └─ defaults.toml      # Default settings placeholder
├─ data/
│  ├─ examples/          # Demonstration input files
│  └─ synthetic/         # Generated test and demo data
├─ main.py               # Application entry point
├─ pyproject.toml        # Project metadata and tool configuration
├─ requirements.txt      # Runtime dependencies
├─ requirements-dev.txt  # Development tool dependencies
├─ .gitignore
├─ CHANGELOG.md
└─ CONTRIBUTING.md
```

## Documentation

The full documentation package is located in [`documentation/`](documentation/).

Start with [`documentation/00_project_overview.md`](documentation/00_project_overview.md) for an
introduction to the project, its engineering context and design goals.

## Development Status

**Stage 3 complete — File Import and Synthetic Data.**

- Stage 1: repository foundation, configuration, documentation baseline.
- Stage 2: full domain model layer in `iva/core/models/` — frozen dataclasses, enumerations,
  exception hierarchy, minimal infrastructure logger, 84 passing unit tests.
- Stage 2.5: code quality infrastructure — `.editorconfig`, pre-commit hooks, cross-platform
  scripts, GitHub Actions CI.
- Stage 3: file readers (CSV, Parquet, Excel), data quality validator, enhanced logger with
  daily rotation and 30-day retention, synthetic signal generator.

**Supported input formats:** `.csv`, `.parquet`, `.xlsx`

To regenerate the demo data files:

```bash
python scripts/generate_synthetic_data.py
```

No analysis pipeline, UI, charts or reports are implemented yet. Those will
be added in Stages 4–10 according to the development roadmap.
