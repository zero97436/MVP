#!/usr/bin/env bash
# Sauvegarde PostgreSQL de supervision-house (Linux / macOS).
#   ./scripts/backup.sh [nb_a_garder]   (défaut 7)
set -e
KEEP="${1:-7}"
cd "$(dirname "$0")/.."

USER_="${POSTGRES_USER:-supervision}"
DB_="${POSTGRES_DB:-supervision}"
mkdir -p backups
NAME="supervision_$(date +%Y%m%d_%H%M%S).dump"

echo "Sauvegarde -> backups/$NAME ..."
docker compose exec -T db pg_dump -U "$USER_" -F c -f "/backups/$NAME" "$DB_"
echo "OK : $NAME ($(du -h "backups/$NAME" | cut -f1))"

# Rotation : garder les $KEEP plus récentes.
ls -1t backups/supervision_*.dump 2>/dev/null | tail -n +$((KEEP + 1)) | while read -r f; do
  rm -f "$f" && echo "  purge : $(basename "$f")"
done
