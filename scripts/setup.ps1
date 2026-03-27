[CmdletBinding()]
param()

Set-StrictMode -Version Latest

. (Join-Path $PSScriptRoot "common.ps1")

Assert-Command "uv"
Assert-Command "pnpm"

Ensure-ProjectEnvFile

$repoRoot = Get-RepoRoot
Push-Location $repoRoot
try {
    Write-Host "Installing API dependencies..."
    & uv sync --project apps/api

    Write-Host "Installing worker dependencies..."
    & uv sync --project apps/worker

    Write-Host "Installing web dependencies..."
    & pnpm --dir apps/web install

    Write-Host "Setup completed."
}
finally {
    Pop-Location
}
