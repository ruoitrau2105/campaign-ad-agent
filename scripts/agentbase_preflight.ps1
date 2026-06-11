param(
    [switch]$RunLocalGates
)

$ErrorActionPreference = "Stop"
$script:Failures = 0

function Write-Check {
    param(
        [string]$Name,
        [bool]$Passed,
        [string]$Detail = ""
    )

    $status = if ($Passed) { "PASS" } else { "FAIL" }
    if (-not $Passed) {
        $script:Failures += 1
    }
    $suffix = if ($Detail) { " - $Detail" } else { "" }
    Write-Host "[$status] $Name$suffix"
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

$gitBashCandidates = @(
    "C:\Program Files\Git\bin\bash.exe",
    "C:\Program Files\Git\usr\bin\bash.exe"
)
$gitBash = $gitBashCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
$gitBashDetail = if ($gitBash) { $gitBash } else { "Install Git for Windows with Git Bash" }
Write-Check "Git Bash" ([bool]$gitBash) $gitBashDetail

if ($gitBash) {
    $jqPath = (& $gitBash -lc "command -v jq" 2>$null)
    Write-Check "jq in Git Bash" ([bool]$jqPath) ($(if ($jqPath) { $jqPath } else { "Install jq and ensure Git Bash can find it on PATH" }))
} else {
    Write-Check "jq in Git Bash" $false "Git Bash is required before jq can be checked"
}

$docker = Get-Command docker -ErrorAction SilentlyContinue
$dockerDetail = if ($docker) { $docker.Source } else { "Install/start Docker Desktop" }
Write-Check "Docker CLI" ([bool]$docker) $dockerDetail

if ($gitBash) {
    & $gitBash ".agents/skills/agentbase/scripts/check_credentials.sh" "iam"
    Write-Check "AgentBase IAM credentials" ($LASTEXITCODE -eq 0) "checked with helper script; no secret values printed"
}

if ($RunLocalGates) {
    & ".\venv\Scripts\python.exe" -m pytest -q
    & ".\venv\Scripts\python.exe" "evals\run.py"
    & ".\scripts\smoke_docker.ps1"
}

if ($script:Failures -gt 0) {
    exit 1
}
