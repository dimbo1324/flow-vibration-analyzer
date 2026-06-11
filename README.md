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

### Supported runtime

The test suite and type checks are exercised in CI on Python 3.11, 3.12 and
3.13. The scientific stack is supported across NumPy 1.26–2.x and pandas 2.x
(the code is verified to run under NumPy 2 and pandas 2/3). Newer major
versions of NumPy/pandas are covered by the Python 3.13 CI lane.

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

## Development Diagnostics and Logs

The `out/` directory is generated at runtime and is excluded from version
control (`.gitignore`).  It is created automatically the first time any
script or the application writes to it.

| Path | Contents |
|---|---|
| `out/logs/` | Daily rotating `iva_YYYY-MM-DD.log` files (30-day retention) |
| `out/workflow-runs/` | Timestamped directories from `check_project.py` runs (per-step logs + summary) |
| `out/test-results/` | Reserved for future pytest XML/HTML reports |
| `out/diagnostics/` | Snapshots from `diagnose_project.py` |
| `out/cli-runs/` | Reserved for future CLI run artefacts |

Override the base path with the `IVA_OUT_DIR` environment variable (useful
in CI or when you want to redirect output to another location).

### Full project check

```bash
python scripts/check_project.py
```

Runs smoke test, CLI help, compile check, pytest, black, ruff, and mypy in
sequence.  Creates a timestamped run directory under `out/workflow-runs/`
with individual log files and a `summary.txt`.

### Collect diagnostics

```bash
python scripts/diagnose_project.py
```

Prints Python version, platform, package versions, git branch and status,
and the latest log file path.  Writes the same information to
`out/diagnostics/YYYYMMDD_HHMMSS_diagnostics.txt`.

Automated agents and future CI jobs can inspect `out/workflow-runs/`,
`out/test-results/`, `out/diagnostics/`, and `out/logs/` without
additional tooling.

## Documentation

The full documentation package is located in [`documentation/`](documentation/).

Start with [`documentation/00_project_overview.md`](documentation/00_project_overview.md) for an
introduction to the project, its engineering context and design goals.

## CLI Usage

Stage 7 adds a full command-line interface.  Run a complete analysis with:

```bash
python -m iva.cli.main analyze \
    --data data/examples/example_clean_sine.csv \
    --config config/example_config.json \
    --output reports/run_001
```

The command produces the following files in the output directory:

| File | Description |
|---|---|
| `analysis_summary.json` | Machine-readable JSON summary (scalars only, no large arrays) |
| `spectrum.csv` | Frequency / PSD / peak-marker table |
| `signal.csv` | Time / cleaned signal / filtered signal table |
| `physics_summary.csv` | Physics parameters and risk level (key–value format) |
| `analysis_summary.html` | Static HTML summary page (no JS, no external assets) |

Get CLI help:

```bash
python -m iva.cli.main --help
python -m iva.cli.main analyze --help
```

## Desktop GUI

Launch the full desktop application:

```bash
python main.py
```

The CLI remains fully available and independent of the GUI:

```bash
python -m iva.cli.main analyze --help
```

## Development Status

**Stage 8 complete — PySide6 Desktop Interface.**

- Stage 1: repository foundation, configuration, documentation baseline.
- Stage 2: full domain model layer in `iva/core/models/` — frozen dataclasses, enumerations,
  exception hierarchy, minimal infrastructure logger, 84 passing unit tests.
- Stage 2.5: code quality infrastructure — `.editorconfig`, pre-commit hooks, cross-platform
  scripts, GitHub Actions CI.
- Stage 3: file readers (CSV, Parquet, Excel), data quality validator, enhanced logger with
  daily rotation and 30-day retention, synthetic signal generator.
- Stage 4: signal preprocessing pipeline in `iva/core/signal/` — mean removal, MAD-based outlier
  detection and replacement, gap filling, Butterworth bandpass/lowpass/highpass filters
  (`filtfilt` zero-phase), `preprocess_signal()` pipeline orchestrator. 36 unit tests.
- Stage 5: spectral analysis in `iva/core/spectrum/` — Welch PSD (`scaling='density'`), peak
  detection in dB domain with -3 dB width, peak interpretation (VORTEX_SHEDDING / HARMONIC /
  STRUCTURAL / UNKNOWN), total/band/sliding-window RMS. 29 unit tests.
- Stage 6: physics and risk — Reynolds number, Strouhal number (Blevins table + tandem),
  vortex shedding frequency, velocity/frequency ratios, three-level lock-in risk assessment
  with Russian engineering recommendations.
- Stage 7: application coordination layer (`iva/app/`) and CLI (`iva/cli/`) — synchronous
  `run_pipeline()` orchestrator, `AnalysisSession` state container, `AnalysisRunner`,
  `settings_manager` (TOML + JSON config), CSV/JSON/HTML result exporters, integration tests,
  architecture boundary tests, `config/example_config.json`.

**Supported input formats:** `.csv`, `.parquet`, `.xlsx`

To regenerate the demo data files:

```bash
python scripts/generate_synthetic_data.py
```
