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
    "TopLevelScoreField",
    "deepseek-chat",
    "deepseek-reasoner"
)

$legacyReferenceTerms = @(
    "apps/api/contracts",
    "docs/architecture/",
    "docs/contracts/",
    "docs/decisions/",
    "docs/getting-started/",
    "docs/operations/",
    "docs/planning/",
    "docs/product/",
    "docs/prompting/",
    "docs/research/",
    "packages/domain/",
    "packages/shared/",
    "packages/sdk/"
)

$secretPatterns = @(
    @{
        Name = "DeepSeek/OpenAI style API key"
        Pattern = [regex]'(?<![A-Za-z0-9_])sk-[A-Za-z0-9_-]{12,}'
    }
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
$rootScanFiles = @(
    "README.md",
    "CONTRIBUTING.md",
    "CLAUDE.md",
    ".env.example"
) | ForEach-Object {
    Join-Path $repoRoot $_
} | Where-Object {
    Test-Path $_
} | ForEach-Object {
    Get-Item $_
}
$scanExtensions = @(".md", ".yaml", ".yml", ".txt")
$filesToScan = @(
    foreach ($scanRoot in $scanRoots) {
    if (-not (Test-Path $scanRoot)) {
        continue
    }
    Get-ChildItem -LiteralPath $scanRoot -Recurse -File | Where-Object {
        $scanExtensions -contains $_.Extension.ToLowerInvariant()
    }
    }
    $rootScanFiles
) | Sort-Object FullName -Unique

foreach ($term in $legacyTerms) {
    $matches = $filesToScan | Select-String -SimpleMatch $term
    foreach ($match in $matches) {
        $relativeFile = [System.IO.Path]::GetRelativePath($repoRoot, $match.Path)
        $errors.Add("Legacy term '$term' found in ${relativeFile}:$($match.LineNumber)")
    }
}

foreach ($term in $legacyReferenceTerms) {
    $matches = $filesToScan | Select-String -SimpleMatch $term
    foreach ($match in $matches) {
        $relativeFile = [System.IO.Path]::GetRelativePath($repoRoot, $match.Path)
        $errors.Add("Legacy reference '$term' found in ${relativeFile}:$($match.LineNumber)")
    }
}

foreach ($secretPattern in $secretPatterns) {
    foreach ($file in $filesToScan) {
        $lines = @(Get-Content -LiteralPath $file.FullName)
        for ($lineIndex = 0; $lineIndex -lt $lines.Count; $lineIndex++) {
            $line = $lines[$lineIndex]
            if (-not $secretPattern.Pattern.IsMatch($line)) {
                continue
            }
            $relativeFile = [System.IO.Path]::GetRelativePath($repoRoot, $file.FullName)
            $errors.Add("Possible secret '$($secretPattern.Name)' found in ${relativeFile}:$($lineIndex + 1)")
        }
    }
}

$markdownFiles = $filesToScan | Where-Object {
    $_.Extension.ToLowerInvariant() -eq ".md"
}
$repoRootWithSeparator = $repoRoot.TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
$markdownLinkPattern = [regex]'!?\[[^\]]*\]\(([^)]+)\)'
foreach ($file in $markdownFiles) {
    $lines = @(Get-Content -LiteralPath $file.FullName)
    for ($lineIndex = 0; $lineIndex -lt $lines.Count; $lineIndex++) {
        foreach ($match in $markdownLinkPattern.Matches($lines[$lineIndex])) {
            $rawTarget = $match.Groups[1].Value.Trim()
            if (-not $rawTarget) {
                continue
            }
            if ($rawTarget.StartsWith("#") -or $rawTarget -match "^[a-zA-Z][a-zA-Z0-9+.-]*:") {
                continue
            }
            $targetWithoutAnchor = ($rawTarget -split "#", 2)[0]
            $targetPath = ($targetWithoutAnchor -split "\?", 2)[0].Trim()
            if (-not $targetPath) {
                continue
            }
            $targetPath = [System.Uri]::UnescapeDataString($targetPath)
            $resolvedTarget = if ([System.IO.Path]::IsPathRooted($targetPath)) {
                [System.IO.Path]::GetFullPath($targetPath)
            }
            else {
                [System.IO.Path]::GetFullPath((Join-Path $file.DirectoryName $targetPath))
            }
            if ($resolvedTarget -ne $repoRoot -and -not $resolvedTarget.StartsWith($repoRootWithSeparator)) {
                $relativeFile = [System.IO.Path]::GetRelativePath($repoRoot, $file.FullName)
                $errors.Add("Local Markdown link points outside repository: ${relativeFile}:$($lineIndex + 1) -> $rawTarget")
                continue
            }
            if (-not (Test-Path $resolvedTarget)) {
                $relativeFile = [System.IO.Path]::GetRelativePath($repoRoot, $file.FullName)
                $errors.Add("Broken local Markdown link: ${relativeFile}:$($lineIndex + 1) -> $rawTarget")
            }
        }
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
