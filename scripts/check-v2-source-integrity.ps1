$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$sourceRoots = @(
    "backend/app/api/v2",
    "backend/app/models/v2",
    "backend/app/services",
    "frontend/src/services/api/v2",
    "frontend/src/types/contracts/v2"
)
$extensions = @(".py", ".ts", ".tsx")
$rules = @(
    @{
        Name = "legacy runtime source"
        Pattern = "(?i)\b(DataManager|LLMDataSource|TianAPI|BilibiliSource|PreloadedDataSource)\b"
    },
    @{
        Name = "predictive field declaration"
        Pattern = '(?im)^\s*[''"]?(estimated_heat|composite_score|ctr_estimate|viral_probability|growth_probability|heat_score|trend_score)[''"]?\s*[:=]'
    }
)

$violations = @()
foreach ($relativeRoot in $sourceRoots) {
    $root = Join-Path $repoRoot $relativeRoot
    foreach ($file in Get-ChildItem -LiteralPath $root -Recurse -File) {
        if ($extensions -notcontains $file.Extension) {
            continue
        }

        $content = [IO.File]::ReadAllText($file.FullName)
        foreach ($rule in $rules) {
            foreach ($match in [regex]::Matches($content, $rule.Pattern)) {
                $line = [regex]::Matches($content.Substring(0, $match.Index), "`n").Count + 1
                $relativePath = $file.FullName.Substring($repoRoot.Length + 1)
                $violations += "${relativePath}:${line}: $($rule.Name): $($match.Value.Trim())"
            }
        }
    }
}

if ($violations.Count -gt 0) {
    $violations | ForEach-Object { Write-Error $_ }
    exit 1
}

Write-Host "V2 source-integrity scan passed."
