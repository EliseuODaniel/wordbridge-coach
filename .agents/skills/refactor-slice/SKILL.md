---
name: "refactor-slice"
description: "Use when planning or executing a refactor in small safe slices."
---

# Refactor Slice

## Goal

Break refactors into safe increments that preserve behavior and reduce risk.

## Workflow

1. Identify the current behavior to preserve.
2. Identify the coupling or complexity to reduce.
3. Define one slice with a clear boundary.
4. Update code.
5. Run validation for that slice.
6. Record architecture-impacting decisions in `docs/DECISIONS.md` when needed.

## Rules

- Do not mix cleanup, feature work, and architecture changes in one uncontrolled batch.
- Prefer slices that can be tested independently.
- Update `docs/ROADMAP.md` when priorities or sequence change.
