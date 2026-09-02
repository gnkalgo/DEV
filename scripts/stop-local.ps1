[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$docker = Get-Command docker -ErrorAction SilentlyContinue
$dockerExe = if ($docker) { $docker.Source } else { "C:\Program Files\Docker\Docker\resources\bin\docker.exe" }
if (-not (Test-Path -LiteralPath $dockerExe)) { throw "Docker CLI not found." }

Push-Location $projectRoot
try {
    & $dockerExe compose -p gnk_dev down
    if ($LASTEXITCODE -ne 0) { throw "Docker Compose shutdown failed." }
    Write-Host "GnKAlgo stopped. Database volumes were preserved." -ForegroundColor Yellow
} finally {
    Pop-Location
}
