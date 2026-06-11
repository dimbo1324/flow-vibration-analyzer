#!/usr/bin/env pwsh
#
# run.ps1 — Launch the IVA application (Windows)
#
# Purpose:
#   Activate the local virtual environment and start the Industrial Vibration
#   Analyzer GUI, or run the headless smoke test.
#
# Usage:
#   .\scripts\run.ps1                # launch the desktop GUI
#   .\scripts\run.ps1 -SmokeTest     # run 'python main.py --smoke-test'
#
# Safety notes:
#   - Read-only with respect to the repository; only launches the app.
#   - No hardcoded user paths; the repository root is detected from this script.
#
# Compatibility:
#   Windows PowerShell 5.1 compatible. PowerShell 7+ is recommended.

[CmdletBinding()]
param(
    [switch]$SmokeTest
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

Write-Host "=== IVA Run ===" -ForegroundColor Cyan

# --- 1. Ensure the virtual environment exists -------------------------------
$venvPath = Join-Path $repoRoot ".venv"
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
$venvPython = Join-Path $venvPath "Scripts\python.exe"
if (-not (Test-Path $activateScript) -or -not (Test-Path $venvPython)) {
    Write-Status "FAILED" "No virtual environment found. Run .\scripts\setup.ps1 first." "Red"
    exit 1
}

# --- 2. Activate the virtual environment ------------------------------------
& $activateScript
Write-Status "OK" "Virtual environment activated." "Green"

# --- 3. Launch the application ----------------------------------------------
$mainPy = Join-Path $repoRoot "main.py"
if ($SmokeTest) {
    Write-Status "INFO" "Running smoke test ..." "Cyan"
    $env:QT_QPA_PLATFORM = "offscreen"
    $env:QT_OPENGL = "software"
    $env:MPLBACKEND = "Agg"
    & $venvPython $mainPy --smoke-test
} else {
    Write-Status "INFO" "Launching the IVA desktop application ..." "Cyan"
    & $venvPython $mainPy
}

$exitCode = $LASTEXITCODE
if ($exitCode -ne 0) {
    Write-Status "FAILED" "Application exited with code $exitCode." "Red"
} else {
    Write-Status "OK" "Application exited cleanly." "Green"
}
exit $exitCode
