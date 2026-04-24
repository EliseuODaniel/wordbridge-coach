---
name: "git-hygiene"
description: "Use when preparing, reviewing, or publishing repo changes and you want safe Git habits: inspect status first, isolate scope, stage intentionally, protect user work, and keep local and remote history tidy."
---

# Git Hygiene

## Goal

Keep Git history understandable and safe without losing user work or mixing unrelated changes.

## Workflow

1. Inspect `git status` and current branch before editing, staging, or syncing.
2. Separate the intended change from unrelated worktree changes and avoid touching files outside the task.
3. Review the diff before staging so the commit matches one coherent purpose.
4. Stage intentionally and prefer one logical commit per change slice when practical.
5. Push only after the relevant validation has run, or clearly state what was not validated.
6. When syncing with remotes, prefer non-destructive operations and verify branch state before deleting or cleaning up refs.
7. After publishing or cleaning up branches, confirm local `HEAD`, upstream `HEAD`, and `git status --short`.
8. When runtime testing starts containers or dev servers, clean those processes separately from Git cleanup.

## Rules

- Never discard or rewrite user changes without explicit approval.
- Do not mix unrelated fixes, formatting noise, and feature work in the same commit.
- Prefer clear imperative commit messages that describe the change, not the process.
- Before deleting branches or cleaning refs, confirm that the needed history is already preserved on `main`, on a remote, or in an explicit backup.
- Keep generated runtime artifacts out of commits unless they are intentional source files.
