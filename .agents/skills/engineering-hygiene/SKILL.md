---
name: "engineering-hygiene"
description: "Use when making code changes in any layer and you want a compact workflow for software engineering hygiene: small scope, explicit contracts, right-sized validation, and docs kept in sync."
---

# Engineering Hygiene

## Goal

Keep changes small, understandable, validated, and aligned with the repository's official docs.

## Workflow

1. Read the closest `AGENTS.md`, the affected code, and only the official docs needed for the change.
2. Identify the observable behavior, contract, or invariant that must remain true.
3. Prefer the smallest useful slice instead of mixing refactor, feature work, cleanup, and setup changes.
4. Update tests, scripts, types, or docs when they are part of the same behavior surface.
5. Run the smallest validation set that meaningfully covers the touched area.
6. Record architectural or workflow-impacting changes in `docs/DECISIONS.md`, `docs/ROADMAP.md`, or `docs/CODEX_SETUP.md` when needed.

## Rules

- Do not leave hidden behavior changes without matching docs or validation.
- Prefer contract-preserving extractions before broader redesigns.
- Keep naming, config, and user-facing text consistent across backend, frontend, scripts, and docs.
- When a shortcut is taken, call out the remaining risk explicitly in the close-out.
