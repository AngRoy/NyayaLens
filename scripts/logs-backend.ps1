# Tail the most recent Cloud Run logs for the backend service.
#
# Usage:
#   ./scripts/logs-backend.ps1              # last 50 lines
#   ./scripts/logs-backend.ps1 -Lines 200   # last 200 lines

param(
    [string]$Project = "nyayalens-28b93",
    [string]$Region = "asia-south1",
    [string]$Service = "nyayalens-api",
    [int]$Lines = 50
)

$ErrorActionPreference = "Stop"

$gcloudBin = "$env:LOCALAPPDATA\Google\Cloud SDK\google-cloud-sdk\bin"
if (Test-Path $gcloudBin) { $env:PATH = "$gcloudBin;$env:PATH" }

gcloud run services logs read $Service --project $Project --region $Region --limit $Lines
