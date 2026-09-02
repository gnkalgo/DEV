[CmdletBinding()]
param(
    [switch]$Rebuild
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $projectRoot ".env"
$docker = Get-Command docker -ErrorAction SilentlyContinue
if (-not $docker) {
    $dockerPath = "C:\Program Files\Docker\Docker\resources\bin\docker.exe"
    if (-not (Test-Path -LiteralPath $dockerPath)) { throw "Docker CLI not found. Install or start Docker Desktop." }
    $dockerExe = $dockerPath
} else {
    $dockerExe = $docker.Source
}
$env:Path = (Split-Path -Parent $dockerExe) + ";" + $env:Path

function Wait-HttpOk([string]$Uri, [int]$Attempts = 20) {
    for ($attempt = 1; $attempt -le $Attempts; $attempt++) {
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri $Uri -TimeoutSec 5
            if ($response.StatusCode -eq 200) { return $response }
        } catch {
            if ($attempt -eq $Attempts) { throw "Service did not become ready: $Uri. $($_.Exception.Message)" }
        }
        Start-Sleep -Seconds 2
    }
    throw "Service did not become ready: $Uri"
}

if (-not (Test-Path -LiteralPath $envFile)) {
    throw "Missing $envFile. Copy .env.example to .env and configure it first."
}

& $dockerExe info *> $null
if ($LASTEXITCODE -ne 0) { throw "Docker Desktop is not running." }

Push-Location $projectRoot
try {
    $legacyFrontend = & $dockerExe ps -aq --filter "name=^gnk_dev-frontend-1$"
    if ($legacyFrontend) {
        $labelsJson = & $dockerExe inspect gnk_dev-frontend-1 --format '{{json .Config.Labels}}' 2>$null
        $labels = if ($labelsJson) { $labelsJson | ConvertFrom-Json } else { $null }
        $composeService = if ($labels) { $labels.'com.docker.compose.service' } else { $null }
        if (-not $composeService) {
            Write-Host "Replacing legacy standalone frontend container..."
            & $dockerExe rm -f gnk_dev-frontend-1 | Out-Null
        }
    }

    $arguments = @("compose", "-p", "gnk_dev", "up", "-d")
    if ($Rebuild) { $arguments += @("--build", "--force-recreate") }
    & $dockerExe @arguments
    if ($LASTEXITCODE -ne 0) { throw "Docker Compose startup failed." }

    & $dockerExe compose -p gnk_dev exec -T backend alembic upgrade head
    if ($LASTEXITCODE -ne 0) { throw "Database migration failed." }

    [void](Wait-HttpOk "http://localhost:8000/health")
    [void](Wait-HttpOk "http://localhost:3000/login")

    & $dockerExe compose -p gnk_dev ps
    Write-Host "GnKAlgo is ready: http://localhost:3000" -ForegroundColor Green
} finally {
    Pop-Location
}
