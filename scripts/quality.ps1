#!/usr/bin/env pwsh
# IVA — Combined quality script
# Run from repository root: .\scripts\quality.ps1
Write-Host "=== IVA Quality Checks ===" -ForegroundColor Cyan

Write-Host "`n--- Running lint checks ---" -ForegroundColor Yellow
& "$PSScriptRoot\lint.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Quality check ABORTED: lint failed" -ForegroundColor Red
    exit 1
}

Write-Host "`n--- Running tests ---" -ForegroundColor Yellow
& "$PSScriptRoot\test.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Quality check FAILED: tests failed" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== ALL QUALITY CHECKS PASSED ===" -ForegroundColor Green
exit 0
