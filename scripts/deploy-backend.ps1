# Deploy the FastAPI backend to Cloud Run.
#
# Builds the container with the current git SHA, pushes to Artifact Registry,
# rolls a new Cloud Run revision, and smoke tests /health.
#
# Usage: ./scripts/deploy-backend.ps1
#
# Refuses to deploy if backend/ has uncommitted changes (the image SHA must
# match what is in git so rollbacks are reproducible).

param(
    [string]$Project = "nyayalens-28b93",
    [string]$Region = "asia-south1",
    [string]$Repo = "nyayalens",
    [string]$Service = "nyayalens-api"
)

$ErrorActionPreference = "Stop"

$gcloudBin = "$env:LOCALAPPDATA\Google\Cloud SDK\google-cloud-sdk\bin"
if (Test-Path $gcloudBin) { $env:PATH = "$gcloudBin;$env:PATH" }

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    $dirty = git status --porcelain backend/ 2>$null
    if ($dirty) {
        Write-Host "[refuse] backend/ has uncommitted changes:" -ForegroundColor Red
        Write-Host $dirty
        Write-Host "Commit or stash before deploying so the image SHA matches what is in git."
        exit 1
    }

    $shortSha = (git rev-parse --short HEAD).Trim()
    $image = "$Region-docker.pkg.dev/$Project/$Repo/${Service}:${shortSha}"

    Write-Host "==> Building $image" -ForegroundColor Cyan
    gcloud builds submit backend --tag $image --project $Project --timeout=20m
    if ($LASTEXITCODE -ne 0) { Write-Host "[fail] cloud build failed" -ForegroundColor Red ; exit 1 }

    Write-Host "==> Deploying revision to Cloud Run" -ForegroundColor Cyan
    gcloud run deploy $Service --project $Project --region $Region --image $image
    if ($LASTEXITCODE -ne 0) { Write-Host "[fail] cloud run deploy failed" -ForegroundColor Red ; exit 1 }

    Write-Host "==> Smoke test /health" -ForegroundColor Cyan
    $url = (gcloud run services describe $Service --project $Project --region $Region --format "value(status.url)").Trim()
    $health = Invoke-RestMethod "$url/health"
    $healthJson = $health | ConvertTo-Json -Compress
    Write-Host $healthJson
    if ($health.status -ne "ok") {
        Write-Host "[fail] /health did not return status=ok" -ForegroundColor Red
        exit 1
    }

    Write-Host "OK Backend deployed: $url" -ForegroundColor Green
    Write-Host "   via Hosting rewrite: https://$Project.web.app/api/v1/*"
}
finally {
    Pop-Location
}
