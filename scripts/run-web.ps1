[CmdletBinding()]
param()

Set-StrictMode -Version Latest

. (Join-Path $PSScriptRoot "common.ps1")

Assert-Command "pnpm"
Ensure-ProjectEnvFile
Import-ProjectEnv

$apiHost = Get-EnvOrDefault -Name "NOVEL_EVAL_API_HOST" -Default "127.0.0.1"
$apiPort = Get-EnvOrDefault -Name "NOVEL_EVAL_API_PORT" -Default "8000"
$webPort = Get-EnvOrDefault -Name "NOVEL_EVAL_WEB_PORT" -Default "3000"
Assert-PortAvailable -ListenHost "127.0.0.1" -Port ([int]$webPort) -ServiceName "Web"

$repoRoot = Get-RepoRoot
Push-Location $repoRoot
try {
    $env:NOVEL_EVAL_API_HOST = $apiHost
    $env:NOVEL_EVAL_API_PORT = $apiPort
    $env:NOVEL_EVAL_WEB_PORT = $webPort

    Write-Host "Starting web at http://127.0.0.1:$webPort"
    Write-Host "Proxying API to http://$apiHost`:$apiPort"
    & pnpm --dir apps/web dev -- --hostname 127.0.0.1 --port $webPort
}
finally {
    Pop-Location
}
