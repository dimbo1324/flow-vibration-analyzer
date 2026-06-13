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

IVA v1.0.0 includes the complete analysis pipeline, desktop visualisation, PDF/HTML reporting,
versioned project sessions, experiment-versus-CFD profile comparison, and a full Windows installer
build toolchain. The desktop UI, CLI help and product-facing errors, recommendations, and PDF/HTML
reports are presented in Russian; technical notation and machine-readable export keys remain stable.

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
├─ docs/                 # Project documentation (23 files) + DEVELOPMENT_CHECKLIST.md
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

The full documentation package is located in [`docs/`](docs/).

Start with [`docs/00_project_overview.md`](docs/00_project_overview.md) for an
introduction to the project, its engineering context and design goals.

## Demo Mode and Quick Start

Демо-режим позволяет пройти полный расчетный цикл без подготовки CSV-файла.

В GUI:

1. Запустите приложение командой `python main.py`.
2. На странице «Сводка» нажмите `Запустить демо-анализ` или выберите сценарий на странице «Импорт».
3. Изучите графики, физические параметры, оценку риска и экспортируйте отчет.

Запуск демо-сценария из CLI:

```bash
python -m iva.cli.main demo --scenario clean_40hz --output out/cli-runs/demo_clean --export-pdf --export-html --save-project
```

Список доступных сценариев:

```bash
python -m iva.cli.main demo --list-scenarios
```

Демо-данные являются синтетическими и не должны использоваться как реальные измерения.

## CLI Usage

Stage 7 adds a full command-line interface.  Run a complete analysis with:

```bash
python -m iva.cli.main analyze \
    --data data/examples/example_clean_sine.csv \
    --config config/example_config.json \
    --output reports/run_001 \
    --export-pdf \
    --export-html \
    --save-project
```

The command produces the following files in the output directory:

| File | Description |
|---|---|
| `analysis_summary.json` | Machine-readable JSON summary (scalars only, no large arrays) |
| `spectrum.csv` | Frequency / PSD / peak-marker table |
| `signal.csv` | Time / cleaned signal / filtered signal table |
| `physics_summary.csv` | Physics parameters and risk level (key–value format) |
| `analysis_summary.html` | Static HTML summary page (no JS, no external assets) |
| `report.pdf` | Full light-theme engineering report (`--export-pdf`) |
| `report.html` | Full standalone report (`--export-html`) |
| `project.vibproj` | Versioned JSON project session (`--save-project`) |

Get CLI help:

```bash
python -m iva.cli.main --help
python -m iva.cli.main analyze --help
```

GUI features include PDF/HTML/CSV/JSON export on the Report page,
`.vibproj` save/open actions, zoom/pan/reset and PNG chart controls, and a
Profiles page that compares `coordinate,value` experiment and CFD CSV files.

## Desktop GUI

Launch the full desktop application:

```bash
python main.py
```

### Desktop UX

Рабочее окно использует изменяемые по размеру панели: компактную или развёрнутую
навигацию (`L`), центральную рабочую область и инспектор результатов (`R`). График
можно открыть в режиме детального просмотра двойным щелчком или клавишей `F`;
`Esc` возвращает исходную компоновку. Во время анализа отображаются реальный
индикатор прогресса и согласованные состояния страниц: ожидание, выполнение,
ошибка и готовый результат.

The CLI remains fully available and independent of the GUI:

```bash
python -m iva.cli.main analyze --help
```

## Web Interface

An optional FastAPI + React web interface provides full browser-based analysis:
demo scenarios, CSV/Excel/Parquet file upload, spectral analysis, PDF/HTML/CSV
report download, and `.vibproj` session save/load.

It does not require the desktop GUI or Docker for local development.

### Dependencies

Install Python web dependencies (FastAPI, uvicorn, httpx):

```powershell
# PowerShell
.\scripts\iva.ps1 setup-web
```

```bash
# Cross-platform
python scripts/iva.py setup-web
# or directly:
python -m pip install -r requirements-web.txt
```

### Manual launch (recommended for development)

**Backend (FastAPI):**

```powershell
# PowerShell
.\scripts\iva.ps1 web-backend
```

```bash
# Cross-platform
python scripts/iva.py web-backend
# or directly:
python -m uvicorn iva.api.main:app --reload --host 127.0.0.1 --port 8000
```

API docs: **http://127.0.0.1:8000/docs**

**Frontend (React/Vite):**

```powershell
# PowerShell
.\scripts\iva.ps1 web-frontend
```

```bash
# Cross-platform
python scripts/iva.py web-frontend
# or directly:
cd web/frontend && pnpm install && pnpm dev
```

Open **http://localhost:5173** in a browser.

### Docker launch

```powershell
# Requires Docker Desktop running
docker compose up --build web-backend web-frontend
```

```powershell
# Via iva.ps1 dispatcher
.\scripts\iva.ps1 web
```

| Service | Port | Description |
|---------|------|-------------|
| `web-backend` | 8000 | FastAPI — REST API, `/api/docs` for Swagger UI |
| `web-frontend` | 5173 | React/Vite SPA (Nginx in production build) |

Docker commands:

```powershell
.\scripts\docker.ps1 web-build   # build images
.\scripts\docker.ps1 web-up      # start in background
.\scripts\docker.ps1 web-down    # stop services
.\scripts\docker.ps1 web-logs    # tail logs
.\scripts\docker.ps1 web-test    # run API tests in Docker
```

### File upload workflow

1. Open **http://localhost:5173** → click **«Загрузка файла»**.
2. Drag-and-drop or select a CSV / Excel / Parquet file (max 100 MB).
3. Configure columns (`time_s`, signal column, sampling rate) and optional flow parameters.
4. Click **«Запустить анализ»** → view spectrum chart, metrics, risk badge, warnings.
5. Download results via **«Экспорт результатов»**:
   - HTML report, PDF report
   - Spectrum CSV, Signal CSV, Physics summary CSV
6. Save session as **`.vibproj`** and reload it later via **«Сессии»**.

### Architecture notes

- `iva/api/` is a standalone FastAPI package; it never imports `iva.ui` or PySide6.
- All scientific calculations run server-side inside the existing `iva` Python package.
- Arrays sent to the browser are down-sampled server-side to 2000 points maximum.
- CORS origins are configured via `IVA_API_CORS_ORIGINS` environment variable.
- All web-generated files land under `out/web/` (gitignored).
- Uploaded files are stored with UUID names — original filenames are never used as server paths.

### Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'fastapi'` | Run `python -m pip install -r requirements-web.txt` |
| `ModuleNotFoundError: No module named 'pnpm'` | Run `corepack enable` then `corepack prepare pnpm@latest --activate` |
| Port 8000 busy | Stop the other process or run uvicorn on another port |
| Port 5173 busy | Edit `web/frontend/vite.config.ts` → `server.port` |
| Docker unavailable | Use manual launch (no Docker required for local development) |

## Windows helper scripts

The recommended Windows 11 entrypoint is `scripts/iva.ps1`. It works with
Windows PowerShell 5.1 and PowerShell 7+, detects the repository root without
user-specific paths, and keeps the common developer commands in one place.

```powershell
# One-time environment bootstrap
.\scripts\iva.ps1 setup

# Headless startup check, then an interactive GUI launch
.\scripts\iva.ps1 smoke
.\scripts\iva.ps1 run

# Quality and full project checks
.\scripts\iva.ps1 quality
.\scripts\iva.ps1 check
.\scripts\iva.ps1 diagnose

# Always preview cleanup before explicitly allowing deletion
.\scripts\iva.ps1 clean -DryRun
.\scripts\iva.ps1 clean -DryRun -KeepLogs
.\scripts\iva.ps1 clean -Force
.\scripts\iva.ps1 clean -DryRun -IncludeVenv
.\scripts\iva.ps1 clean -Force -IncludeVenv

# CLI demo and non-building release environment check
.\scripts\iva.ps1 demo
.\scripts\iva.ps1 build-check

# Safe developer chain: smoke, quality, check, demo, build-check
.\scripts\iva.ps1 all
```

`all` does not perform destructive cleanup or a full installer build. The full
build runs only via `.\scripts\iva.ps1 build` and requires Windows,
PyInstaller, and Inno Setup 6. Existing individual scripts remain available
for focused work and backward compatibility:

```powershell
.\scripts\run.ps1 -SmokeTest
.\scripts\clean.ps1 -DryRun
.\scripts\clean-logs.ps1 -DryRun
.\scripts\lint.ps1     # black, ruff, mypy
.\scripts\test.ps1     # pytest with coverage (excludes performance tests)
.\scripts\quality.ps1  # lint + tests
.\scripts\build-all.ps1 -CheckOnly
```

### Cross-platform cleanup

`scripts/clean_project.py` is the Python counterpart of `clean.ps1` for
non-Windows shells and CI. It removes only a conservative, hardcoded list of
generated artifacts (caches, `build/`, `dist/`, `out/`, coverage files,
`__pycache__`); source code, docs, tests, config and demo data are never
touched. Virtual environments `.venv/`, `venv/` and `env/` are preserved by
default and enter the plan only with the explicit `--include-venv` flag.
Always preview first; actual deletion additionally requires `--force`:

```bash
python scripts/clean_project.py --dry-run
python scripts/clean_project.py --dry-run --keep-logs   # preserve out/ logs
python scripts/clean_project.py --force                 # delete without prompt
python scripts/clean_project.py --dry-run --include-venv
python scripts/clean_project.py --force --include-venv  # recreate with setup afterwards
```

The same opt-in is available on Windows as `-IncludeVenv`. After removing a
virtual environment, run `.\scripts\iva.ps1 setup` before other developer
commands. Cleanup refuses repository roots it cannot validate, paths outside
the repository, symlinks, source trees, documentation, tests, scripts,
configuration and example or synthetic data.

#### Блокировка `.venv` на Windows

Если очистка запущена интерпретатором из `.venv` (например, через
`.\scripts\iva.ps1 clean -Force -IncludeVenv`), Windows удерживает
`python.exe` и не позволяет удалить директорию. Скрипт определяет этот
случай автоматически: использует базовый системный Python для запуска
`clean_project.py` вместо `.venv`-интерпретатора, что позволяет удалить
`.venv` без ошибок. Если системного Python нет — скрипт сообщит об этом
и выведет команду для ручного удаления:

```powershell
Remove-Item -Recurse -Force .venv
```

После удаления окружения переустановите его командой:

```powershell
.\scripts\iva.ps1 setup
```

## Docker-автоматизация (опционально)

Docker — **опциональный** инструмент для разработчика. Он не нужен для
повседневной работы на Windows и не поддерживает запуск GUI PySide6. Его
назначение: воспроизводимые проверки в Linux-среде, близкой к GitHub Actions CI.

### Когда Docker полезен

- Линтер, mypy, тесты в чистом Linux-окружении.
- Проверка CLI-демо без локального `.venv`.
- Воспроизведение ошибок CI, которые не проявляются на Windows.

### Команды

```powershell
# Собрать образ (однократно или после изменения зависимостей)
.\scripts\docker.ps1 build

# Линтер + mypy + тесты (аналог CI)
.\scripts\docker.ps1 quality

# Тесты с отчётом о покрытии
.\scripts\docker.ps1 test

# CLI-демо, результаты сохраняются в ./out/cli-runs/demo_docker/
.\scripts\docker.ps1 cli-demo

# Интерактивная оболочка внутри контейнера
.\scripts\docker.ps1 shell

# Удалить образ и тома Docker
.\scripts\docker.ps1 clean
```

Если Docker не установлен, скрипт выведет понятное сообщение и ссылку на
установку. Отсутствие Docker не влияет на локальные и CI-проверки.

## Building the Windows Installer

Requires PyInstaller and (for the installer) Inno Setup 6 on Windows:

```bash
# Install build dependencies (PyInstaller)
python -m pip install -r requirements-build.txt

# Check build environment
python scripts/build_installer.py --check-only

# Full build: run tests, build PyInstaller exe, build Inno Setup installer
python scripts/build_installer.py

# Skip tests (for debugging the build process only)
python scripts/build_installer.py --skip-tests
```

The installer is produced at `dist/release/IVA_Setup_1.0.0.exe`.

Notes for the installed application:

- bundled resources (`config/`, demo examples) are read from the install
  directory automatically;
- generated output (logs, demo data, reports) is written to the writable
  per-user folder `Documents\IVA\` — never into `Program Files`.

## Development Status

**v1.0.0 — first public release.**

- Stage 1: repository foundation, configuration, documentation baseline.
- Stage 2: full domain model layer in `iva/core/models/` — frozen dataclasses, enumerations,
  exception hierarchy, minimal infrastructure logger.
- Stage 2.5: code quality infrastructure — `.editorconfig`, pre-commit hooks, cross-platform
  scripts, GitHub Actions CI.
- Stage 3: file readers (CSV, Parquet, Excel), data quality validator, enhanced logger with
  daily rotation and 30-day retention, synthetic signal generator.
- Stage 4: signal preprocessing pipeline in `iva/core/signal/` — mean removal, MAD-based outlier
  detection and replacement, gap filling, Butterworth bandpass/lowpass/highpass filters
  (`filtfilt` zero-phase), `preprocess_signal()` pipeline orchestrator.
- Stage 5: spectral analysis in `iva/core/spectrum/` — Welch PSD (`scaling='density'`), peak
  detection in dB domain with -3 dB width, peak interpretation (VORTEX_SHEDDING / HARMONIC /
  STRUCTURAL / UNKNOWN), total/band/sliding-window RMS.
- Stage 6: physics and risk — Reynolds number, Strouhal number (Blevins table + tandem),
  vortex shedding frequency, velocity/frequency ratios, three-level lock-in risk assessment
  with Russian engineering recommendations.
- Stage 7: application coordination layer (`iva/app/`) and CLI (`iva/cli/`) — synchronous
  `run_pipeline()` orchestrator, `AnalysisSession` state container, `AnalysisRunner`,
  `settings_manager` (TOML + JSON config), CSV/JSON/HTML result exporters, integration tests,
  architecture boundary tests, `config/example_config.json`.
- Stage 8: PySide6 desktop GUI — seven workflow pages with dark engineering theme, QThread
  background analysis, zoom/pan charts, error banner, drag-and-drop import.
- Stage 9: reports and sessions — PDF/HTML report generation, `.vibproj` session persistence,
  experiment vs. CFD profile comparison.
- Stage 10: quality, performance, build — 98% core test coverage, 60k-row performance test,
  edge-case and system scenario tests, PyInstaller spec, Inno Setup script, PowerShell
  quality scripts, version 1.0.0.

**Supported input formats:** `.csv`, `.parquet`, `.xlsx`

To regenerate the demo data files:

```bash
python scripts/generate_synthetic_data.py
```
