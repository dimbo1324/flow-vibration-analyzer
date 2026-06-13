#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Управление Docker-окружением IVA.

.DESCRIPTION
    Скрипт предоставляет удобные команды для сборки образа и запуска сервисов
    из docker-compose.yml. Docker — опциональный инструмент: он не требуется для
    разработки и запуска GUI на Windows; его назначение — воспроизводимые
    проверки в Linux-среде, аналогичные GitHub Actions CI.

.EXAMPLE
    .\scripts\docker.ps1 build
.EXAMPLE
    .\scripts\docker.ps1 quality
.EXAMPLE
    .\scripts\docker.ps1 test
.EXAMPLE
    .\scripts\docker.ps1 cli-demo
.EXAMPLE
    .\scripts\docker.ps1 shell
.EXAMPLE
    .\scripts\docker.ps1 clean

.NOTES
    Совместимо с Windows PowerShell 5.1 и PowerShell 7+.
    Требует установленного Docker Desktop для Windows.
#>

[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet("build", "quality", "test", "cli-demo", "shell", "clean", "help")]
    [string]$Command = "help"
)

$ErrorActionPreference = "Stop"

# Корень репозитория вычисляется относительно скрипта, не от текущего каталога.
$repoRoot = Split-Path -Parent $PSScriptRoot

function Write-DockerStatus {
    param(
        [ValidateSet("OK", "FAILED", "INFO", "WARN")] [string]$Tag,
        [string]$Message
    )
    $color = switch ($Tag) {
        "OK"     { "Green" }
        "FAILED" { "Red" }
        "WARN"   { "Yellow" }
        default  { "Cyan" }
    }
    Write-Host "[$Tag] " -ForegroundColor $color -NoNewline
    Write-Host $Message
}

function Test-DockerAvailable {
    # Проверяем доступность Docker перед любой операцией — иначе получим
    # непонятную ошибку вместо ясного сообщения.
    $dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
    if ($null -eq $dockerCmd) {
        Write-DockerStatus "FAILED" "Docker не найден на PATH."
        Write-Host ""
        Write-Host "Установите Docker Desktop для Windows:" -ForegroundColor Yellow
        Write-Host "  https://docs.docker.com/desktop/install/windows-install/"
        Write-Host ""
        Write-Host "Docker — опциональный инструмент. Для локальной разработки он не нужен."
        Write-Host "Используйте вместо него:"
        Write-Host "  .\scripts\iva.ps1 quality"
        Write-Host "  .\scripts\iva.ps1 test"
        exit 1
    }
    # Проверяем, что демон запущен (docker info — быстрая проверка).
    $null = & docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-DockerStatus "FAILED" "Docker установлен, но демон не запущен. Запустите Docker Desktop."
        exit 1
    }
}

function Show-DockerHelp {
    Write-Host "=== IVA Docker-автоматизация ===" -ForegroundColor Cyan
    Write-Host "Использование: .\scripts\docker.ps1 <команда>"
    Write-Host ""
    Write-Host "Команды:"
    Write-Host "  build      Собрать Docker-образ iva-dev"
    Write-Host "  quality    Линтер + тесты (black, ruff, mypy, pytest)"
    Write-Host "  test       Тесты с покрытием"
    Write-Host "  cli-demo   CLI-демо анализа, вывод в ./out/"
    Write-Host "  shell      Интерактивная оболочка внутри контейнера"
    Write-Host "  clean      Удалить образ и тома Docker"
    Write-Host ""
    Write-Host "Примечание: Docker — опциональный инструмент." -ForegroundColor Yellow
    Write-Host "Для обычной разработки используйте: .\scripts\iva.ps1 quality"
}

Push-Location $repoRoot
try {
    switch ($Command) {
        "help" {
            Show-DockerHelp
            exit 0
        }
        "build" {
            Test-DockerAvailable
            Write-DockerStatus "INFO" "Сборка образа iva-dev ..."
            & docker build -t iva-dev .
            if ($LASTEXITCODE -ne 0) {
                Write-DockerStatus "FAILED" "Сборка образа завершилась с ошибкой."
                exit 1
            }
            Write-DockerStatus "OK" "Образ iva-dev собран."
        }
        "quality" {
            Test-DockerAvailable
            Write-DockerStatus "INFO" "Запуск проверок качества в Docker ..."
            & docker compose run --rm quality
            if ($LASTEXITCODE -ne 0) {
                Write-DockerStatus "FAILED" "Проверки качества завершились с ошибкой (код $LASTEXITCODE)."
                exit $LASTEXITCODE
            }
            Write-DockerStatus "OK" "Проверки качества пройдены."
        }
        "test" {
            Test-DockerAvailable
            Write-DockerStatus "INFO" "Запуск тестов в Docker ..."
            & docker compose run --rm test
            if ($LASTEXITCODE -ne 0) {
                Write-DockerStatus "FAILED" "Тесты завершились с ошибкой (код $LASTEXITCODE)."
                exit $LASTEXITCODE
            }
            Write-DockerStatus "OK" "Тесты пройдены."
        }
        "cli-demo" {
            Test-DockerAvailable
            Write-DockerStatus "INFO" "Запуск CLI-демо в Docker ..."
            & docker compose run --rm cli-demo
            if ($LASTEXITCODE -ne 0) {
                Write-DockerStatus "FAILED" "CLI-демо завершилось с ошибкой (код $LASTEXITCODE)."
                exit $LASTEXITCODE
            }
            Write-DockerStatus "OK" "CLI-демо завершено. Результаты: ./out/cli-runs/demo_docker/"
        }
        "shell" {
            Test-DockerAvailable
            Write-DockerStatus "INFO" "Открытие интерактивной оболочки в контейнере ..."
            & docker run --rm -it -v "${repoRoot}:/app" iva-dev bash
        }
        "clean" {
            Test-DockerAvailable
            Write-DockerStatus "INFO" "Удаление образа и томов Docker ..."
            & docker compose down --volumes --remove-orphans 2>&1 | Out-Null
            & docker rmi iva-dev 2>&1 | Out-Null
            Write-DockerStatus "OK" "Образ и тома Docker удалены."
        }
        default {
            Show-DockerHelp
            exit 1
        }
    }
} finally {
    Pop-Location
}

exit 0
