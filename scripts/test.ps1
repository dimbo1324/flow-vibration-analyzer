#!/usr/bin/env pwsh
# IVA — тесты с покрытием
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

Write-Host "=== IVA Tests (with coverage) ===" -ForegroundColor Cyan

# Qt-переменные действуют на весь процесс PowerShell, поэтому обязательно
# восстанавливаем их даже после падения pytest: иначе следующий GUI-запуск
# в том же терминале окажется невидимым.
$environment = Set-IvaHeadlessQtEnvironment
Push-Location $repoRoot
try {
    & $python -m pytest --cov=iva/core --cov-report=term-missing --cov-fail-under=80 -m "not performance"
    $testExitCode = $LASTEXITCODE
} finally {
    Pop-Location
    Restore-IvaEnvironment -Snapshot $environment
}

if ($testExitCode -ne 0) {
    Write-Host "[FAILED] === TESTS FAILED ===" -ForegroundColor Red
    exit $testExitCode
}
Write-Host "[OK] === TESTS PASSED ===" -ForegroundColor Green
exit 0
