#!/usr/bin/env pwsh
#
# clean.ps1 - Remove repository-local generated artifacts (Windows).
#
# Purpose:
#   Remove known caches, coverage data, build output, reports, and runtime output.
#
# Usage:
#   .\scripts\clean.ps1 -DryRun
#   .\scripts\clean.ps1
#   .\scripts\clean.ps1 -Force
#   .\scripts\clean.ps1 -Force -KeepLogs
#
# Safety notes:
#   - Only known generated names below can be removed.
#   - .git, .venv, source, tests, docs, config, and data are never removed.
#   - DryRun never deletes; without Force, interactive confirmation is required.
#
# Windows PowerShell 5.1 compatible. PowerShell 7+ is recommended.

[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$Force,
    [switch]$KeepLogs
)

$ErrorActionPreference = "Stop"
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$rootPrefix = $repoRoot.TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar

function Write-Status {
    param([string]$Tag, [string]$Message, [string]$Color)
    Write-Host "[$Tag] " -ForegroundColor $Color -NoNewline
    Write-Host $Message
}

function Test-InRepository {
    param([string]$Path)
    $fullPath = [IO.Path]::GetFullPath($Path)
    return $fullPath.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)
}

function Test-UnderDirectory {
    param([string]$Path, [string[]]$Directories)
    $fullPath = [IO.Path]::GetFullPath($Path)
    foreach ($directory in $Directories) {
        $prefix = [IO.Path]::GetFullPath($directory).TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
        if ($fullPath.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
            return $true
        }
    }
    return $false
}

Write-Host "=== IVA Clean ===" -ForegroundColor Cyan
Write-Status "INFO" "Repository root: $repoRoot" "Cyan"
if ($DryRun) {
    Write-Status "INFO" "DRY RUN - nothing will be deleted." "Yellow"
}

$topLevelDirectoryNames = @("reports", ".tmp", ".pytest_cache", ".mypy_cache", ".ruff_cache", "build", "dist")
if (-not $KeepLogs) {
    $topLevelDirectoryNames += "out"
}

$directories = New-Object System.Collections.Generic.List[string]
$files = New-Object System.Collections.Generic.List[string]

foreach ($name in $topLevelDirectoryNames) {
    $path = Join-Path $repoRoot $name
    if (Test-Path -LiteralPath $path -PathType Container) {
        $directories.Add([IO.Path]::GetFullPath($path))
    }
}

foreach ($name in @(".coverage")) {
    $path = Join-Path $repoRoot $name
    if (Test-Path -LiteralPath $path -PathType Leaf) {
        $files.Add([IO.Path]::GetFullPath($path))
    }
}

Get-ChildItem -LiteralPath $repoRoot -Filter ".coverage.*" -File -Force -ErrorAction SilentlyContinue |
    ForEach-Object { $files.Add($_.FullName) }

# Avoid traversing repository metadata, virtual environments, and top-level
# directories that are already scheduled for removal.
$excludedScanNames = @(".git", ".venv", "venv") + $topLevelDirectoryNames
$scanRoots = Get-ChildItem -LiteralPath $repoRoot -Force -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -notin $excludedScanNames }

foreach ($scanRoot in $scanRoots) {
    $items = @($scanRoot)
    if ($scanRoot.PSIsContainer) {
        $items += Get-ChildItem -LiteralPath $scanRoot.FullName -Recurse -Force -ErrorAction SilentlyContinue
    }
    foreach ($item in $items) {
        if ($item.PSIsContainer -and ($item.Name -eq "__pycache__" -or $item.Name -like "*.egg-info")) {
            $directories.Add($item.FullName)
        } elseif (-not $item.PSIsContainer -and ($item.Extension -in @(".pyc", ".pyo"))) {
            $files.Add($item.FullName)
        }
    }
}

$directories = @($directories | Select-Object -Unique)
$files = @($files | Select-Object -Unique | Where-Object { -not (Test-UnderDirectory $_ $directories) })

foreach ($path in @($directories) + @($files)) {
    if (-not (Test-InRepository $path)) {
        Write-Status "FAILED" "Refusing to remove path outside repository: $path" "Red"
        exit 2
    }
}

$plannedFiles = $files.Count
$plannedDirectories = $directories.Count
[long]$plannedBytes = 0

foreach ($file in $files) {
    if (Test-Path -LiteralPath $file -PathType Leaf) {
        $plannedBytes += (Get-Item -LiteralPath $file -Force).Length
    }
}
foreach ($directory in $directories) {
    if (Test-Path -LiteralPath $directory -PathType Container) {
        $children = Get-ChildItem -LiteralPath $directory -Recurse -Force -ErrorAction SilentlyContinue
        $plannedFiles += @($children | Where-Object { -not $_.PSIsContainer }).Count
        $plannedDirectories += @($children | Where-Object { $_.PSIsContainer }).Count
        $size = ($children | Where-Object { -not $_.PSIsContainer } | Measure-Object Length -Sum).Sum
        if ($null -ne $size) {
            $plannedBytes += $size
        }
    }
}

$plannedMB = [math]::Round($plannedBytes / 1MB, 2)
if ($directories.Count -eq 0 -and $files.Count -eq 0) {
    Write-Status "OK" "Nothing to clean." "Green"
    exit 0
}

Write-Status "INFO" "Planned removal: $plannedDirectories directories, $plannedFiles files, ~$plannedMB MB." "Cyan"
foreach ($directory in $directories) {
    Write-Host "  [dir]  $directory" -ForegroundColor DarkGray
}
foreach ($file in $files) {
    Write-Host "  [file] $file" -ForegroundColor DarkGray
}

if ($DryRun) {
    Write-Status "OK" "DRY RUN complete - nothing was deleted." "Green"
    exit 0
}

if (-not $Force) {
    $answer = Read-Host "Delete the generated artifacts listed above? [y/N]"
    if ($answer -notmatch "^[Yy]$") {
        Write-Status "INFO" "Aborted by user. Nothing was deleted." "Yellow"
        exit 0
    }
}

$hadErrors = $false
foreach ($file in $files) {
    try {
        Remove-Item -LiteralPath $file -Force -ErrorAction Stop
    } catch {
        $hadErrors = $true
        Write-Status "FAILED" "Could not remove file '$file': $($_.Exception.Message)" "Red"
    }
}

foreach ($directory in ($directories | Sort-Object Length -Descending)) {
    try {
        Remove-Item -LiteralPath $directory -Recurse -Force -ErrorAction Stop
    } catch {
        $hadErrors = $true
        Write-Status "FAILED" "Could not remove directory '$directory': $($_.Exception.Message)" "Red"
    }
}

if ($hadErrors) {
    Write-Status "FAILED" "Cleanup completed with errors." "Red"
    exit 1
}

Write-Status "OK" "Removed $plannedDirectories directories and $plannedFiles files; freed ~$plannedMB MB." "Green"
exit 0
