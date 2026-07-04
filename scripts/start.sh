#!/usr/bin/env bash
# Démarrage complet via Docker Compose.
set -e
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "Création de .env depuis .env.example"
  cp .env.example .env
fi

docker compose up -d --build
echo ""
echo "✅ supervision-house démarré."
echo "   UI       : http://localhost:8080"
echo "   API docs : http://localhost:8000/docs"
echo "   Login    : admin@local / admin1234"
