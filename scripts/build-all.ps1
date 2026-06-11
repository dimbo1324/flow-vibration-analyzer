#!/usr/bin/env pwsh
#
# build-all.ps1 — Full IVA release build orchestration (Windows)
#
# Purpose:
#   Run the complete release pipeline: clean generated artifacts, run quality
#   checks (lint + tests), then build the executable and installer via
#   scripts\build_installer.py.
#
# Usage:
#   .\scripts\build-all.ps1                # clean, quality, full build
#   .\scripts\build-all.ps1 -SkipClean     # do not clean artifacts first
#   .\scripts\build-all.ps1 -SkipTests     # skip the test phase (lint still runs)
#   .\scripts\build-all.ps1 -CheckOnly      # verify environment only, no build
#
# Safety notes:
#   - Stops immediately on the first failure; exit codes are preserved.
#   - -SkipClean is passed through; clean.ps1 only removes generated artifacts.
#   - No hardcoded user paths; repository root is detected from this script.
#
# Compatibility:
#   Windows PowerShell 5.1 compatible. PowerShell 7+ is recommended.

[CmdletBinding()]
param(
    [switch]$SkipClean,
    [switch]$SkipTests,
    [switch]$CheckOnly
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

function Stop-OnFailure {
    param([string]$Step)
    if ($LASTEXITCODE -ne 0) {
        Write-Status "FAILED" "$Step (exit code $LASTEXITCODE)." "Red"
        exit $LASTEXITCODE
    }
}

Write-Host "=== IVA Build All ===" -ForegroundColor Cyan
Write-Status "INFO" "Repository root: $repoRoot" "Cyan"

# --- 1. Clean ----------------------------------------------------------------
if ($SkipClean) {
    Write-Status "INFO" "Skipping clean step." "Cyan"
} else {
    Write-Status "INFO" "Cleaning generated artifacts ..." "Cyan"
    & "$PSScriptRoot\clean.ps1" -Force
    Stop-OnFailure "Clean step failed"
    Write-Status "OK" "Clean complete." "Green"
}

# --- 2. Quality checks (lint + tests) ---------------------------------------
if ($SkipTests) {
    Write-Status "INFO" "Running lint only (-SkipTests) ..." "Cyan"
    & "$PSScriptRoot\lint.ps1"
    Stop-OnFailure "Lint failed"
    Write-Status "OK" "Lint passed." "Green"
} else {
    Write-Status "INFO" "Running quality checks (lint + tests) ..." "Cyan"
    & "$PSScriptRoot\quality.ps1"
    Stop-OnFailure "Quality checks failed"
    Write-Status "OK" "Quality checks passed." "Green"
}

# --- 3. Build ----------------------------------------------------------------
$buildScript = Join-Path $repoRoot "scripts\build_installer.py"
if ($CheckOnly) {
    Write-Status "INFO" "Checking build environment (--check-only) ..." "Cyan"
    & python $buildScript --check-only
    Stop-OnFailure "Build environment check failed"
} elseif ($SkipTests) {
    Write-Status "INFO" "Building (--skip-tests) ..." "Cyan"
    & python $buildScript --skip-tests
    Stop-OnFailure "Build failed"
} else {
    Write-Status "INFO" "Building installer ..." "Cyan"
    & python $buildScript
    Stop-OnFailure "Build failed"
}

Write-Host ""
Write-Status "OK" "Build pipeline completed successfully." "Green"
exit 0
