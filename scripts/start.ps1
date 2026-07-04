# Lance toute la stack supervision-house via Docker Compose (Windows / PowerShell).
# Usage :  .\scripts\start.ps1            (démarre)
#          .\scripts\start.ps1 -Down      (arrête)
#          .\scripts\start.ps1 -Logs      (suit les logs)
param(
    [switch]$Down,
    [switch]$Logs,
    [switch]$Rebuild
)

$ErrorActionPreference = "Stop"

# Se placer à la racine du projet (dossier parent de /scripts).
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

# Vérifier que Docker est disponible.
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker n'est pas installé ou pas dans le PATH." -ForegroundColor Red
    Write-Host "   Installe Docker Desktop : https://www.docker.com/products/docker-desktop/"
    exit 1
}

if ($Down) {
    Write-Host "🛑 Arrêt de la stack..." -ForegroundColor Yellow
    docker compose down
    exit 0
}

if ($Logs) {
    docker compose logs -f
    exit 0
}

# Créer .env depuis .env.example au premier lancement.
if (-not (Test-Path ".env")) {
    Write-Host "📄 Création de .env depuis .env.example" -ForegroundColor Cyan
    Copy-Item ".env.example" ".env"
}

Write-Host "🚀 Démarrage de supervision-house..." -ForegroundColor Green
if ($Rebuild) {
    docker compose up -d --build --force-recreate
} else {
    docker compose up -d --build
}

Write-Host ""
Write-Host "✅ supervision-house est lancé." -ForegroundColor Green
Write-Host "   Interface web : http://localhost:8080"
Write-Host "   API / Swagger : http://localhost:8000/docs"
Write-Host "   Login         : admin@local / admin1234"
Write-Host ""
Write-Host "   Logs    : .\scripts\start.ps1 -Logs"
Write-Host "   Arrêter : .\scripts\start.ps1 -Down"
