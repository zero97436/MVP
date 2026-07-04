# Restauration PostgreSQL de supervision-house (Windows / PowerShell).
#   .\scripts\restore.ps1 supervision_20260101_120000.dump
# ⚠️ Écrase les données actuelles par celles de la sauvegarde.
param([Parameter(Mandatory = $true)][string]$File)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$user = if ($env:POSTGRES_USER) { $env:POSTGRES_USER } else { "supervision" }
$db   = if ($env:POSTGRES_DB)   { $env:POSTGRES_DB }   else { "supervision" }

if (-not (Test-Path (Join-Path $root "backups\$File"))) { throw "Fichier introuvable : backups\$File" }
if ((Read-Host "Restaurer '$File' et ÉCRASER la base '$db' ? (oui/non)") -ne "oui") { Write-Host "Annulé."; exit }

Write-Host "Restauration de $File ..." -ForegroundColor Yellow
docker compose exec -T db pg_restore -U $user -d $db --clean --if-exists --no-owner "/backups/$File"
Write-Host "Restauration terminée. Redémarre le backend : docker compose restart backend" -ForegroundColor Green
