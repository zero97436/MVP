#!/usr/bin/env bash
# Applique les migrations Alembic dans le conteneur backend.
set -e
cd "$(dirname "$0")/.."
docker compose run --rm backend migrate
