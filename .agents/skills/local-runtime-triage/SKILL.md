---
name: "local-runtime-triage"
description: "Use when bringing WordBridge Coach up locally, debugging Docker Compose/Vite/ports, or verifying that db, api, frontend, audio, and AI profiles match the intended runtime."
---

# Local Runtime Triage

## Goal

Bring the local app up predictably, diagnose runtime drift quickly, and leave the machine clean after testing.

## Workflow

1. Check `git status --short` first so runtime artifacts are not confused with source changes.
2. Inspect active ports before starting services: `8000`, `3007`, `5432`, `55432`, `8001`, `8010`, and `8080`.
3. Prefer the default app stack first: `db`, `api`, and `frontend`.
4. Use `WORDBRIDGE_DB_PORT=55432` when host port `5432` is already occupied.
5. Run migrations and seed after `api` is healthy when not using `scripts/quick_start.sh`.
6. Use profile `audio` only when TTS behavior is being tested.
7. Use profile `ai` only when Chat Coach local LLM or LanguageTool behavior is being tested.
8. Use `./scripts/smoke_local.sh` for the short default-runtime check whenever compose, Nginx, startup, or API/frontend contracts changed.
9. If the containerized frontend is blocked, use Vite as a temporary fallback and record that as runtime drift.
10. Verify behavior with `/health`, `/api/v1/users/`, and a browser smoke path before handing it to the user.
11. After testing, run `docker compose down --remove-orphans` and stop any Vite process that was started manually.

## Rules

- Keep default-runtime issues separate from optional `audio` and `ai` profile issues.
- Do not leave containers, dev servers, or occupied ports running unless the user is actively testing.
- Treat a button that appears to do nothing as both a frontend UX problem and a backend/runtime signal until proven otherwise.
- Prefer fixing the supported runtime path over documenting a workaround as if it were normal.
- Keep `scripts/init.sql` table-agnostic; extensions and permissions belong there, while schema and indexes belong in Alembic migrations.
- Keep heavy translation dependencies out of the base API runtime. Use `INSTALL_ARGOS=true` only when validating offline Argos translation.
- If a simple smoke test spends minutes building API dependencies, record it as platform debt before expanding the smoke scope.
