[CmdletBinding()]
param()

Set-StrictMode -Version Latest

. (Join-Path $PSScriptRoot "common.ps1")

Assert-Command "uv"
Ensure-ProjectEnvFile
Import-ProjectEnv

$apiHost = Get-EnvOrDefault -Name "NOVEL_EVAL_API_HOST" -Default "127.0.0.1"
$apiPort = Get-EnvOrDefault -Name "NOVEL_EVAL_API_PORT" -Default "8000"
Assert-PortAvailable -ListenHost $apiHost -Port ([int]$apiPort) -ServiceName "API"

$repoRoot = Get-RepoRoot
Push-Location $repoRoot
try {
    Write-Host "Starting API at http://$apiHost`:$apiPort"
    & uv run --project apps/api uvicorn api.app:app --reload --host $apiHost --port $apiPort
}
finally {
    Pop-Location
}
