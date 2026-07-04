#!/usr/bin/env bash
# (Re)lance le seed de données initiales.
set -e
cd "$(dirname "$0")/.."
docker compose run --rm backend seed
