# Three-point smoke test for the deployed stack.
#
# Hits Cloud Run /health directly, the Hosting root, and the
# /api/v1/audits endpoint via the Hosting -> Cloud Run rewrite.
# Exits non-zero on any failure so it can be wired into CI later.
#
# Usage: ./scripts/smoke.ps1

param(
    [string]$Project = "nyayalens-28b93",
    [string]$Region = "asia-south1",
    [string]$Service = "nyayalens-api"
)

$ErrorActionPreference = "Stop"

$gcloudBin = "$env:LOCALAPPDATA\Google\Cloud SDK\google-cloud-sdk\bin"
if (Test-Path $gcloudBin) { $env:PATH = "$gcloudBin;$env:PATH" }

$failed = 0

Write-Host "==> Cloud Run /health (direct)" -ForegroundColor Cyan
try {
    $runUrl = (gcloud run services describe $Service --project $Project --region $Region --format "value(status.url)").Trim()
    $health = Invoke-RestMethod "$runUrl/health"
    Write-Host ($health | ConvertTo-Json -Compress)
    if ($health.status -ne "ok") { Write-Host "[fail] /health.status != ok" -ForegroundColor Red ; $failed++ }
}
catch {
    Write-Host "[fail] $($_.Exception.Message)" -ForegroundColor Red
    $failed++
}

Write-Host ""
Write-Host "==> Hosting root" -ForegroundColor Cyan
try {
    $r = Invoke-WebRequest "https://$Project.web.app/" -UseBasicParsing
    Write-Host "HTTP $($r.StatusCode)"
    if ($r.StatusCode -ne 200) { Write-Host "[fail] hosting root not 200" -ForegroundColor Red ; $failed++ }
}
catch {
    Write-Host "[fail] $($_.Exception.Message)" -ForegroundColor Red
    $failed++
}

Write-Host ""
Write-Host "==> /api/v1/audits via Hosting rewrite" -ForegroundColor Cyan
try {
    $headers = @{
        "X-User-Id"          = "demo-uid"
        "X-User-Name"        = "Demo Reviewer"
        "X-User-Role"        = "admin"
        "X-Organization-Id"  = "demo-org"
    }
    $audits = Invoke-RestMethod "https://$Project.web.app/api/v1/audits" -Headers $headers
    Write-Host ($audits | ConvertTo-Json -Compress)
}
catch {
    Write-Host "[fail] $($_.Exception.Message)" -ForegroundColor Red
    $failed++
}

Write-Host ""
if ($failed -gt 0) {
    Write-Host "FAIL $failed smoke test(s) failed" -ForegroundColor Red
    exit 1
}
Write-Host "OK All smoke tests green" -ForegroundColor Green
