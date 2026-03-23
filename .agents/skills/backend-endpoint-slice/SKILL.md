---
name: "backend-endpoint-slice"
description: "Use when refactoring or extending a FastAPI endpoint or backend service in a small safe slice with targeted pytest validation."
---

# Backend Endpoint Slice

## Goal

Refactor or extend backend behavior in small slices without breaking existing HTTP contracts or the validated test baseline.

## Workflow

1. Read the endpoint and the closest supporting service.
2. Identify the smallest extraction or contract-preserving change.
3. Keep domain rules explicit in helpers or services.
4. Run only the targeted backend tests needed for that slice.
5. If setup, architecture, or testing expectations changed, update `docs/`.

## Rules

- Do not parallelize pytest suites that share the same test database.
- Prefer extracting pure helpers before redesigning data flow.
- Preserve validated chat and Spec4 flows unless the task explicitly changes them.
