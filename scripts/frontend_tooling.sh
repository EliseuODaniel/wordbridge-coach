#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./scripts/frontend_tooling.sh <install|lint|typecheck|build|check> [extra args]

Commands:
  install     Run npm ci in the pinned Docker Node environment
  lint        Run npm run lint
  typecheck   Run npm run typecheck
  build       Run npm run build
  check       Run npm ci, lint, typecheck and build in sequence

This script is the supported local path for frontend checks in hybrid
Windows/WSL environments. It keeps npm cache and node_modules in .cache/
to avoid cross-runtime corruption of frontend/node_modules.
EOF
}

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required to run frontend_tooling.sh" >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"
CACHE_ROOT="$ROOT_DIR/.cache/frontend-tooling"
NODE_MODULES_DIR="$CACHE_ROOT/node_modules"
NPM_CACHE_DIR="$CACHE_ROOT/npm-cache"
IMAGE="${FRONTEND_TOOLING_IMAGE:-node:20-bookworm}"

mkdir -p "$NODE_MODULES_DIR" "$NPM_CACHE_DIR"

quote_args() {
  if [[ $# -eq 0 ]]; then
    return
  fi

  printf '%q ' "$@"
}

run_in_container() {
  local command="$1"

  docker run --rm \
    -u "$(id -u):$(id -g)" \
    -e npm_config_cache=/tmp/npm-cache \
    -v "$FRONTEND_DIR:/app" \
    -v "$NODE_MODULES_DIR:/app/node_modules" \
    -v "$NPM_CACHE_DIR:/tmp/npm-cache" \
    -w /app \
    "$IMAGE" \
    bash -lc "$command"
}

command="$1"
shift || true
extra_args="$(quote_args "$@")"

case "$command" in
  install)
    run_in_container "npm ci"
    ;;
  lint)
    run_in_container "npm run lint${extra_args:+ -- $extra_args}"
    ;;
  typecheck)
    run_in_container "npm run typecheck"
    ;;
  build)
    run_in_container "npm run build"
    ;;
  check)
    run_in_container "npm ci && npm run lint && npm run typecheck && npm run build"
    ;;
  *)
    usage
    exit 1
    ;;
esac
