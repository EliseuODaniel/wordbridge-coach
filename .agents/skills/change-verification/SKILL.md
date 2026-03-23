---
name: "change-verification"
description: "Use after code changes to run the smallest reliable validation set for the affected area."
---

# Change Verification

## Goal

Run right-sized validation after a change and report what was checked and what was not.

## Workflow

1. Identify touched areas: backend, frontend, infra, e2e.
2. Pick the smallest useful command set.
3. Run checks.
4. Summarize pass/fail and remaining risk.

## Default checks

- Backend: `cd api && pytest`
- Frontend: `cd frontend && npm run lint && npm run build`
- E2E: `cd tests/e2e && npm test`

## Rules

- Prefer targeted checks when the scope is narrow.
- Escalate to broader checks when architecture or shared contracts changed.
- If a check is skipped, say why.
