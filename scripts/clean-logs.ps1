#!/usr/bin/env pwsh
#
# clean-logs.ps1 - Remove old IVA user logs (Windows).
#
# Purpose:
#   Remove aged *.log files from Documents\IVA\logs and, only when explicitly
#   requested, remove saved items from Documents\IVA\results.
#
# Usage:
#   .\scripts\clean-logs.ps1
#   .\scripts\clean-logs.ps1 -OlderThanDays 7 -DryRun
#   .\scripts\clean-logs.ps1 -CleanResults
#   .\scripts\clean-logs.ps1 -CleanResults -Force
#
# Safety notes:
#   - Never deletes outside %USERPROFILE%\Documents\IVA.
#   - Results require CleanResults and confirmation unless Force is supplied.
#   - DryRun never deletes anything.
#
# Windows PowerShell 5.1 compatible. PowerShell 7+ is recommended.

[CmdletBinding()]
param(
    [ValidateRange(0, 36500)]
    [int]$OlderThanDays = 30,
    [switch]$Force,
    [switch]$DryRun,
    [switch]$CleanResults
)

$ErrorActionPreference = "Stop"

function Write-Status {
    param([string]$Tag, [string]$Message, [string]$Color)
    Write-Host "[$Tag] " -ForegroundColor $Color -NoNewline
    Write-Host $Message
}

Write-Host "=== IVA Log Cleanup ===" -ForegroundColor Cyan

if ([string]::IsNullOrWhiteSpace($env:USERPROFILE)) {
    Write-Status "FAILED" "USERPROFILE is not defined." "Red"
    exit 1
}

$ivaRoot = [IO.Path]::GetFullPath((Join-Path $env:USERPROFILE "Documents\IVA"))
$ivaPrefix = $ivaRoot.TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar

function Test-InIvaRoot {
    param([string]$Path)
    $fullPath = [IO.Path]::GetFullPath($Path)
    return $fullPath.StartsWith($ivaPrefix, [StringComparison]::OrdinalIgnoreCase)
}

if (-not (Test-Path -LiteralPath $ivaRoot -PathType Container)) {
    Write-Status "OK" "No IVA data directory at '$ivaRoot'; nothing to clean." "Green"
    exit 0
}

Write-Status "INFO" "Target directory: $ivaRoot" "Cyan"
if ($DryRun) {
    Write-Status "INFO" "DRY RUN - nothing will be deleted." "Yellow"
}

$cutoff = (Get-Date).AddDays(-$OlderThanDays)
$logsDirectory = Join-Path $ivaRoot "logs"
$logFiles = @()
if (Test-Path -LiteralPath $logsDirectory -PathType Container) {
    $logFiles = @(Get-ChildItem -LiteralPath $logsDirectory -Filter "*.log" -File -Force -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt $cutoff } |
        Sort-Object FullName -Unique)
}

foreach ($file in $logFiles) {
    if (-not (Test-InIvaRoot $file.FullName)) {
        Write-Status "FAILED" "Refusing to remove path outside IVA directory: $($file.FullName)" "Red"
        exit 2
    }
}

$resultsDirectory = Join-Path $ivaRoot "results"
$resultItems = @()
if ($CleanResults -and (Test-Path -LiteralPath $resultsDirectory -PathType Container)) {
    if (-not (Test-InIvaRoot $resultsDirectory)) {
        Write-Status "FAILED" "Refusing to clean results outside IVA directory." "Red"
        exit 2
    }
    $resultItems = @(Get-ChildItem -LiteralPath $resultsDirectory -Force -ErrorAction SilentlyContinue)
}

Write-Status "INFO" "Found $($logFiles.Count) log files older than $OlderThanDays days." "Cyan"
foreach ($file in $logFiles) {
    Write-Host "  [log] $($file.FullName)" -ForegroundColor DarkGray
}

$removeResults = $CleanResults -and $resultItems.Count -gt 0
if ($removeResults) {
    Write-Status "WARN" "Results cleanup requested for $($resultItems.Count) top-level items." "Yellow"
    if (-not $DryRun -and -not $Force) {
        $answer = Read-Host "Permanently delete all analysis results in '$resultsDirectory'? [y/N]"
        if ($answer -notmatch "^[Yy]$") {
            $removeResults = $false
            Write-Status "INFO" "Results cleanup declined; logs will still be processed." "Yellow"
        }
    }
}

if ($DryRun) {
    Write-Status "OK" "DRY RUN complete - no logs or results were deleted." "Green"
    exit 0
}

$removedLogs = 0
$removedResults = 0
$hadErrors = $false

foreach ($file in $logFiles) {
    try {
        Remove-Item -LiteralPath $file.FullName -Force -ErrorAction Stop
        $removedLogs++
    } catch {
        $hadErrors = $true
        Write-Status "FAILED" "Could not remove '$($file.FullName)': $($_.Exception.Message)" "Red"
    }
}

if ($removeResults) {
    foreach ($item in $resultItems) {
        try {
            Remove-Item -LiteralPath $item.FullName -Recurse -Force -ErrorAction Stop
            $removedResults++
        } catch {
            $hadErrors = $true
            Write-Status "FAILED" "Could not remove '$($item.FullName)': $($_.Exception.Message)" "Red"
        }
    }
}

if ($hadErrors) {
    Write-Status "FAILED" "Cleanup finished with errors after removing $removedLogs logs and $removedResults result items." "Red"
    exit 1
}

Write-Status "OK" "Removed $removedLogs logs and $removedResults result items." "Green"
exit 0
