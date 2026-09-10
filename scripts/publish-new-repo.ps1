param(
    [string]$RepositoryName = "microcredential-video-generator",
    [ValidateSet("private", "public")]
    [string]$Visibility = "private"
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw "GitHub CLI (gh) is not installed or not on PATH. Install it, then rerun this script."
}

& gh auth status
if ($LASTEXITCODE -ne 0) {
    throw "GitHub CLI is not authenticated. Run: gh auth login"
}

if (-not (Test-Path ".git")) {
    git init -b main
    git add .
    git commit -m "Initial microcredential video generator"
}

$visibilityFlag = if ($Visibility -eq "public") { "--public" } else { "--private" }
& gh repo create $RepositoryName $visibilityFlag --source . --remote origin --push
if ($LASTEXITCODE -ne 0) {
    throw "GitHub repository creation/push failed. Review the gh output above."
}

Write-Host "Repository created and pushed: $RepositoryName"
