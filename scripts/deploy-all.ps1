# Deploy backend then frontend.
#
# Order matters: backend ships first so any new endpoint is live before the
# UI that consumes it. If the backend fails, the frontend deploy is skipped.
#
# Usage: ./scripts/deploy-all.ps1

param(
    [string]$Project = "nyayalens-28b93",
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"
$here = $PSScriptRoot

Write-Host "===== BACKEND =====" -ForegroundColor Magenta
& "$here\deploy-backend.ps1" -Project $Project
if ($LASTEXITCODE -ne 0) { Write-Host "[fail] backend failed; skipping frontend" -ForegroundColor Red ; exit 1 }

Write-Host ""
Write-Host "===== FRONTEND =====" -ForegroundColor Magenta
if ($SkipTests) {
    & "$here\deploy-frontend.ps1" -Project $Project -SkipTests
}
else {
    & "$here\deploy-frontend.ps1" -Project $Project
}
if ($LASTEXITCODE -ne 0) { Write-Host "[fail] frontend deploy failed" -ForegroundColor Red ; exit 1 }

Write-Host ""
Write-Host "OK Full stack deployed: https://$Project.web.app" -ForegroundColor Green
