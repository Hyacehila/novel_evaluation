Set-StrictMode -Version Latest

$script:RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

function Get-RepoRoot {
    return $script:RepoRoot
}

function Assert-Command {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command '$Name' was not found. Install dependencies first."
    }
}

function Ensure-ProjectEnvFile {
    param(
        [string]$EnvPath = (Join-Path (Get-RepoRoot) ".env"),
        [string]$ExamplePath = (Join-Path (Get-RepoRoot) ".env.example")
    )

    if ((-not (Test-Path $EnvPath)) -and (Test-Path $ExamplePath)) {
        Copy-Item $ExamplePath $EnvPath
        Write-Host "Created .env from .env.example."
    }
}

function Import-ProjectEnv {
    param(
        [string]$EnvPath = (Join-Path (Get-RepoRoot) ".env")
    )

    if (-not (Test-Path $EnvPath)) {
        return
    }

    foreach ($rawLine in Get-Content $EnvPath) {
        $line = $rawLine.Trim()
        if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith("#")) {
            continue
        }

        $parts = $line -split "=", 2
        if ($parts.Count -ne 2) {
            continue
        }

        $name = $parts[0].Trim()
        $value = $parts[1].Trim()

        if (
            ($value.StartsWith('"') -and $value.EndsWith('"')) -or
            ($value.StartsWith("'") -and $value.EndsWith("'"))
        ) {
            $value = $value.Substring(1, $value.Length - 2)
        }

        [Environment]::SetEnvironmentVariable($name, $value, "Process")
    }
}

function Get-EnvOrDefault {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [string]$Default
    )

    $value = [Environment]::GetEnvironmentVariable($Name, "Process")
    if ([string]::IsNullOrWhiteSpace($value)) {
        return $Default
    }
    return $value
}

function Assert-PortAvailable {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ListenHost,
        [Parameter(Mandatory = $true)]
        [int]$Port,
        [Parameter(Mandatory = $true)]
        [string]$ServiceName
    )

    $listeners = @(Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue)
    if ($listeners.Count -eq 0) {
        return
    }

    $normalizedHost = $ListenHost.Trim().ToLowerInvariant()
    $matchingListeners = @(
        $listeners | Where-Object {
            $listenerHost = $_.LocalAddress.Trim().ToLowerInvariant()
            if ($normalizedHost -in @("127.0.0.1", "localhost", "::1")) {
                return $listenerHost -in @("127.0.0.1", "0.0.0.0", "::1", "::")
            }
            return $listenerHost -in @($normalizedHost, "0.0.0.0", "::")
        }
    )

    if ($matchingListeners.Count -eq 0) {
        return
    }

    $processDetails = foreach ($listener in ($matchingListeners | Sort-Object OwningProcess -Unique)) {
        $process = Get-CimInstance Win32_Process -Filter "ProcessId = $($listener.OwningProcess)" -ErrorAction SilentlyContinue
        $commandLine = if ($process -and $process.CommandLine) { $process.CommandLine.Trim() } else { "<unknown command line>" }
        "PID $($listener.OwningProcess) listening on $($listener.LocalAddress):$Port`n  $commandLine"
    }

    throw @"
$ServiceName 无法启动：$ListenHost`:$Port 已被占用。
$($processDetails -join "`n")
请先关闭占用该端口的旧进程，再重新运行启动脚本。
"@
}
