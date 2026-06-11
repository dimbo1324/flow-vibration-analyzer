#!/usr/bin/env pwsh
# IVA — Lint check script
# Run from repository root: .\scripts\lint.ps1
Write-Host "=== IVA Lint Checks ===" -ForegroundColor Cyan

$failed = $false

Write-Host "`n[1/3] Black format check..." -ForegroundColor Yellow
python -m black --check .
if ($LASTEXITCODE -ne 0) { $failed = $true; Write-Host "FAILED" -ForegroundColor Red }
else { Write-Host "OK" -ForegroundColor Green }

Write-Host "`n[2/3] Ruff lint check..." -ForegroundColor Yellow
python -m ruff check .
if ($LASTEXITCODE -ne 0) { $failed = $true; Write-Host "FAILED" -ForegroundColor Red }
else { Write-Host "OK" -ForegroundColor Green }

Write-Host "`n[3/3] Mypy type check..." -ForegroundColor Yellow
python -m mypy iva main.py
if ($LASTEXITCODE -ne 0) { $failed = $true; Write-Host "FAILED" -ForegroundColor Red }
else { Write-Host "OK" -ForegroundColor Green }

if ($failed) {
    Write-Host "`n=== LINT FAILED ===" -ForegroundColor Red
    exit 1
}
Write-Host "`n=== LINT PASSED ===" -ForegroundColor Green
exit 0
