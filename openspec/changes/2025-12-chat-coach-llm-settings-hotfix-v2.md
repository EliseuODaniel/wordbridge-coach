# Change Proposal: Chat Coach - LLM Settings Hotfix v2

**Status:** 🚧 In Progress
**Created:** 2025-12-26
**Author:** User (via Claude)
**Scope:** Hotfix (LLM Settings modal, model switching)

---

## Problem Statement

**Current state:**
- Multi-service LLM infrastructure implemented (commit 8c00259)
- 3 llama.cpp services running: llm (8080), llm_chat (8081), llm_teacher (8082)
- Backend API endpoints working (verified via curl):
  - `GET /api/v1/llm-profiles` → 200 OK (3 profiles with service_url)
  - `GET /api/v1/users/me/llm-preferences?user_id=xxx` → 200 OK
  - All 3 services accessible from api container

**But user reports:**
1. ❌ "Failed to load LLM settings" error when opening ⚙️ modal
2. ❌ "Sem resposta ao trocar modelo" - chat stops working after model change
3. ❌ Settings not persisting or not being applied

**Hypothesis:**
- Frontend error handling or parsing issue (backend works via curl)
- Possible service_url routing problem (wrong host/port in config)
- Missing userId or wrong userId being passed
- WebSocket not reconnecting after preferences change

---

## Proposed Solution

### Phase 1: Reproduce Error (Manual)
1. Open `http://localhost:3007/?mode=chat` in browser
2. Open DevTools (Console + Network tabs)
3. Click ⚙️ button
4. Capture:
   - Network requests (URL, status, response body)
   - Console errors (red text)
   - Screenshots of modal state

### Phase 2: Fix "Failed to load LLM settings"
**Possible causes:**
- A. Frontend calling wrong endpoint URL
- B. Response parsing error (schema mismatch)
- C. userId undefined or invalid
- D. CORS error (unlikely since same-origin)

**Fix approach:**
- Add console.log to LLMSettingsPanel.tsx to debug
- Verify userId is being passed correctly
- Add error boundary component
- Ensure service_url is in LLMProfile interface

### Phase 3: Fix "sem resposta ao trocar modelo"
**Possible causes:**
- A. service_url using "localhost:8081" instead of "llm_chat:8081"
- B. WebSocket not reconnecting after preferences update
- C. LLM provider failing silently (strict=False but not logging)
- D. Model file not loaded in service

**Fix approach:**
- Verify service_url values (must be Docker service names, not localhost)
- Add fallback in chat.py if profile service fails
- Add health check before using profile
- Log which service_url is being used for chat vs teacher

### Phase 4: Validate Accessibility
**Tests:**
```bash
# From api container, verify all services reachable
docker compose exec api python -c "
import urllib.request
print('llm:', urllib.request.urlopen('http://llm:8080/health', timeout=2).read()[:100])
print('llm_chat:', urllib.request.urlopen('http://llm_chat:8081/health', timeout=2).read()[:100])
print('llm_teacher:', urllib.request.urlopen('http://llm_teacher:8082/health', timeout=2).read()[:100])
"
```

### Phase 5: Manual Validation
1. Open Chat Coach
2. Click ⚙️ button → modal opens (no error)
3. Select chat=phi-3-mini-4k-instruct, teacher=qwen2.5-3b-instruct
4. Click "Save Preferences" → success toast
5. Send "hello" → chat responds with Phi-3
6. Check logs → show routing to correct services
7. Teacher analysis appears with Qwen 3B

---

## Goals

1. ✅ Modal opens without error
2. ✅ Profiles and preferences load correctly
3. ✅ Save persists to database
4. ✅ Chat uses selected model (logs prove it)
5. ✅ Teacher uses selected model (logs prove it)
6. ✅ No regression in Spec4/Lingvist

---

## Acceptance Criteria

### CA1: Modal Opens and Loads

**Given** user opens Chat Coach at `http://localhost:3007/?mode=chat`
**When** clicking ⚙️ button
**Then** modal opens without error
**And** shows 2 dropdowns (Chat Model, Teacher Model)
**And** each dropdown has 3 options
**And** current selection matches user's saved preferences
**Validation:** Screenshot + Console clean (no red errors)

---

### CA2: Save Persists and Reapplies

**Given** modal is open
**When** selecting chat=phi-3-mini-4k-instruct, teacher=qwen2.5-3b-instruct
**And** clicking "Save Preferences"
**Then** green success toast appears
**And** preferences saved to database
**And** after page refresh (F5), dropdowns still show selected models
**Test:**
```bash
# Before save
curl -s "http://localhost:8000/api/v1/users/me/llm-preferences?user_id=XXX" | jq '.chat_model_profile'
# After save (should return phi-3-mini-4k-instruct)
```
**Validation:** Database query + browser test

---

### CA3: Chat Uses Selected Model

**Given** preferences saved with chat=phi-3-mini-4k-instruct
**When** user sends "hello" in chat
**Then** chat responds
**And** backend logs show:
```
[LLM_PROFILES] conv=..., user=... chat=phi-3-mini-4k-instruct, teacher=qwen2.5-3b-instruct
[CHAT_LLM] Starting stream with profile chat_provider.model=phi-3-mini-4k-instruct (base_url=http://llm_chat:8081)
```
**Validation:** Log inspection + actual response

---

### CA4: Teacher Uses Selected Model

**Given** preferences saved with teacher=qwen2.5-3b-instruct
**When** user sends message with grammar error
**Then** teacher analysis appears in panel
**And** backend logs show:
```
[TEACHER_ANALYSIS] Starting generation for conv=... with profile teacher_provider.model=qwen2.5-3b-instruct (base_url=http://llm_teacher:8082)
```
**Validation:** Log inspection + teacher panel appears

---

### CA5: Graceful Error Handling

**Given** user selects profile with offline service
**When** sending message
**Then** chat shows error toast: "Model X unavailable, using default"
**And** backend logs error with fallback reason
**And** chat continues with default model (not silent failure)
**Validation:** Log inspection + error toast visible

---

### CA6: Spec4/Lingvist No Regression

**Given** changes deployed
**When** opening Spec4 mode (`?mode=spec4`)
**And** answering cards
**Then** cards work normally
**And** TTS works
**And** no errors in console
**Validation:** Manual smoke test

---

## Implementation Plan

### Step 1: Reproduce Error (Manual)
- Open browser DevTools
- Try to open modal
- Capture all errors (Network + Console)
- Identify root cause

### Step 2: Fix Based on Root Cause
**If frontend error:**
- Fix TypeScript/interface mismatch
- Add proper error handling
- Verify userId propagation

**If backend routing error:**
- Fix service_url values in profiles.py
- Add health check before using profile
- Implement fallback in chat.py

**If WebSocket not reconnecting:**
- Add reload/refresh after preferences save
- Show "Reconnecting..." message
- Ensure new preferences used on reconnect

### Step 3: Add Logging
- In chat.py, log profile_id and service_url for chat and teacher
- Format: `[LLM_PROFILES] conv={conv_id}, user={user_id} chat={chat_profile}, teacher={teacher_profile}`

### Step 4: Test
- Manual browser test
- Log verification
- Spec4/Lingvist sanity check

### Step 5: Document
- Update OpenSpec proposal with evidence
- Archive proposal
- Update CHANGE_SUMMARY.md
- Create commit

---

## Known Issues

**Current blocker:** Cannot reproduce error via CLI (all curl tests pass)
- Need manual browser test with DevTools
- Need to see actual Network request/response
- Need to see Console errors

**Likely causes (in priority order):**
1. Frontend not passing userId correctly
2. service_url using "localhost" instead of Docker service names
3. WebSocket state not updating after preferences change
4. Silent LLM provider failure (no error shown to user)

---

## Dependencies

- Depends on: commit 8c00259 (multi-service infrastructure)
- Depends on: Docker compose with 3 llama.cpp services running
- Blocked by: Manual browser test to identify actual error

---

## Open Questions

1. **What is the exact error message in browser console?**
   - Need manual test to answer

2. **Is userId being passed correctly to LLMSettingsPanel?**
   - Need to check React state in browser DevTools

3. **Are the service_url values correct in production?**
   - They are "http://llm_chat:8081" etc in code
   - But frontend might be receiving "localhost" from somewhere

4. **Does WebSocket reconnect after preferences change?**
   - Need to verify network activity in DevTools

---

## Evidence

### Backend Tests (All ✅ Pass)

**llm-profiles endpoint:**
```bash
curl -s http://localhost:8000/api/v1/llm-profiles | jq '.profiles | length'
# Output: 3
```

**Preferences endpoint:**
```bash
curl -s "http://localhost:8000/api/v1/users/me/llm-preferences?user_id=30b8a6df-1cbb-4620-b13f-f3bdb5cf1fdf" | jq '.chat_model_profile'
# Output: "qwen2.5-7b-instruct"
```

**Service accessibility (from api container):**
```bash
docker compose exec api python -c "
import urllib.request
print('llm:', urllib.request.urlopen('http://llm:8080/health', timeout=2).read()[:100])
print('llm_chat:', urllib.request.urlopen('http://llm_chat:8081/health', timeout=2).read()[:100])
print('llm_teacher:', urllib.request.urlopen('http://llm_teacher:8082/health', timeout=2).read()[:100])
"
# Output:
# llm: b'{"status":"ok"}'
# llm_chat: b'{"status":"ok"}'
# llm_teacher: b'{"status":"ok"}'
```

### Frontend Bundle (✅ Verified)
```bash
docker compose exec frontend grep -r "LLMSettingsPanel" /usr/share/nginx/html/assets/
# Output: FOUND_IN_BUNDLE
```

**TBD:** Manual browser test results with actual error details

---

## Conclusion

Backend infrastructure is working correctly. The issue is in frontend runtime behavior or configuration. Next step is manual browser test to identify the exact error, then apply targeted fix.

**Estimated time:** 30-60 minutes (depending on root cause complexity)
