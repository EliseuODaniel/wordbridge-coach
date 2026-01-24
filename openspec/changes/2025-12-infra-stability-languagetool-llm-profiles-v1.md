# Infra Stability: LanguageTool Healthcheck + LLM VRAM Optimization

**Status**: Proposed
**Created**: 2025-12-26
**Author**: Claude Code
**Type**: Infrastructure

## Problem Statement

### A) LanguageTool Unhealthy
LanguageTool container shows as `unhealthy` in `docker compose ps` despite being functional. The healthcheck is failing, likely because it's calling an endpoint that returns 400 (missing parameters).

**Evidence Needed**:
- `docker compose ps` showing `unhealthy`
- `docker compose logs languagetool` showing 400 errors from healthcheck
- Current healthcheck configuration in `docker-compose.yml`

### B) VRAM Near Capacity
With 3 LLM services running (llm, llm_chat, llm_teacher), VRAM usage is at ~95% (7741MB / 8188MB). This creates:
- Risk of OOM errors
- Potential instability
- No headroom for peak usage

**Current Usage**:
- `llm` (qwen2.5-7b): ~5.4GB VRAM
- `llm_chat` (phi-3-mini): ~2.3GB VRAM
- `llm_teacher` (qwen2.5-3b): ~2.1GB VRAM
- **Total**: ~9.8GB needed, but only 8GB available

## Goals

1. **Fix LanguageTool healthcheck** - Container should show `healthy` when service is actually responsive
2. **Reduce VRAM usage** - Default stack should run with comfortable VRAM headroom
3. **Preserve functionality** - Chat Coach, Spec4, and Lingvist must continue working
4. **Optional fast chat** - Provide ability to run llm_chat when explicitly requested

## Proposed Solution

### 1. LanguageTool Healthcheck Fix
Change healthcheck from `/v2/check` (which requires payload) to `/v2/languages` (which returns 200 with available languages):

```yaml
healthcheck:
  test: ["CMD-SHELL", "curl -fsS http://localhost:8010/v2/languages || exit 1"]
  start_period: 60s
  interval: 15s
  timeout: 5s
  retries: 10
```

### 2. LLM Chat as Optional Service
Make `llm_chat` optional via Docker Compose profiles:

**Default behavior** (2 LLM services):
```bash
docker compose up -d
# Starts: llm (qwen2.5-7b) + llm_teacher (qwen2.5-3b)
# VRAM: ~7.5GB (leaves ~500MB headroom)
```

**With fast chat** (3 LLM services):
```bash
docker compose --profile fastchat up -d
# Also starts: llm_chat (phi-3-mini)
# VRAM: ~9.8GB (near capacity)
```

### 3. Optional: Reduce Teacher Context
If VRAM still tight, reduce `llm_teacher` context from 4096 to 2048 tokens:
- Saves ~1GB VRAM
- Still sufficient for teacher analysis

## Acceptance Criteria

### CA1: LanguageTool Healthy
```bash
docker compose ps | grep languagetool
# Expected: "Up (healthy)"
```

### CA2: LanguageTool Endpoint Responds
```bash
curl -i http://localhost:8010/v2/languages
# Expected: HTTP 200 with languages list
```

### CA3: Default Stack Uses 2 LLMs
```bash
docker compose up -d
docker compose ps | grep -E "llm|llm_chat|llm_teacher"
# Expected: llm (healthy), llm_teacher (healthy)
# Expected: llm_chat NOT running
```

### CA4: Fastchat Profile Adds Third LLM
```bash
docker compose --profile fastchat up -d
docker compose ps | grep llm_chat
# Expected: llm_chat (healthy)
```

### CA5: VRAM Headroom in Default Mode
```bash
docker compose exec llm nvidia-smi
# Expected: >= 500MB free VRAM
```

### CA6: App Functionality Preserved
```bash
# Chat Coach
curl -f http://localhost:8000/health
# Expected: 200 OK

# Spec4
curl -i "http://localhost:8000/api/v1/cards/next-spec4?user_id=DEMO_USER"
# Expected: 200 with card data

# Lingvist
curl -i "http://localhost:8000/api/v1/cards/next-lingvist?user_id=DEMO_USER"
# Expected: 200 with card data
```

## Implementation Plan

1. **Diagnostic** - Collect evidence of current issues
2. **Fix LanguageTool** - Update healthcheck in docker-compose.yml
3. **Make llm_chat Optional** - Add `profiles: ["fastchat"]`
4. **Validate** - Test all CAs
5. **Create Branch & PR** - Follow Gitflow

## Risks & Mitigations

### Risk: Breaking Chat Coach
**Mitigation**: Smoke test Chat Coach after changes

### Risk: Spec4/Lingvist Regression
**Mitigation**: Test card endpoints with existing user

### Risk: VRAM Still Too High
**Mitigation**: Reduce teacher context as fallback

## Evidence Collection (To Be Updated)

### Before Changes
- `docker compose ps`: [TBD]
- LanguageTool logs: [TBD]
- VRAM usage: [TBD]

### After Changes
- `docker compose ps`: [TBD]
- LanguageTool health: [TBD]
- VRAM usage (default): [TBD]
- VRAM usage (fastchat): [TBD]

## OpenSpec Checklist

- [ ] Proposal created
- [ ] Diagnostic evidence collected
- [ ] Changes implemented
- [ ] All CAs validated
- [ ] Change documented with evidence
- [ ] PR opened and merged
- [ ] Change archived
- [ ] CHANGE_SUMMARY.md updated
