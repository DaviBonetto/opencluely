param()

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$targets = @(
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "__pycache__",
    "logs",
    "data",
    "quarantine",
    "tmp"
)
$files = @(
    "barratop.py",
    "floating_bar_preview.png",
    "floating_bar_preview_transcript.png",
    "floating_bar_preview_ui_fix.png"
)

foreach ($target in $targets) {
    $fullPath = Join-Path $repoRoot $target
    if (Test-Path $fullPath) {
        Remove-Item $fullPath -Recurse -Force
        Write-Host "Removed $target"
    }
}

foreach ($file in $files) {
    $fullPath = Join-Path $repoRoot $file
    if (Test-Path $fullPath) {
        Remove-Item $fullPath -Force
        Write-Host "Removed $file"
    }
}

Get-ChildItem -Path $repoRoot -Directory -Recurse -Filter "__pycache__" | ForEach-Object {
    Remove-Item $_.FullName -Recurse -Force
    Write-Host "Removed $($_.FullName.Substring($repoRoot.Length + 1))"
}
