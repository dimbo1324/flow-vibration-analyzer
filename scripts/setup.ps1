#!/usr/bin/env pwsh
#
# setup.ps1 — Подготовка окружения разработчика IVA в Windows
#
# Назначение:
#   Создать локальное .venv, установить зависимости разработки, подключить
#   пакет в editable-режиме и проверить запуск smoke-тестом.
#
# Использование:
#   .\scripts\setup.ps1
#   .\scripts\setup.ps1 -NoEditable        # пропустить pip install -e .
#   .\scripts\setup.ps1 -SkipSmokeTest     # пропустить smoke-тест
#
# Безопасность:
#   - Изменения ограничены локальным .venv; глобальный Python не модифицируется.
#   - Корень проекта вычисляется относительно самого скрипта.
#
# Совместимость:
#   Поддерживается Windows PowerShell 5.1, рекомендуется PowerShell 7+.

[CmdletBinding()]
param(
    [switch]$NoEditable,
    [switch]$SkipSmokeTest
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot

function Write-Status {
    param([string]$Tag, [string]$Message, [string]$Color)
    $label = switch ($Tag) {
        "OK"     { "[OK]" }
        "FAILED" { "[FAILED]" }
        "INFO"   { "[INFO]" }
        "WARN"   { "[WARN]" }
        default  { "[$Tag]" }
    }
    Write-Host "$label " -ForegroundColor $Color -NoNewline
    Write-Host $Message
}

Write-Host "=== IVA Setup ===" -ForegroundColor Cyan
Write-Status "INFO" "Repository root: $repoRoot" "Cyan"

# --- 1. Проверка версии Python ----------------------------------------------
try {
    $pythonVersionRaw = & python --version 2>&1
} catch {
    Write-Status "FAILED" "Python was not found on PATH. Install Python 3.11 or later." "Red"
    exit 1
}

if ($pythonVersionRaw -match "Python (\d+)\.(\d+)\.(\d+)") {
    $major = [int]$Matches[1]
    $minor = [int]$Matches[2]
    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 11)) {
        Write-Status "FAILED" "Python >= 3.11 required, found $pythonVersionRaw." "Red"
        exit 1
    }
    Write-Status "OK" "Python version: $pythonVersionRaw" "Green"
} else {
    Write-Status "FAILED" "Could not parse Python version from '$pythonVersionRaw'." "Red"
    exit 1
}

# --- 2. Create virtual environment ------------------------------------------
$venvPath = Join-Path $repoRoot ".venv"
if (-not (Test-Path $venvPath)) {
    Write-Status "INFO" "Creating virtual environment in .venv ..." "Cyan"
    & python -m venv $venvPath
    if ($LASTEXITCODE -ne 0) {
        Write-Status "FAILED" "Failed to create virtual environment." "Red"
        exit 1
    }
    Write-Status "OK" "Virtual environment created." "Green"
} else {
    Write-Status "INFO" "Virtual environment already exists; reusing it." "Cyan"
}

# --- 3. Activate virtual environment ----------------------------------------
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
$venvPython = Join-Path $venvPath "Scripts\python.exe"
if (-not (Test-Path $activateScript)) {
    Write-Status "FAILED" "Activation script not found at $activateScript." "Red"
    exit 1
}
if (-not (Test-Path $venvPython)) {
    Write-Status "FAILED" "Virtual environment Python not found. Remove .venv and run setup again." "Red"
    exit 1
}
& $activateScript
Write-Status "OK" "Virtual environment activated." "Green"

# --- 4. Upgrade pip ----------------------------------------------------------
Write-Status "INFO" "Upgrading pip ..." "Cyan"
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    Write-Status "FAILED" "Failed to upgrade pip." "Red"
    exit 1
}
Write-Status "OK" "pip upgraded." "Green"

# --- 5. Install development dependencies -------------------------------------
$devReqs = Join-Path $repoRoot "requirements-dev.txt"
Write-Status "INFO" "Installing development dependencies ..." "Cyan"
& $venvPython -m pip install -r $devReqs
if ($LASTEXITCODE -ne 0) {
    Write-Status "FAILED" "Failed to install development dependencies." "Red"
    exit 1
}
Write-Status "OK" "Development dependencies installed." "Green"

# --- 6. Editable install -----------------------------------------------------
if (-not $NoEditable) {
    Write-Status "INFO" "Installing IVA in editable mode (pip install -e .) ..." "Cyan"
    & $venvPython -m pip install -e $repoRoot
    if ($LASTEXITCODE -ne 0) {
        Write-Status "WARN" "Editable install failed; continuing (imports will be verified)." "Yellow"
    } else {
        Write-Status "OK" "Editable install complete." "Green"
    }
} else {
    Write-Status "INFO" "Skipping editable install (-NoEditable)." "Cyan"
}

# Verify imports regardless of whether editable installation was requested.
& $venvPython -c "import iva; from iva.__version__ import __version__; print('iva', __version__)"
if ($LASTEXITCODE -ne 0) {
    Write-Status "FAILED" "The 'iva' package cannot be imported." "Red"
    exit 1
}
Write-Status "OK" "Package import verified." "Green"

# --- 7. Smoke test -----------------------------------------------------------
if (-not $SkipSmokeTest) {
    Write-Status "INFO" "Running smoke test (python main.py --smoke-test) ..." "Cyan"
    # Environment variables are process-wide in PowerShell: save and restore
    # them so an interactive session is not left in offscreen mode (which
    # would make a later .\scripts\run.ps1 GUI launch invisible).
    $savedQpa = $env:QT_QPA_PLATFORM
    $savedOpenGl = $env:QT_OPENGL
    $savedMpl = $env:MPLBACKEND
    try {
        $env:QT_QPA_PLATFORM = "offscreen"
        $env:QT_OPENGL = "software"
        $env:MPLBACKEND = "Agg"
        & $venvPython (Join-Path $repoRoot "main.py") --smoke-test
        $smokeExit = $LASTEXITCODE
    } finally {
        $env:QT_QPA_PLATFORM = $savedQpa
        $env:QT_OPENGL = $savedOpenGl
        $env:MPLBACKEND = $savedMpl
    }
    if ($smokeExit -ne 0) {
        Write-Status "FAILED" "Smoke test failed." "Red"
        exit 1
    }
    Write-Status "OK" "Smoke test passed." "Green"
} else {
    Write-Status "INFO" "Skipping smoke test (-SkipSmokeTest)." "Cyan"
}

# --- Final instructions ------------------------------------------------------
Write-Host ""
Write-Host "=== Setup complete ===" -ForegroundColor Green
Write-Host "Next steps:"
Write-Host "  Run the GUI:    .\scripts\run.ps1"
Write-Host "  Run checks:     .\scripts\quality.ps1"
exit 0
