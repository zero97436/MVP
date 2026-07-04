# Sauvegarde PostgreSQL de supervision-house (Windows / PowerShell).
#   .\scripts\backup.ps1            # crée une sauvegarde, garde les 7 dernières
#   .\scripts\backup.ps1 -Keep 30   # rétention personnalisée
param([int]$Keep = 7)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$user = if ($env:POSTGRES_USER) { $env:POSTGRES_USER } else { "supervision" }
$db   = if ($env:POSTGRES_DB)   { $env:POSTGRES_DB }   else { "supervision" }

New-Item -ItemType Directory -Force (Join-Path $root "backups") | Out-Null
$ts   = Get-Date -Format "yyyyMMdd_HHmmss"
$name = "supervision_$ts.dump"

Write-Host "Sauvegarde -> backups/$name ..." -ForegroundColor Cyan
# pg_dump tourne DANS le conteneur db (même version) et écrit dans /backups (monté).
docker compose exec -T db pg_dump -U $user -F c -f "/backups/$name" $db
if ($LASTEXITCODE -ne 0) { throw "pg_dump a échoué (code $LASTEXITCODE)" }

$file = Join-Path $root "backups\$name"
$size = [math]::Round((Get-Item $file).Length / 1KB, 1)
Write-Host "OK : $name ($size Ko)" -ForegroundColor Green

# Rotation : ne garder que les $Keep plus récentes.
$old = Get-ChildItem (Join-Path $root "backups") -Filter "supervision_*.dump" |
       Sort-Object LastWriteTime -Descending | Select-Object -Skip $Keep
foreach ($f in $old) { Remove-Item $f.FullName -Force; Write-Host "  purge : $($f.Name)" }
