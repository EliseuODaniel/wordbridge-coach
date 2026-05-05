#!/bin/bash

set -euo pipefail

BACKUP_DIR="${WORDBRIDGE_BACKUP_DIR:-backups}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
OUTPUT_FILE="${1:-${BACKUP_DIR}/wordbridge-${TIMESTAMP}.dump}"
COMPOSE_CMD=(docker compose)

usage() {
    echo "Usage: ./scripts/db_backup.sh [output-file]"
    echo
    echo "Environment overrides:"
    echo "  WORDBRIDGE_BACKUP_DIR  Backup directory when output-file is omitted (default: backups)"
}

if [[ "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi

if ! docker info >/dev/null 2>&1; then
    echo "Docker is not running."
    exit 1
fi

mkdir -p "$(dirname "$OUTPUT_FILE")"

echo "Checking database service..."
"${COMPOSE_CMD[@]}" exec -T db pg_isready -U ftw_user -d filltheword >/dev/null

echo "Writing database backup: ${OUTPUT_FILE}"
"${COMPOSE_CMD[@]}" exec -T db pg_dump -U ftw_user -d filltheword --format=custom --no-owner --no-acl > "$OUTPUT_FILE"

echo "Backup complete."
ls -lh "$OUTPUT_FILE"
