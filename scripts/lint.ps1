#!/usr/bin/env pwsh
# IVA — проверки форматирования, линтера и типов
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Import-Module (Join-Path $PSScriptRoot "lib\IvaDevTools.psm1") -Force

$repoRoot = Get-IvaRepositoryRoot
if (-not (Test-IvaVenv -RepositoryRoot $repoRoot)) {
    Write-IvaStatus "FAILED" ".venv не найден. Сначала выполните .\scripts\iva.ps1 setup."
    exit 1
}
$python = Get-IvaVenvPython -RepositoryRoot $repoRoot

Write-Host "=== IVA Lint Checks ===" -ForegroundColor Cyan

$failed = $false

# Mypy ищет pyproject.toml от текущего каталога, поэтому абсолютных путей к
# исходникам недостаточно. Временно переходим в корень и обязательно возвращаем
# исходный каталог, чтобы прямой запуск скрипта не менял сессию разработчика.
Push-Location $repoRoot
try {
    Write-Host "`n[1/3] Black format check..." -ForegroundColor Yellow
    & $python -m black --check .
    if ($LASTEXITCODE -ne 0) { $failed = $true; Write-Host "[FAILED]" -ForegroundColor Red }
    else { Write-Host "[OK]" -ForegroundColor Green }

    Write-Host "`n[2/3] Ruff lint check..." -ForegroundColor Yellow
    & $python -m ruff check .
    if ($LASTEXITCODE -ne 0) { $failed = $true; Write-Host "[FAILED]" -ForegroundColor Red }
    else { Write-Host "[OK]" -ForegroundColor Green }

    Write-Host "`n[3/3] Mypy type check..." -ForegroundColor Yellow
    & $python -m mypy iva main.py
    if ($LASTEXITCODE -ne 0) { $failed = $true; Write-Host "[FAILED]" -ForegroundColor Red }
    else { Write-Host "[OK]" -ForegroundColor Green }
} finally {
    Pop-Location
}

if ($failed) {
    Write-Host "`n[FAILED] === LINT FAILED ===" -ForegroundColor Red
    exit 1
}
Write-Host "`n[OK] === LINT PASSED ===" -ForegroundColor Green
exit 0
