$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
docker compose run --rm --no-deps --entrypoint pytest backend
Set-Location (Join-Path $Root "frontend")
if (-not (Test-Path "node_modules")) {
    npm install
}
npm test
