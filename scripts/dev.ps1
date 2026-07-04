# Lance supervision-house en mode DÉVELOPPEMENT local, sans Docker (Windows / PowerShell).
#
# Pré-requis :
#   - Python 3.12+  et  Node 20+
#   - Postgres et Redis accessibles (le plus simple : docker compose up -d db redis)
#
# Le script ouvre 4 fenêtres PowerShell : API, worker, scheduler, frontend.
# Usage :  .\scripts\dev.ps1
param(
    [switch]$SkipInfra  # ne pas démarrer db/redis via Docker
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$backend  = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"

# Variables d'environnement pour le dev local (db/redis sur localhost).
$env:DATABASE_URL          = "postgresql+psycopg2://supervision:supervision@localhost:5432/supervision"
$env:REDIS_URL             = "redis://localhost:6379/0"
$env:CELERY_BROKER_URL     = "redis://localhost:6379/1"
$env:CELERY_RESULT_BACKEND = "redis://localhost:6379/2"

# 1) Infra (Postgres + Redis) via Docker, sauf si -SkipInfra.
if (-not $SkipInfra) {
    if (Get-Command docker -ErrorAction SilentlyContinue) {
        Write-Host "🐘 Démarrage de Postgres + Redis (Docker)..." -ForegroundColor Cyan
        docker compose up -d db redis
        Start-Sleep -Seconds 4
    } else {
        Write-Host "⚠️  Docker absent : assure-toi que Postgres et Redis tournent déjà." -ForegroundColor Yellow
    }
}

# 2) Backend : venv + dépendances.
Set-Location $backend
if (-not (Test-Path ".venv")) {
    Write-Host "🐍 Création du venv Python..." -ForegroundColor Cyan
    python -m venv .venv
}
$py = Join-Path $backend ".venv\Scripts\python.exe"
Write-Host "📦 Installation des dépendances backend..." -ForegroundColor Cyan
& $py -m pip install --quiet --upgrade pip
& $py -m pip install --quiet -r requirements.txt

# 3) Migrations + seed.
Write-Host "🗃️  Migrations Alembic + seed..." -ForegroundColor Cyan
& $py -m alembic upgrade head
& $py -m app.db.seed

# 4) Frontend : dépendances.
Set-Location $frontend
if (-not (Test-Path "node_modules")) {
    Write-Host "📦 Installation des dépendances frontend..." -ForegroundColor Cyan
    npm install
}

# 5) Lancer les 4 process dans des fenêtres séparées.
Write-Host "🚀 Lancement API / worker / scheduler / frontend..." -ForegroundColor Green

Start-Process powershell -ArgumentList "-NoExit","-Command",
    "Set-Location '$backend'; `$env:DATABASE_URL='$($env:DATABASE_URL)'; & '$py' -m uvicorn app.main:app --reload --port 8000"

Start-Process powershell -ArgumentList "-NoExit","-Command",
    "Set-Location '$backend'; `$env:CELERY_BROKER_URL='$($env:CELERY_BROKER_URL)'; & '$py' -m celery -A app.workers.celery_app.celery_app worker --loglevel=info --pool=solo"

Start-Process powershell -ArgumentList "-NoExit","-Command",
    "Set-Location '$backend'; `$env:DATABASE_URL='$($env:DATABASE_URL)'; & '$py' -m app.workers.scheduler"

Start-Process powershell -ArgumentList "-NoExit","-Command",
    "Set-Location '$frontend'; npm run dev"

Write-Host ""
Write-Host "✅ Tout est lancé (4 fenêtres ouvertes)." -ForegroundColor Green
Write-Host "   Frontend (dev) : http://localhost:5173"
Write-Host "   API / Swagger  : http://localhost:8000/docs"
Write-Host "   Login          : admin@local / admin1234"
