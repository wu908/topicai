$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$scanRoots = @(
    ".github",
    "backend/app",
    "backend/config",
    "backend/tests",
    "frontend/e2e",
    "frontend/src",
    "scripts",
    "specs/008-content-project-mvp"
)
$rootFiles = @("README.md", "docker-compose.yml")
$extensions = @(
    ".css", ".env", ".example", ".html", ".js", ".json", ".md", ".mjs",
    ".py", ".ps1", ".sh", ".sql", ".toml", ".ts", ".tsx", ".yaml", ".yml"
)
$markers = @(
    [string][char]0xFFFD,
    [string][char]0x00C3,
    [string][char]0x00C2,
    -join @([char]0x00E2, [char]0x20AC),
    -join @([char]0x00F0, [char]0x0178),
    -join @([char]0x951F, [char]0x65A4, [char]0x62F7)
)
$utf8 = [Text.UTF8Encoding]::new($false, $true)

$files = @()
foreach ($relativeRoot in $scanRoots) {
    $root = Join-Path $repoRoot $relativeRoot
    $files += Get-ChildItem -LiteralPath $root -Recurse -File
}
foreach ($relativeFile in $rootFiles) {
    $files += Get-Item -LiteralPath (Join-Path $repoRoot $relativeFile)
}

$violations = @()
foreach ($file in $files | Sort-Object FullName -Unique) {
    if (($extensions -notcontains $file.Extension) -and ($rootFiles -notcontains $file.Name)) {
        continue
    }

    $relativePath = $file.FullName.Substring($repoRoot.Length + 1)
    try {
        $content = $utf8.GetString([IO.File]::ReadAllBytes($file.FullName))
    }
    catch {
        $violations += "${relativePath}: invalid UTF-8"
        continue
    }

    foreach ($marker in $markers) {
        $index = $content.IndexOf($marker, [StringComparison]::Ordinal)
        if ($index -ge 0) {
            $line = [regex]::Matches($content.Substring(0, $index), "`n").Count + 1
            $violations += "${relativePath}:${line}: mojibake marker '$marker'"
        }
    }
}

if ($violations.Count -gt 0) {
    $violations | ForEach-Object { Write-Error $_ }
    exit 1
}

Write-Host "UTF-8 and mojibake scan passed."
