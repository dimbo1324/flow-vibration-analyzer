#!/usr/bin/env pwsh
# IVA — объединённая проверка качества
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Import-Module (Join-Path $PSScriptRoot "lib\IvaDevTools.psm1") -Force

Write-Host "=== IVA Quality Checks ===" -ForegroundColor Cyan

Write-Host "`n[INFO] --- Running lint checks ---" -ForegroundColor Yellow
& "$PSScriptRoot\lint.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-IvaStatus "FAILED" "Quality остановлен: lint вернул код $LASTEXITCODE."
    exit $LASTEXITCODE
}

Write-Host "`n[INFO] --- Running tests ---" -ForegroundColor Yellow
& "$PSScriptRoot\test.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-IvaStatus "FAILED" "Quality завершился ошибкой: тесты вернули код $LASTEXITCODE."
    exit $LASTEXITCODE
}

Write-Host "`n[OK] === ALL QUALITY CHECKS PASSED ===" -ForegroundColor Green
exit 0
