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
