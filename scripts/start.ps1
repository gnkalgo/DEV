$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example — change CHANGE_ME secrets before production."
}
docker compose up -d --build
docker compose run --rm --entrypoint alembic backend upgrade head
