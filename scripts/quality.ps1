#!/usr/bin/env pwsh
# IVA — Combined quality script
# Run from repository root: .\scripts\quality.ps1
[CmdletBinding()]
param()

Write-Host "=== IVA Quality Checks ===" -ForegroundColor Cyan

Write-Host "`n[INFO] --- Running lint checks ---" -ForegroundColor Yellow
& "$PSScriptRoot\lint.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAILED] Quality check ABORTED: lint failed" -ForegroundColor Red
    exit 1
}

Write-Host "`n[INFO] --- Running tests ---" -ForegroundColor Yellow
& "$PSScriptRoot\test.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAILED] Quality check FAILED: tests failed" -ForegroundColor Red
    exit 1
}

Write-Host "`n[OK] === ALL QUALITY CHECKS PASSED ===" -ForegroundColor Green
exit 0
