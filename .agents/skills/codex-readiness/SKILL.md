---
name: "codex-readiness"
description: "Use when preparing or auditing the repository for strong Codex workflows, including AGENTS, skills, validation gates, and MCP setup documentation."
---

# Codex Readiness

## Goal

Keep the repository ready for repeatable Codex usage with clear governance, local skills, and explicit environment setup.

## Workflow

1. Verify `AGENTS.md` at the root and in critical subdirectories.
2. Verify official docs under `docs/` reflect the actual workflow.
3. Check whether repo-local skills cover repeated workflows.
4. Check whether validation gates exist locally or in CI.
5. Document recommended MCP setup without committing user-specific secrets.

## Rules

- Prefer documenting MCP setup over committing user-local MCP credentials or private config.
- Keep the official source of truth small and centralized.
- Do not recreate parallel governance systems.
