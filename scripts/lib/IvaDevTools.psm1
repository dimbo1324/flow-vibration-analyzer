<#
.SYNOPSIS
    Общие вспомогательные функции для PowerShell-скриптов IVA.

.DESCRIPTION
    Этот модуль собирает в одном месте код, который раньше дублировался почти
    в каждом скрипте: определение корня репозитория, единообразный вывод
    статуса, безопасный запуск шагов с проверкой кода возврата и работу с
    виртуальным окружением. Цель — убрать копипасту и сделать поведение всех
    скриптов одинаковым и предсказуемым.

    Совместимо с Windows PowerShell 5.1 и PowerShell 7+.
#>

Set-StrictMode -Version Latest

function Get-IvaRepositoryRoot {
    <#
    .SYNOPSIS
        Вернуть абсолютный путь к корню репозитория IVA.
    .DESCRIPTION
        Корень определяется относительно расположения этого модуля
        (scripts/lib/), а не от текущего рабочего каталога. Это важно: скрипт
        могут запустить из любой папки, и жёстко прописывать пути пользователя
        нельзя.
    #>
    [CmdletBinding()]
    param()
    # $PSScriptRoot указывает на scripts/lib, поэтому поднимаемся на два уровня.
    return [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
}

function Write-IvaStatus {
    <#
    .SYNOPSIS
        Печать строки статуса в едином формате [TAG] message.
    .DESCRIPTION
        Все скрипты используют одинаковые метки [OK]/[FAILED]/[INFO]/[WARN],
        чтобы вывод выглядел последовательно и легко читался в журналах сборки.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)] [ValidateSet("OK", "FAILED", "INFO", "WARN")] [string]$Tag,
        [Parameter(Mandatory)] [string]$Message
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

function Invoke-IvaStep {
    <#
    .SYNOPSIS
        Выполнить внешнюю команду и остановить сценарий при ошибке.
    .DESCRIPTION
        Нужна для цепочек шагов (проверки, сборка): если очередной шаг вернул
        ненулевой код, дальнейшее выполнение бессмысленно и потенциально
        опасно (например, продолжать релизную сборку после падения тестов).
        Код возврата сохраняется и пробрасывается наружу без искажения.
    .PARAMETER Name
        Человекочитаемое название шага для сообщений.
    .PARAMETER Action
        Блок-скрипт с самой командой.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)] [string]$Name,
        [Parameter(Mandatory)] [scriptblock]$Action
    )
    Write-IvaStatus "INFO" "Шаг: $Name ..."
    & $Action
    $code = $LASTEXITCODE
    # $LASTEXITCODE заполняется только нативными командами; для чистых
    # PowerShell-блоков он может остаться пустым — это считаем успехом.
    if ($null -ne $code -and $code -ne 0) {
        Write-IvaStatus "FAILED" "$Name (код возврата $code)."
        exit $code
    }
    Write-IvaStatus "OK" "$Name — выполнено."
}

function Get-IvaVenvPython {
    <#
    .SYNOPSIS
        Вернуть путь к python.exe внутри локального .venv.
    .DESCRIPTION
        Скрипты должны работать именно с интерпретатором проекта, а не с
        глобальным Python, чтобы зависимости и версии были предсказуемы.
    #>
    [CmdletBinding()]
    param([string]$RepositoryRoot = (Get-IvaRepositoryRoot))
    return Join-Path $RepositoryRoot ".venv\Scripts\python.exe"
}

function Test-IvaVenv {
    <#
    .SYNOPSIS
        Проверить, что виртуальное окружение создано и пригодно к запуску.
    #>
    [CmdletBinding()]
    param([string]$RepositoryRoot = (Get-IvaRepositoryRoot))
    $python = Get-IvaVenvPython -RepositoryRoot $RepositoryRoot
    return (Test-Path -LiteralPath $python)
}

function Set-IvaHeadlessQtEnvironment {
    <#
    .SYNOPSIS
        Включить безоконный режим Qt/Matplotlib и вернуть прежние значения.
    .DESCRIPTION
        Переменные окружения в PowerShell действуют на весь процесс. Если
        выставить offscreen-режим и не вернуть обратно, последующий запуск GUI
        в том же окне окажется невидимым. Поэтому функция возвращает снимок
        прежних значений, который затем передаётся в Restore-IvaEnvironment.
    #>
    [CmdletBinding()]
    param()
    $snapshot = @{
        QT_QPA_PLATFORM = $env:QT_QPA_PLATFORM
        QT_OPENGL       = $env:QT_OPENGL
        MPLBACKEND      = $env:MPLBACKEND
    }
    $env:QT_QPA_PLATFORM = "offscreen"
    $env:QT_OPENGL = "software"
    $env:MPLBACKEND = "Agg"
    return $snapshot
}

function Restore-IvaEnvironment {
    <#
    .SYNOPSIS
        Восстановить переменные окружения из снимка Set-IvaHeadlessQtEnvironment.
    .DESCRIPTION
        Значение $null означает, что переменной изначально не было — тогда её
        нужно удалить, а не выставлять в пустую строку, иначе offscreen-режим
        останется «прилипшим» к сессии.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)] [hashtable]$Snapshot)
    foreach ($name in @("QT_QPA_PLATFORM", "QT_OPENGL", "MPLBACKEND")) {
        $value = $Snapshot[$name]
        if ($null -eq $value) {
            Remove-Item "Env:$name" -ErrorAction SilentlyContinue
        } else {
            Set-Item "Env:$name" $value
        }
    }
}

Export-ModuleMember -Function `
    Get-IvaRepositoryRoot, `
    Write-IvaStatus, `
    Invoke-IvaStep, `
    Get-IvaVenvPython, `
    Test-IvaVenv, `
    Set-IvaHeadlessQtEnvironment, `
    Restore-IvaEnvironment
