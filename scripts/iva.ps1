#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Единая точка входа для рабочих команд IVA на Windows.

.DESCRIPTION
    Этот скрипт — удобная «обёртка-диспетчер»: он не дублирует логику, а
    вызывает уже существующие специализированные скрипты (setup.ps1, run.ps1,
    clean.ps1 и т.д.) и Python-инструменты. Так разработчику не нужно помнить
    десяток отдельных команд — достаточно одной.

    Поведение по безопасности:
      - сообщения выводятся на русском в едином формате;
      - коды возврата вложенных шагов сохраняются;
      - цепочка `all` останавливается на первом сбое;
      - разрушительная очистка выполняется только с явным -Force;
      - полная сборка установщика запускается только командой `build`.

.EXAMPLE
    .\scripts\iva.ps1 setup
.EXAMPLE
    .\scripts\iva.ps1 clean -DryRun
.EXAMPLE
    .\scripts\iva.ps1 all

.NOTES
    Совместимо с Windows PowerShell 5.1 и PowerShell 7+.
#>

[CmdletBinding()]
param(
    # Команда (см. список ниже). По умолчанию печатается справка.
    [Parameter(Position = 0)]
    [ValidateSet(
        "help", "setup", "setup-web", "run", "smoke", "lint", "test", "quality",
        "check", "diagnose", "clean", "clean-logs", "demo",
        "build-check", "build", "all",
        "web", "web-backend", "web-frontend"
    )]
    [string]$Command = "help",

    # Пробрасываемые флаги очистки/прочих подкоманд.
    [switch]$DryRun,
    [switch]$Force,
    [switch]$KeepLogs,
    [switch]$IncludeVenv,
    [switch]$CleanResults,
    [int]$OlderThanDays = 30
)

$ErrorActionPreference = "Stop"

# Подключаем общий модуль с помощниками. Путь строится относительно
# расположения скрипта, чтобы не зависеть от текущего каталога.
Import-Module (Join-Path $PSScriptRoot "lib\IvaDevTools.psm1") -Force

$repoRoot = Get-IvaRepositoryRoot
$venvPython = Get-IvaVenvPython -RepositoryRoot $repoRoot

function Invoke-Script {
    # Запустить другой скрипт из каталога scripts/ через splatting хэш-таблицы.
    # Хэш-таблица (а не массив) выбрана намеренно: пустой массив, возвращённый
    # из функции, в PowerShell «схлопывается» в $null и ломает передачу
    # аргументов, тогда как пустой @{} splat безопасен.
    param([string]$ScriptName, [hashtable]$BoundArgs = @{})
    $path = Join-Path $PSScriptRoot $ScriptName
    & $path @BoundArgs
}

function Invoke-PythonTool {
    # Запустить Python-инструмент интерпретатором проекта (.venv), если он есть,
    # иначе системным python — чтобы команда работала и до полного setup.
    param([string[]]$Arguments)
    # Относительные пути CLI и каталог out/ должны разрешаться от корня проекта,
    # даже если iva.ps1 вызван из другой директории.
    Push-Location $repoRoot
    try {
        if (Test-IvaVenv -RepositoryRoot $repoRoot) {
            & $venvPython @Arguments
        } else {
            Write-IvaStatus "WARN" ".venv не найден; используется системный python."
            & python @Arguments
        }
    } finally {
        Pop-Location
    }
}

function Show-Help {
    Write-Host "=== IVA — единая точка входа ===" -ForegroundColor Cyan
    Write-Host "Использование: .\scripts\iva.ps1 <команда> [флаги]"
    Write-Host ""
    Write-Host "Команды:"
    Write-Host "  setup         Создать окружение и установить зависимости"
    Write-Host "  setup-web     Установить веб-зависимости (FastAPI, uvicorn, httpx)"
    Write-Host "  run           Запустить графический интерфейс"
    Write-Host "  smoke         Безоконный smoke-тест приложения"
    Write-Host "  lint          Проверки стиля и типов (black, ruff, mypy)"
    Write-Host "  test          Тесты с покрытием"
    Write-Host "  quality       lint + test"
    Write-Host "  check         python scripts/check_project.py"
    Write-Host "  diagnose      python scripts/diagnose_project.py"
    Write-Host "  clean         Очистка (-DryRun/-Force/-KeepLogs/-IncludeVenv)"
    Write-Host "  clean-logs    Очистка логов (-DryRun/-Force/-OlderThanDays/-CleanResults)"
    Write-Host "  demo          Демо-анализ через CLI"
    Write-Host "  build-check   Проверка окружения сборки (без сборки)"
    Write-Host "  build         Полная сборка приложения и установщика"
    Write-Host "  all           Безопасная цепочка: smoke, quality, check, demo, build-check"
    Write-Host "  web           Запустить веб-интерфейс через Docker Compose"
    Write-Host "  web-backend   Запустить FastAPI бэкенд (без Docker, порт 8000)"
    Write-Host "  web-frontend  Запустить React фронтенд (pnpm dev, порт 5173)"
    Write-Host ""
    Write-Host "Совет: перед разрушительной очисткой используйте 'clean -DryRun'." -ForegroundColor Yellow
}

# Пробрасываемые флаги для clean.ps1 и clean-logs.ps1 собираем как хэш-таблицу,
# передавая только реально указанные пользователем ключи.
function Get-CleanBoundArgs {
    $bound = @{}
    if ($DryRun) { $bound["DryRun"] = $true }
    if ($Force) { $bound["Force"] = $true }
    if ($KeepLogs) { $bound["KeepLogs"] = $true }
    if ($IncludeVenv) { $bound["IncludeVenv"] = $true }
    return $bound
}

function Get-CleanLogsBoundArgs {
    $bound = @{}
    if ($DryRun) { $bound["DryRun"] = $true }
    if ($Force) { $bound["Force"] = $true }
    if ($CleanResults) { $bound["CleanResults"] = $true }
    if ($PSBoundParameters.ContainsKey("OlderThanDays")) {
        $bound["OlderThanDays"] = $OlderThanDays
    }
    return $bound
}

$demoArgs = @(
    "-m", "iva.cli.main", "demo",
    "--scenario", "clean_40hz",
    "--output", "out/cli-runs/demo_quick",
    "--export-html", "--save-project"
)

switch ($Command) {
    "help"        { Show-Help; exit 0 }
    "setup"       { Invoke-Script "setup.ps1"; exit $LASTEXITCODE }
    "run"         { Invoke-Script "run.ps1"; exit $LASTEXITCODE }
    "smoke"       { Invoke-Script "run.ps1" @{ SmokeTest = $true }; exit $LASTEXITCODE }
    "lint"        { Invoke-Script "lint.ps1"; exit $LASTEXITCODE }
    "test"        { Invoke-Script "test.ps1"; exit $LASTEXITCODE }
    "quality"     { Invoke-Script "quality.ps1"; exit $LASTEXITCODE }
    "check"       { Invoke-PythonTool @("scripts/check_project.py"); exit $LASTEXITCODE }
    "diagnose"    { Invoke-PythonTool @("scripts/diagnose_project.py"); exit $LASTEXITCODE }
    "clean" {
        # Через единую точку входа удаление разрешено только с явным -Force.
        # Старый clean.ps1 сохраняет интерактивный режим для обратной
        # совместимости, но автоматизация не должна зависеть от случайного ввода.
        if (-not $DryRun -and -not $Force) {
            Write-IvaStatus "FAILED" "Для удаления укажите -Force. Сначала рекомендуется clean -DryRun."
            exit 2
        }
        Invoke-Script "clean.ps1" (Get-CleanBoundArgs)
        exit $LASTEXITCODE
    }
    "clean-logs"  { Invoke-Script "clean-logs.ps1" (Get-CleanLogsBoundArgs); exit $LASTEXITCODE }
    "demo"        { Invoke-PythonTool $demoArgs; exit $LASTEXITCODE }
    "build-check" { Invoke-Script "build-all.ps1" @{ CheckOnly = $true }; exit $LASTEXITCODE }
    "build"       { Invoke-Script "build-all.ps1"; exit $LASTEXITCODE }
    "all" {
        # Безопасная цепочка для разработчика: проверяет работоспособность,
        # качество, демо и готовность окружения сборки — но НЕ собирает
        # установщик и НЕ удаляет файлы.
        Write-Host "=== IVA: безопасная цепочка проверок (all) ===" -ForegroundColor Cyan
        Invoke-IvaStep "smoke" { Invoke-Script "run.ps1" @{ SmokeTest = $true } }
        Invoke-IvaStep "quality" { Invoke-Script "quality.ps1" }
        Invoke-IvaStep "check" { Invoke-PythonTool @("scripts/check_project.py") }
        Invoke-IvaStep "demo" { Invoke-PythonTool $demoArgs }
        Invoke-IvaStep "build-check" { Invoke-Script "build-all.ps1" @{ CheckOnly = $true } }
        Write-IvaStatus "OK" "Цепочка 'all' успешно завершена."
        exit 0
    }
    "web"         { Invoke-Script "docker.ps1" @{ Command = "web-up" }; exit $LASTEXITCODE }
    "setup-web" {
        Write-IvaStatus "INFO" "Установка веб-зависимостей (FastAPI, uvicorn, httpx) ..."
        $webReqs = Join-Path $PSScriptRoot ".." "requirements-web.txt"
        & $venvPython -m pip install -r $webReqs
        if ($LASTEXITCODE -ne 0) {
            Write-IvaStatus "FAILED" "Установка веб-зависимостей завершилась с ошибкой."
            exit 1
        }
        Write-IvaStatus "OK" "Веб-зависимости установлены."
        & $venvPython -c "import fastapi; import uvicorn; import httpx; print('web deps ok')"
        exit $LASTEXITCODE
    }
    "web-backend" {
        Write-IvaStatus "INFO" "Запуск FastAPI бэкенда на http://127.0.0.1:8000 ..."
        Write-Host "  Документация API: http://127.0.0.1:8000/docs" -ForegroundColor Cyan
        Write-Host "  Нажмите Ctrl+C для остановки." -ForegroundColor Yellow
        Push-Location $repoRoot
        try {
            & $venvPython -m uvicorn iva.api.main:app --reload --host 127.0.0.1 --port 8000
        } finally {
            Pop-Location
        }
        exit $LASTEXITCODE
    }
    "web-frontend" {
        $frontendDir = Join-Path $repoRoot "web" "frontend"
        if (-not (Test-Path $frontendDir)) {
            Write-IvaStatus "FAILED" "Каталог web/frontend не найден."
            exit 1
        }
        Push-Location $frontendDir
        try {
            Write-IvaStatus "INFO" "Проверка зависимостей фронтенда ..."
            if (-not (Test-Path "node_modules")) {
                Write-IvaStatus "INFO" "node_modules не найден — запуск pnpm install ..."
                & pnpm install
                if ($LASTEXITCODE -ne 0) {
                    Write-IvaStatus "FAILED" "pnpm install завершился с ошибкой."
                    exit 1
                }
            }
            Write-IvaStatus "INFO" "Запуск React фронтенда на http://localhost:5173 ..."
            Write-Host "  Нажмите Ctrl+C для остановки." -ForegroundColor Yellow
            & pnpm dev
        } finally {
            Pop-Location
        }
        exit $LASTEXITCODE
    }
    default       { Show-Help; exit 1 }
}
