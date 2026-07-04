#!/usr/bin/env bash
# Entrypoint multi-rôle : api | worker | scheduler | migrate | seed
set -e

ROLE="${1:-api}"

wait_for_db() {
  echo "Waiting for database..."
  python - <<'PY'
import time, sys
from sqlalchemy import create_engine, text
from app.core.config import settings
for _ in range(30):
    try:
        create_engine(settings.DATABASE_URL).connect().execute(text("SELECT 1"))
        print("Database is up.")
        sys.exit(0)
    except Exception:
        time.sleep(2)
print("Database not reachable", file=sys.stderr)
sys.exit(1)
PY
}

case "$ROLE" in
  api)
    wait_for_db
    alembic upgrade head
    python -m app.db.seed
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000
    ;;
  worker)
    wait_for_db
    exec celery -A app.workers.celery_app.celery_app worker --loglevel=info
    ;;
  scheduler)
    wait_for_db
    exec python -m app.workers.scheduler
    ;;
  migrate)
    wait_for_db
    exec alembic upgrade head
    ;;
  seed)
    wait_for_db
    exec python -m app.db.seed
    ;;
  *)
    exec "$@"
    ;;
esac
