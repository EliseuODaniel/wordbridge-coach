#!/bin/bash

set -euo pipefail

COMPOSE_CMD=(docker compose)
WITH_AI=0
WITH_AUDIO=0
DB_PORT="${FTW_DB_PORT:-5432}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --with-ai)
            WITH_AI=1
            shift
            ;;
        --with-audio)
            WITH_AUDIO=1
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: ./scripts/quick_start.sh [--with-ai] [--with-audio]"
            exit 1
            ;;
    esac
done

if [[ "$WITH_AI" -eq 1 ]]; then
    COMPOSE_CMD+=(--profile ai)
fi

if [[ "$WITH_AUDIO" -eq 1 ]]; then
    COMPOSE_CMD+=(--profile audio)
fi

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

echo "Applying database migrations..."
"${COMPOSE_CMD[@]}" exec -T api alembic upgrade head

echo "Seeding database..."
"${COMPOSE_CMD[@]}" exec -T api python scripts/seed_data.py

echo "Checking service health..."
"${COMPOSE_CMD[@]}" exec -T api python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

if [[ "$WITH_AUDIO" -eq 1 ]]; then
    "${COMPOSE_CMD[@]}" exec -T tts curl -fsS http://localhost:8001/health >/dev/null
fi

echo
echo "FillTheWord is running."
echo "======================="
echo "Frontend:  http://localhost:3007"
echo "API docs:  http://localhost:8000/docs"
echo "Database:  localhost:${DB_PORT} (user: ftw_user, db: filltheword)"
if [[ "$WITH_AUDIO" -eq 1 ]]; then
    echo "Audio:     enabled (TTS em http://localhost:8001/health)"
else
    echo "Audio:     disabled by default; rerun with --with-audio to enable local TTS"
fi
if [[ "$WITH_AI" -eq 1 ]]; then
    echo "AI stack:  enabled (Chat Coach local LLM + LanguageTool)"
else
    echo "AI stack:  disabled by default; rerun with --with-ai to enable Chat Coach services"
fi
echo
echo "Useful commands:"
echo "  ${COMPOSE_CMD[*]} ps"
echo "  ${COMPOSE_CMD[*]} logs -f"
echo "  ${COMPOSE_CMD[*]} down"
