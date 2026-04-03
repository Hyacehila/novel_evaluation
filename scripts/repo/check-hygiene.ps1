[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\\..")).Path
$errors = New-Object System.Collections.Generic.List[string]

$bannedDirectories = @(
    "apps/api/contracts",
    "docs/architecture",
    "docs/contracts",
    "docs/decisions",
    "docs/getting-started",
    "docs/operations",
    "docs/planning",
    "docs/product",
    "docs/prompting",
    "docs/research",
    "packages/domain",
    "packages/shared",
    "packages/sdk",
    "packages/application/judge-orchestration",
    "packages/application/report-generation",
    "packages/application/scoring-pipeline",
    "prompts/calibration",
    "prompts/extraction",
    "prompts/scoring/system",
    "prompts/scoring/templates"
)

$allowedPackageDirectories = @(
    "application",
    "prompt-runtime",
    "provider-adapters",
    "runtime",
    "schemas"
)

$legacyTerms = @(
    "signingProbability",
    "commercialValue",
    "writingQuality",
    "innovationScore",
    "detailedAnalysis",
    "editorVerdictDraft",
    "detailedAnalysisDraft",
    "affectedSkeletonDimensions",
    "SkeletonDimensionId",
    "TopLevelScoreField"
)

foreach ($relativePath in $bannedDirectories) {
    $target = [System.IO.Path]::GetFullPath((Join-Path $repoRoot $relativePath))
    if (-not $target.StartsWith($repoRoot)) {
        throw "Path outside workspace: $target"
    }
    if (Test-Path $target) {
        $errors.Add("Banned path exists: $relativePath")
    }
}

$packagesRoot = Join-Path $repoRoot "packages"
if (Test-Path $packagesRoot) {
    Get-ChildItem -LiteralPath $packagesRoot -Directory | ForEach-Object {
        if ($allowedPackageDirectories -notcontains $_.Name) {
            $errors.Add("Unexpected top-level package directory: packages/$($_.Name)")
        }
    }
}

$scanRoots = @(
    (Join-Path $repoRoot "docs"),
    (Join-Path $repoRoot "prompts")
)
$scanExtensions = @(".md", ".yaml", ".yml", ".txt")
$filesToScan = foreach ($scanRoot in $scanRoots) {
    if (-not (Test-Path $scanRoot)) {
        continue
    }
    Get-ChildItem -LiteralPath $scanRoot -Recurse -File | Where-Object {
        $scanExtensions -contains $_.Extension.ToLowerInvariant()
    }
}

foreach ($term in $legacyTerms) {
    $matches = $filesToScan | Select-String -SimpleMatch $term
    foreach ($match in $matches) {
        $relativeFile = [System.IO.Path]::GetRelativePath($repoRoot, $match.Path)
        $errors.Add("Legacy term '$term' found in ${relativeFile}:$($match.LineNumber)")
    }
}

if ($errors.Count -gt 0) {
    Write-Host "Repository hygiene check failed:" -ForegroundColor Red
    foreach ($errorMessage in $errors) {
        Write-Host " - $errorMessage"
    }
    exit 1
}

Write-Host "Repository hygiene check passed."
