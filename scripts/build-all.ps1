#!/usr/bin/env pwsh
#
# build-all.ps1 — Полная оркестрация релизной сборки IVA (Windows)
#
# Назначение:
#   Выполнить релизную цепочку: очистить артефакты, запустить проверки качества,
#   затем собрать приложение и установщик через scripts\build_installer.py.
#
# Использование:
#   .\scripts\build-all.ps1                # очистка, quality и полная сборка
#   .\scripts\build-all.ps1 -SkipClean     # не очищать артефакты перед сборкой
#   .\scripts\build-all.ps1 -SkipTests     # пропустить тесты, сохранив lint
#   .\scripts\build-all.ps1 -CheckOnly     # только проверить окружение
#
# Безопасность:
#   - Любая ошибка немедленно останавливает цепочку с исходным кодом возврата.
#   - -CheckOnly ничего не удаляет и не запускает полную сборку.
#   - Пользовательские абсолютные пути не используются.
#
# Совместимость:
#   Поддерживается Windows PowerShell 5.1, рекомендуется PowerShell 7+.

[CmdletBinding()]
param(
    [switch]$SkipClean,
    [switch]$SkipTests,
    [switch]$CheckOnly
)

$ErrorActionPreference = "Stop"

Import-Module (Join-Path $PSScriptRoot "lib\IvaDevTools.psm1") -Force

function Stop-OnFailure {
    param([string]$Step)
    if ($LASTEXITCODE -ne 0) {
        Write-IvaStatus "FAILED" "$Step (код возврата $LASTEXITCODE)."
        exit $LASTEXITCODE
    }
}

$repoRoot = Get-IvaRepositoryRoot
$venvPython = Get-IvaVenvPython -RepositoryRoot $repoRoot
$buildScript = Join-Path $repoRoot "scripts\build_installer.py"

Write-Host "=== IVA Build All ===" -ForegroundColor Cyan
Write-IvaStatus "INFO" "Корень репозитория: $repoRoot"

if (-not (Test-IvaVenv -RepositoryRoot $repoRoot)) {
    Write-IvaStatus "FAILED" ".venv не найден. Сначала выполните .\scripts\iva.ps1 setup."
    exit 1
}

# Проверка окружения вынесена до очистки и quality: команда используется внутри
# безопасной цепочки `iva.ps1 all` и не должна менять рабочее дерево или повторно
# запускать уже пройденные тесты.
if ($CheckOnly) {
    Write-IvaStatus "INFO" "Проверка окружения сборки без создания артефактов ..."
    & $venvPython $buildScript --check-only
    Stop-OnFailure "Проверка окружения сборки завершилась ошибкой"
    Write-IvaStatus "OK" "Окружение сборки проверено."
    exit 0
}

# --- 1. Очистка --------------------------------------------------------------
if ($SkipClean) {
    Write-IvaStatus "INFO" "Очистка пропущена (-SkipClean)."
} else {
    Write-IvaStatus "INFO" "Очистка сгенерированных артефактов ..."
    & "$PSScriptRoot\clean.ps1" -Force
    Stop-OnFailure "Очистка завершилась ошибкой"
    Write-IvaStatus "OK" "Очистка завершена."
}

# --- 2. Проверки качества ----------------------------------------------------
if ($SkipTests) {
    Write-IvaStatus "INFO" "Запуск только lint (-SkipTests) ..."
    & "$PSScriptRoot\lint.ps1"
    Stop-OnFailure "Lint завершился ошибкой"
    Write-IvaStatus "OK" "Lint пройден."
} else {
    Write-IvaStatus "INFO" "Запуск quality (lint + tests) ..."
    & "$PSScriptRoot\quality.ps1"
    Stop-OnFailure "Проверки качества завершились ошибкой"
    Write-IvaStatus "OK" "Проверки качества пройдены."
}

# --- 3. Сборка ---------------------------------------------------------------
if ($SkipTests) {
    Write-IvaStatus "INFO" "Сборка с флагом --skip-tests ..."
    & $venvPython $buildScript --skip-tests
    Stop-OnFailure "Сборка завершилась ошибкой"
} else {
    Write-IvaStatus "INFO" "Сборка приложения и установщика ..."
    & $venvPython $buildScript
    Stop-OnFailure "Сборка завершилась ошибкой"
}

Write-Host ""
Write-IvaStatus "OK" "Цепочка сборки успешно завершена."
exit 0
