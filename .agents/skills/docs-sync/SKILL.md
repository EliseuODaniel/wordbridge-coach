---
name: "docs-sync"
description: "Use when code, setup, or architecture changed and the official docs may be stale."
---

# Docs Sync

## Goal

Keep `README.md`, `AGENTS.md`, and `docs/` aligned with the real repository state.

## Workflow

1. Read only the docs related to the touched area.
2. Inspect the code, scripts, and config that define the real behavior.
3. List mismatches between docs and code.
4. Update the smallest official doc set needed.
5. Validate or explicitly mark runtime claims such as compose profiles, ports, healthchecks, and startup order.
6. Prefer consolidation over adding new one-off markdown files.

## Rules

- Treat `AGENTS.md` and `docs/` as the official documentation surface.
- Delete or fold stale snapshot docs when they compete with official docs.
- Do not recreate OpenSpec-style parallel documentation.
- Do not document a workaround as the normal path when the supported runtime can be fixed.
