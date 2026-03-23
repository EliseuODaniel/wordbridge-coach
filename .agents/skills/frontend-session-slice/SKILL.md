---
name: "frontend-session-slice"
description: "Use when simplifying a large frontend session component such as StudySession, LingvistSession, or ChatCoachSession without changing user-facing behavior."
---

# Frontend Session Slice

## Goal

Reduce local coordination, duplicated side effects, and component weight in a session screen while preserving behavior.

## Workflow

1. Identify the repeated local responsibility: timers, audio, focus, transport state, or mode switching.
2. Extract the smallest helper or local callback set that reduces repetition.
3. Keep navigation decisions in `App.tsx` when possible.
4. Validate with `npm run lint` and `npm run build`.
5. Sync official docs only if behavior, setup, or architecture changed.

## Rules

- Prefer local helpers over premature shared abstractions.
- Preserve the current UX flow before optimizing structure.
- Treat session switching as shell behavior, not component-internal routing.
