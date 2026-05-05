#!/bin/bash

set -euo pipefail

COMPOSE_CMD=(docker compose)
CONFIRM=0
BACKUP_FILE=""

usage() {
    echo "Usage: ./scripts/db_restore.sh --yes <backup-file>"
    echo
    echo "Restores a custom-format pg_dump into the local filltheword database."
    echo "This is destructive: existing objects are dropped when present."
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --yes)
            CONFIRM=1
            shift
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            if [[ -n "$BACKUP_FILE" ]]; then
                echo "Unexpected extra argument: $1"
                usage
                exit 1
            fi
            BACKUP_FILE="$1"
            shift
            ;;
    esac
done

if [[ "$CONFIRM" -ne 1 || -z "$BACKUP_FILE" ]]; then
    usage
    exit 1
fi

if [[ ! -f "$BACKUP_FILE" ]]; then
    echo "Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo "Docker is not running."
    exit 1
fi

echo "Checking database service..."
"${COMPOSE_CMD[@]}" exec -T db pg_isready -U ftw_user -d filltheword >/dev/null

echo "Restoring database from: ${BACKUP_FILE}"
"${COMPOSE_CMD[@]}" exec -T db pg_restore \
    -U ftw_user \
    -d filltheword \
    --clean \
    --if-exists \
    --no-owner \
    --no-acl < "$BACKUP_FILE"

echo "Restore complete."
