#!/bin/bash

set -euo pipefail

COMPOSE_CMD=(docker compose)

echo "Starting FillTheWord setup..."
echo "============================="

if ! docker info >/dev/null 2>&1; then
    echo "Docker is not running. Start Docker and try again."
    exit 1
fi

echo "Creating local directories..."
mkdir -p audio/{en,pt,es}/{word,sentence}
mkdir -p tts_models

echo "Building and starting services..."
"${COMPOSE_CMD[@]}" up -d --build

echo "Waiting for database..."
until "${COMPOSE_CMD[@]}" exec -T db pg_isready -U ftw_user -d filltheword >/dev/null 2>&1; do
    echo "  database not ready yet"
    sleep 2
done

echo "Database is ready."

echo "Seeding database..."
"${COMPOSE_CMD[@]}" exec -T api python scripts/seed_data.py

echo "Checking service health..."
"${COMPOSE_CMD[@]}" exec -T api python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
"${COMPOSE_CMD[@]}" exec -T tts curl -fsS http://localhost:8001/health >/dev/null

echo
echo "FillTheWord is running."
echo "======================="
echo "Frontend:  http://localhost:3007"
echo "API docs:  http://localhost:8000/docs"
echo "TTS:       http://localhost:8001/health"
echo "Database:  localhost:5432 (user: ftw_user, db: filltheword)"
echo
echo "Useful commands:"
echo "  ${COMPOSE_CMD[*]} ps"
echo "  ${COMPOSE_CMD[*]} logs -f"
echo "  ${COMPOSE_CMD[*]} down"
