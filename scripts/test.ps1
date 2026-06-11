#!/usr/bin/env pwsh
# IVA — Test script with coverage
# Run from repository root: .\scripts\test.ps1
$env:QT_QPA_PLATFORM = "offscreen"
$env:QT_OPENGL = "software"
$env:MPLBACKEND = "Agg"

Write-Host "=== IVA Tests (with coverage) ===" -ForegroundColor Cyan

python -m pytest --cov=iva/core --cov-report=term-missing --cov-fail-under=80 -m "not performance"
if ($LASTEXITCODE -ne 0) {
    Write-Host "=== TESTS FAILED ===" -ForegroundColor Red
    exit 1
}
Write-Host "=== TESTS PASSED ===" -ForegroundColor Green
exit 0
