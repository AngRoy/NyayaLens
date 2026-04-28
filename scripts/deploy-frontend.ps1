# Deploy the Flutter web bundle to Firebase Hosting.
#
# Runs analyze + tests, builds the release bundle pointed at the Hosting URL
# (so the API_BASE compiled into main.dart.js routes through the
# Firebase Hosting -> Cloud Run rewrite), then deploys.
#
# Usage: ./scripts/deploy-frontend.ps1

param(
    [string]$Project = "nyayalens-28b93",
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"

$flutterBin = "Y:\SDK\flutter\bin"
if (Test-Path $flutterBin) { $env:PATH = "$flutterBin;$env:PATH" }

$repoRoot = Split-Path -Parent $PSScriptRoot

Push-Location "$repoRoot\frontend"
try {
    Write-Host "==> flutter pub get" -ForegroundColor Cyan
    flutter pub get
    if ($LASTEXITCODE -ne 0) { Write-Host "[fail] pub get failed" -ForegroundColor Red ; exit 1 }

    if (-not $SkipTests) {
        Write-Host "==> flutter test --no-pub" -ForegroundColor Cyan
        flutter test --no-pub
        if ($LASTEXITCODE -ne 0) { Write-Host "[fail] tests failed" -ForegroundColor Red ; exit 1 }
    }
    else {
        Write-Host "==> skipping tests (-SkipTests)" -ForegroundColor Yellow
    }

    Write-Host "==> flutter build web --release" -ForegroundColor Cyan
    if (Test-Path "build\web") { Remove-Item -Recurse -Force "build\web" }
    flutter build web --release --dart-define=API_BASE=https://$Project.web.app/api/v1
    if ($LASTEXITCODE -ne 0) { Write-Host "[fail] web build failed" -ForegroundColor Red ; exit 1 }

    if (-not (Test-Path "build\web\main.dart.js")) {
        Write-Host "[fail] build\web\main.dart.js not produced" -ForegroundColor Red
        exit 1
    }
}
finally {
    Pop-Location
}

Push-Location $repoRoot
try {
    Write-Host "==> firebase deploy --only hosting" -ForegroundColor Cyan
    firebase deploy --only hosting --project $Project
    if ($LASTEXITCODE -ne 0) { Write-Host "[fail] hosting deploy failed" -ForegroundColor Red ; exit 1 }
}
finally {
    Pop-Location
}

Write-Host "OK Frontend deployed: https://$Project.web.app" -ForegroundColor Green
Write-Host "   Hard refresh the browser (Ctrl+Shift+R) to bust the index.html cache."
