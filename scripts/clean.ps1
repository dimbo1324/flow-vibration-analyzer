#!/usr/bin/env pwsh
<##############################################################################
.SYNOPSIS
    Безопасная очистка локальных артефактов IVA на Windows.

.DESCRIPTION
    Скрипт остаётся тонкой PowerShell-обёрткой над clean_project.py, чтобы
    правила безопасности не расходились между Windows, CI и другими ОС.
    Реальное удаление требует -Force, а виртуальное окружение включается только
    отдельным флагом -IncludeVenv.

.EXAMPLE
    .\scripts\clean.ps1 -DryRun
.EXAMPLE
    .\scripts\clean.ps1 -Force -KeepLogs
.EXAMPLE
    .\scripts\clean.ps1 -DryRun -IncludeVenv

.NOTES
    Совместимо с Windows PowerShell 5.1 и PowerShell 7+.
##############################################################################>

[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$Force,
    [switch]$KeepLogs,
    [switch]$IncludeVenv
)

$ErrorActionPreference = "Stop"
Import-Module (Join-Path $PSScriptRoot "lib\IvaDevTools.psm1") -Force

$repoRoot = Get-IvaRepositoryRoot
$cleaner = Join-Path $PSScriptRoot "clean_project.py"
$python = $null

if (Test-IvaVenv -RepositoryRoot $repoRoot) {
    $venvPython = Get-IvaVenvPython -RepositoryRoot $repoRoot
    if ($IncludeVenv) {
        # Нельзя надёжно удалить python.exe, пока он выполняет очистку. Для
        # IncludeVenv берём базовый интерпретатор, из которого создана .venv.
        $basePython = (& $venvPython -c "import sys; print(getattr(sys, '_base_executable', sys.executable))").Trim()
        if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $basePython -PathType Leaf)) {
            $python = $basePython
        }
    } else {
        $python = $venvPython
    }
}

if ($null -eq $python) {
    $systemPython = Get-Command python -ErrorAction SilentlyContinue
    if ($null -eq $systemPython) {
        Write-IvaStatus "FAILED" "Python не найден. Установите Python 3.11+ или выполните setup."
        exit 1
    }
    $python = $systemPython.Source
}

$arguments = @($cleaner)
if ($DryRun) { $arguments += "--dry-run" }
if ($Force) { $arguments += "--force" }
if ($KeepLogs) { $arguments += "--keep-logs" }
if ($IncludeVenv) { $arguments += "--include-venv" }

Push-Location $repoRoot
try {
    & $python @arguments
    $exitCode = $LASTEXITCODE
} finally {
    Pop-Location
}

exit $exitCode
