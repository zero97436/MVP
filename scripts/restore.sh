#!/usr/bin/env bash
# Restauration PostgreSQL de supervision-house (Linux / macOS).
#   ./scripts/restore.sh supervision_20260101_120000.dump
# ATTENTION : écrase les données actuelles.
set -e
FILE="${1:?Usage: restore.sh <fichier.dump>}"
cd "$(dirname "$0")/.."
USER_="${POSTGRES_USER:-supervision}"
DB_="${POSTGRES_DB:-supervision}"

[ -f "backups/$FILE" ] || { echo "Fichier introuvable : backups/$FILE"; exit 1; }
read -r -p "Restaurer '$FILE' et ÉCRASER la base '$DB_' ? (oui/non) " ans
[ "$ans" = "oui" ] || { echo "Annulé."; exit 0; }

echo "Restauration de $FILE ..."
docker compose exec -T db pg_restore -U "$USER_" -d "$DB_" --clean --if-exists --no-owner "/backups/$FILE"
echo "Terminé. Redémarre le backend : docker compose restart backend"
