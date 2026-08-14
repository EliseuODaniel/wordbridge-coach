#!/bin/bash

set -euo pipefail

PROJECT_NAME="${WORDBRIDGE_SMOKE_PROJECT:-wordbridge-smoke}"
DB_PORT="${WORDBRIDGE_DB_PORT:-55433}"
API_PORT="${WORDBRIDGE_API_PORT:-18000}"
FRONTEND_PORT="${WORDBRIDGE_FRONTEND_PORT:-13007}"
DOCKER_SUBNET="${WORDBRIDGE_DOCKER_SUBNET:-172.29.0.0/16}"
API_URL="${WORDBRIDGE_API_URL:-http://localhost:${API_PORT}}"
FRONTEND_URL="${WORDBRIDGE_FRONTEND_URL:-http://localhost:${FRONTEND_PORT}}"
KEEP_RUNNING=0
SKIP_BUILD=0

usage() {
    echo "Usage: ./scripts/smoke_local.sh [--keep-running] [--skip-build]"
    echo
    echo "Environment overrides:"
    echo "  WORDBRIDGE_SMOKE_PROJECT  Compose project name (default: wordbridge-smoke)"
    echo "  WORDBRIDGE_DB_PORT        Host Postgres port (default: 55433)"
    echo "  WORDBRIDGE_API_PORT       Host API port (default: 18000)"
    echo "  WORDBRIDGE_FRONTEND_PORT  Host frontend port (default: 13007)"
    echo "  WORDBRIDGE_DOCKER_SUBNET  Compose network subnet (default: 172.29.0.0/16)"
    echo "  WORDBRIDGE_API_URL        API URL (default: http://localhost:18000)"
    echo "  WORDBRIDGE_FRONTEND_URL   Frontend URL (default: http://localhost:13007)"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --keep-running)
            KEEP_RUNNING=1
            shift
            ;;
        --skip-build)
            SKIP_BUILD=1
            shift
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

export WORDBRIDGE_DB_PORT="$DB_PORT"
export WORDBRIDGE_API_PORT="$API_PORT"
export WORDBRIDGE_FRONTEND_PORT="$FRONTEND_PORT"
export WORDBRIDGE_DOCKER_SUBNET="$DOCKER_SUBNET"
COMPOSE_CMD=(docker compose -p "$PROJECT_NAME")

cleanup() {
    if [[ "$KEEP_RUNNING" -eq 1 ]]; then
        echo "Leaving smoke stack running: ${PROJECT_NAME}"
        return
    fi

    echo "Cleaning smoke stack: ${PROJECT_NAME}"
    "${COMPOSE_CMD[@]}" down -v --remove-orphans >/dev/null 2>&1 || true
}

trap cleanup EXIT

require_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "Missing required command: $1"
        exit 1
    fi
}

wait_for_http() {
    local url="$1"
    local label="$2"
    local attempts="${3:-90}"

    for attempt in $(seq 1 "$attempts"); do
        if curl -fsS "$url" >/dev/null; then
            echo "${label}: OK"
            return 0
        fi

        sleep 2
    done

    echo "${label}: FAILED"
    "${COMPOSE_CMD[@]}" ps || true
    "${COMPOSE_CMD[@]}" logs --tail=120 api frontend db || true
    return 1
}

json_get() {
    local expression="$1"
    python3 -c "
import json
import sys

data = json.load(sys.stdin)
print(${expression})
"
}

require_command docker
require_command curl
require_command python3

if ! docker info >/dev/null 2>&1; then
    echo "Docker is not running."
    exit 1
fi

echo "Preparing clean smoke stack: ${PROJECT_NAME}"
"${COMPOSE_CMD[@]}" down -v --remove-orphans >/dev/null 2>&1 || true

echo "Starting default stack on ports db=${DB_PORT}, api=${API_PORT}, frontend=${FRONTEND_PORT} and subnet ${DOCKER_SUBNET}"
if [[ "$SKIP_BUILD" -eq 1 ]]; then
    "${COMPOSE_CMD[@]}" up -d db api frontend
else
    "${COMPOSE_CMD[@]}" up -d --build db api frontend
fi

wait_for_http "${API_URL}/health" "API health"

echo "Applying migrations"
"${COMPOSE_CMD[@]}" exec -T api alembic upgrade head

echo "Seeding data"
"${COMPOSE_CMD[@]}" exec -T api python scripts/seed_data.py

echo "Checking curated seed idempotency"
"${COMPOSE_CMD[@]}" exec -T api python scripts/seed_curated_content.py

wait_for_http "${FRONTEND_URL}" "Frontend"

echo "Checking user list"
curl -fsS "${API_URL}/api/v1/users/" >/dev/null

SMOKE_USERNAME="smoke-$(date +%s)"
echo "Creating smoke user: ${SMOKE_USERNAME}"
USER_RESPONSE="$(
    curl -fsS \
        -X POST "${API_URL}/api/v1/users/" \
        -H "Content-Type: application/json" \
        -d "{\"username\":\"${SMOKE_USERNAME}\",\"language_preference\":\"pt\",\"target_language\":\"en\",\"word_goal_rank\":500,\"mode\":\"spec4\"}"
)"
USER_ID="$(printf '%s' "$USER_RESPONSE" | json_get 'data["id"]')"

echo "Loading first Spec4 card for smoke user"
CARD_RESPONSE="$(curl -fsS "${API_URL}/api/v1/cards/next-spec4?user_id=${USER_ID}")"
printf '%s' "$CARD_RESPONSE" | json_get 'data["card_id"]' >/dev/null
printf '%s' "$CARD_RESPONSE" | json_get 'data["competency"]["code"]' >/dev/null
VALIDATION_STATUS="$(printf '%s' "$CARD_RESPONSE" | json_get 'data["content_context"]["validation_status"]')"
QUALITY_STATUS="$(printf '%s' "$CARD_RESPONSE" | json_get 'data["content_context"]["quality_status"]')"

if [[ "$VALIDATION_STATUS" != "valid" ]]; then
    echo "Smoke card failed content validation: ${VALIDATION_STATUS}"
    exit 1
fi

if [[ "$QUALITY_STATUS" != "approved" && "$QUALITY_STATUS" != "literary" ]]; then
    echo "Smoke card is not deliverable: ${QUALITY_STATUS}"
    exit 1
fi

echo "Smoke passed."
