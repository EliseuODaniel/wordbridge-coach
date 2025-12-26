# Change Proposal: Chat Coach - LLM Profiles Hotfix

**Status:** 🚧 In Progress
**Created:** 2025-12-26
**Author:** User (via Claude)
**Scope:** Hotfix (Frontend rebuild + multi-service models)

---

## Problem Statement

**Current state:**
- LLM Profiles feature was implemented (commit 74509fc)
- Backend endpoints work: `/api/v1/llm-profiles` returns 3 profiles, `/api/v1/users/me/llm-preferences` persists data
- Frontend code exists: `LLMSettingsPanel.tsx`, `ChatCoachSession.tsx` with ⚙️ button
- **BUT**: Frontend Docker bundle is stale (5 hours old, from before the commit)
- **Result**: Users see NO ⚙️ button, NO dropdowns, CANNOT select models

**Root causes identified:**
1. Frontend Docker container was NOT rebuilt after code changes
2. Bundle `index-CvZmj2BR.js` does NOT contain `LLMSettingsPanel` component
3. Only ONE model file exists (Qwen 7B), others are referenced but not downloaded
4. Single llama.cpp service - no separation of chat vs teacher models

**Impact:**
- Feature completely invisible to users
- Cannot test model selection
- Cannot validate A/B benchmarks
- Production release would be broken

---

## Proposed Solution

### Overview

This hotfix will:
1. **Rebuild frontend Docker** with latest code (⚙️ button, dropdowns)
2. **Download 2 additional models** (Qwen 3B, Llama 8B) via scripts
3. **Create 2 llama.cpp services** (llm_chat, llm_teacher) for real multi-model selection
4. **Validate end-to-end** that model selection works
5. **Ensure no regressions** in Spec4/Lingvist modes

### Architecture Changes

#### 1. Frontend Rebuild (Immediate fix)

```bash
docker compose build frontend --no-cache
docker compose up -d frontend
```

**Expected result:**
- New bundle contains `LLMSettingsPanel` component
- ⚙️ button visible in Chat Coach header
- Dropdowns list 3 profiles (Qwen 7B, Qwen 3B, Llama 8B)

#### 2. Model Download Scripts

Create automated download scripts:

**`scripts/download_qwen25_3b_q4km.sh`**:
```bash
#!/usr/bin/env bash
wget -O llm_models/qwen2.5-3b-instruct-q4_k_m.gguf \
  "https://huggingface.co/lmstudio-community/Qwen2.5-3B-Instruct-GGUF/resolve/main/Qwen2.5-3B-Instruct-Q4_K_M.gguf"
```

**`scripts/download_llama31_8b_q4km.sh`**:
```bash
#!/usr/bin/env bash
wget -O llm_models/llama-3.1-8b-instruct-q4_k_m.gguf \
  "https://huggingface.co/lmstudio-community/Llama-3.1-8B-Instruct-GGUF/resolve/main/Llama-3.1-8B-Instruct-Q4_K_M.gguf"
```

**Model sizes:**
- Qwen 2.5 3B Q4_K_M: ~1.8GB (2.1GB VRAM)
- Llama 3.1 8B Q4_K_M: ~4.7GB (5.7GB VRAM)

#### 3. Multi-Service Docker Compose

Add 2 new llama.cpp services to `docker-compose.yml`:

```yaml
services:
  # Existing llm service (keep for backward compatibility)
  llm:
    image: ghcr.io/ggml-org/llama.cpp:server-cuda
    # ... existing config ...

  # NEW: Dedicated chat model (larger, slower, smarter)
  llm_chat:
    image: ghcr.io/ggml-org/llama.cpp:server-cuda
    container_name: filltheword-llm-chat
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    volumes:
      - ./llm_models:/models
    command: >
      -m /models/llama-3.1-8b-instruct-q4_k_m.gguf
      -c 4096
      --port 8081
      --host 0.0.0.0
      --metrics
      --nbthread 8
    ports:
      - "8081:8081"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8081/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # NEW: Dedicated teacher model (smaller, faster, JSON-focused)
  llm_teacher:
    image: ghcr.io/ggml-org/llama.cpp:server-cuda
    container_name: filltheword-llm-teacher
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    volumes:
      - ./llm_models:/models
    command: >
      -m /models/qwen2.5-3b-instruct-q4_k_m.gguf
      -c 2048
      --port 8082
      --host 0.0.0.0
      --metrics
      --nbthread 8
    ports:
      - "8082:8082"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8082/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

#### 4. Backend Profile Updates

Update `api/app/llm/profiles.py` to point to different services:

```python
from pydantic_settings import BaseSettings

class LLMSettings(BaseSettings):
    chat_model_base_url: str = "http://llm_chat:8081"
    teacher_model_base_url: str = "http://llm_teacher:8082"
    fallback_base_url: str = "http://llm:8080"

    class Config:
        env_file = ".env"

llm_settings = LLMSettings()

def get_llm_provider_for_profile(profile_id: str, use_case: str = "chat") -> LLMProvider:
    """Get LLM provider for specific profile and use case.

    Args:
        profile_id: Profile ID from LLM_PROFILES
        use_case: "chat" or "teacher" - determines which service to use
    """
    profile = get_profile(profile_id)

    # Select base URL based on use case
    if use_case == "chat":
        base_url = llm_settings.chat_model_base_url
    elif use_case == "teacher":
        base_url = llm_settings.teacher_model_base_url
    else:
        base_url = llm_settings.fallback_base_url

    return LlamaCppLLMProvider(
        base_url=base_url,
        model=profile.model,
        timeout=120.0,
        strict=False
    )
```

**Important**: All profiles share the SAME service URLs per use case (chat uses llm_chat, teacher uses llm_teacher), but the model path differs. Wait - this won't work with llama.cpp architecture since it loads one model per service.

**Revised approach**:
- Each llama.cpp service loads ONE model file
- Profiles should map to specific services
- Chat profiles map to llm_chat service (Llama 8B for quality)
- Teacher profiles map to llm_teacher service (Qwen 3B for speed)

Actually, let me reconsider. The user wants 2+ models working. Options:

**Option A**: 2 services, each with 1 model (simple, fits in 8GB VRAM)
- llm_chat: Llama 8B (5.7GB VRAM)
- llm_teacher: Qwen 3B (2.1GB VRAM)
- Total: 7.8GB VRAM (fits!)
- Profile selection just switches which service you use

**Option B**: 3 services for 3 models (might OOM on 8GB)
- llm_qwen7b: 5.4GB
- llm_qwen3b: 2.1GB
- llm_llama8b: 5.7GB
- Can't run all 3 simultaneously (need 13GB VRAM)

**Decision**: Option A is the only viable one for 8GB VRAM. We'll:
1. Keep existing llm service as-is (Qwen 7B) for backward compatibility
2. Add llm_chat (Llama 8B) for high-quality chat
3. Add llm_teacher (Qwen 3B) for fast teacher analysis
4. Update profiles to map to appropriate services

---

## Goals

1. ✅ **Frontend rebuilt**: New bundle contains LLMSettingsPanel, ⚙️ button visible
2. ✅ **Models downloaded**: 2 additional GGUF files in llm_models/
3. ✅ **Services running**: 3 llama.cpp containers (llm, llm_chat, llm_teacher) healthy
4. ✅ **Model selection works**: User can select chat=Llama8B, teacher=Qwen3B via UI
5. ✅ **Logs prove routing**: Backend logs show "chat=Llama8B, teacher=Qwen3B"
6. ✅ **No regressions**: Spec4/Lingvist modes work normally

---

## Non-Goals

- ❌ Dynamic model hot-swapping without container restart
- ❌ Model fine-tuning
- ❌ Cloud provider integration
- ❌ Per-conversation model selection (user-level only)
- ❌ Automatic model download on-demand (manual scripts only)

---

## Contracts

### Contract 1: Frontend Bundle Contains New Code

**Given** frontend Docker container is rebuilt
**When** checking bundle for `LLMSettingsPanel` string
**Then** component is found in `index-*.js` file
**And** opening `http://localhost:3007/?mode=chat` shows ⚙️ button

**Rationale**: Verify build succeeded.

---

### Contract 2: Model Files Downloaded

**Given** download scripts executed
**When** listing `llm_models/` directory
**Then** 3 GGUF files exist:
- `model.gguf` (Qwen 7B, existing)
- `qwen2.5-3b-instruct-q4_k_m.gguf` (~1.8GB)
- `llama-3.1-8b-instruct-q4_k_m.gguf` (~4.7GB)

**Rationale**: Models must be present before services start.

---

### Contract 3: Services Healthy with CUDA

**Given** docker compose up -d
**When** running `docker compose ps`
**Then** llm_chat and llm_teacher show "healthy" status
**And** `docker compose logs llm_chat | grep -i cuda` shows CUDA enabled
**And** `nvidia-smi` shows VRAM usage < 8GB

**Rationale**: Services must load models with GPU acceleration without OOM.

---

### Contract 4: UI Selection Works End-to-End

**Given** user opens Chat Coach at `http://localhost:3007/?mode=chat`
**When** clicking ⚙️ button
**Then** modal opens with 2 dropdowns
**And** each dropdown shows 3 model options
**When** selecting chat=Llama8B and teacher=Qwen3B
**And** clicking "Save Preferences"
**Then** green success toast appears
**And** sending message uses selected models (logs prove it)

**Rationale**: Full user flow works.

---

### Contract 5: Spec4/Lingvist No Regression

**Given** changes deployed
**When** opening Spec4 mode (`?mode=spec4`)
**And** opening Lingvist mode (`?mode=lingvist`)
**Then** both modes work normally
**And** no errors in console/logs
**And** TTS plays correctly

**Rationale**: Isolated to Chat Coach mode.

---

## Acceptance Criteria

### CA1: Frontend Shows ⚙️ Button and Dropdowns

**Status:** ⏳ Pending
**Given** user opens `http://localhost:3007/?mode=chat`
**When** page loads
**Then** gear icon ⚙️ appears in header (right side)
**And** clicking it opens modal
**And** modal shows "Modelo do Chat" and "Modelo do Professor" dropdowns
**And** each dropdown has 3 options
**Validation:** Screenshot + manual inspection.

---

### CA2: Backend Accepts User ID (Not /me)

**Status:** ⏳ Pending
**Given** frontend calls API
**When** request is `GET /api/v1/users/me/llm-preferences?user_id=xxx`
**Then** backend returns 200 (not 401/403)
**And** returns user's current preferences
**Test Command:**
```bash
curl -s "http://localhost:8000/api/v1/users/me/llm-preferences?user_id=30b8a6df-1cbb-4620-b13f-f3bdb5cf1fdf" | jq '.chat_model_profile'
# Expected: "qwen2.5-7b-instruct"
```

**Rationale:** Current implementation already works - this is sanity check.

---

### CA3: Models Downloaded and Services Running

**Status:** ⏳ Pending
**Given** scripts executed and docker compose up
**When** checking system
**Then**:
```bash
# Model files exist
ls -lh llm_models/*.gguf
# Expected: 3 files, ~10GB total

# Services healthy
docker compose ps | grep -E "llm_chat|llm_teacher"
# Expected: both "Up X hours (healthy)"

# CUDA enabled
docker compose logs llm_chat | grep -i "BLAS"
# Expected: "BLAS = 1", "CUDA detected"
```
**Validation:** Commands pass.

---

### CA4: Chat Uses Llama 8B, Teacher Uses Qwen 3B

**Status:** ⏳ Pending
**Given** user preferences: chat=llama-3.1-8b-instruct, teacher=qwen2.5-3b-instruct
**When** user sends message "I enjoyed to sleep"
**Then** backend logs show:
```
[LLM_PROFILES] conv=..., user=... chat=llama-3.1-8b-instruct, teacher=qwen2.5-3b-instruct
[CHAT_LLM] Starting stream with profile chat_provider.model=llama-3.1-8b-instruct (base_url=http://llm_chat:8081)
[TEACHER_ANALYSIS] Starting generation for conv=... with profile teacher_provider.model=qwen2.5-3b-instruct (base_url=http://llm_teacher:8082)
```
**Validation:** Log inspection + actual response generation.

---

### CA5: VRAM Usage Under 8GB

**Status:** ⏳ Pending
**Given** both llm_chat and llm_teacher services running
**When** running `nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits`
**Then** output is < 8000 (MB)
**Reason:** Llama 8B (5.7GB) + Qwen 3B (2.1GB) = 7.8GB max (fits!)
**Validation:** Command output.

---

### CA6: Spec4/Lingvist No Regression

**Status:** ⏳ Pending
**Given** changes deployed
**When** opening `http://localhost:3007/?mode=spec4`
**And** answering cards normally
**Then** no errors in console
**And** TTS works
**And** Lingvist mode also works
**Validation:** Manual smoke test.

---

## Implementation Plan

### Phase 1: Frontend Rebuild (Immediate)
1. Run `docker compose build frontend --no-cache`
2. Run `docker compose up -d frontend`
3. Verify bundle contains new code (grep for LLMSettingsPanel)
4. Test ⚙️ button appears in browser

### Phase 2: Model Downloads
1. Create `scripts/download_qwen25_3b_q4km.sh`
2. Create `scripts/download_llama31_8b_q4km.sh`
3. Make scripts executable (`chmod +x`)
4. Run Qwen 3B download (~1.8GB, ~5 min on fast connection)
5. Run Llama 8B download (~4.7GB, ~10 min)
6. Verify all 3 GGUF files exist with `ls -lh`

### Phase 3: Multi-Service Setup
1. Update `docker-compose.yml`:
   - Add llm_chat service (Llama 8B, port 8081)
   - Add llm_teacher service (Qwen 3B, port 8082)
2. Run `docker compose up -d llm_chat llm_teacher`
3. Watch logs: `docker compose logs -f llm_chat llm_teacher`
4. Verify health checks pass
5. Verify CUDA with `nvidia-smi`

### Phase 4: Backend Profile Routing
1. Update `api/app/llm/profiles.py`:
   - Add `service_name` field to LLMProfile
   - Map profiles to specific services (chat -> llm_chat, teacher -> llm_teacher)
2. Update `api/app/llm/factory.py`:
   - Modify `get_llm_provider_for_profile()` to read service_name
   - Route to correct base URL based on service
3. Update `api/app/api/api_v1/endpoints/chat.py`:
   - Pass service context to provider factory
4. Test with curl

### Phase 5: End-to-End Validation
1. Open Chat Coach in browser
2. Click ⚙️ button
3. Select chat=Llama 8B, teacher=Qwen 3B
4. Save preferences
5. Send message "I enjoyed to sleep"
6. Check logs for correct routing
7. Verify VRAM usage
8. Test Spec4/Lingvist modes

### Phase 6: Archive + PR
1. Update this change proposal with evidence (screenshots, logs)
2. Move to `openspec/changes/archived/`
3. Update `openspec/CHANGE_SUMMARY.md`
4. Commit with detailed message
5. Push to remote

---

## Success Metrics

- ✅ Frontend bundle rebuilt and ⚙️ button visible
- ✅ 3 model files downloaded (10GB total)
- ✅ 3 llama.cpp services healthy (llm, llm_chat, llm_teacher)
- ✅ VRAM usage < 8GB
- ✅ Chat and teacher use DIFFERENT models (logs prove it)
- ✅ Spec4/Lingvist modes work normally
- ✅ User can select models via UI and changes persist

---

## Risks & Mitigations

**Risk**: Model downloads take 15+ minutes, fail due to network
**Mitigation**: Use `wget -c` for resume capability, show progress, allow manual download if script fails

**Risk**: VRAM OOM when running 2 services simultaneously
**Mitigation**: Carefully calculated (5.7GB + 2.1GB = 7.8GB < 8GB). If still OOMs, reduce context window to 1024 on teacher.

**Risk**: Frontend rebuild fails due to npm install issues
**Mitigation**: Dockerfile uses `npm ci --only=production`, rebuild is isolated. Can rollback to previous image if needed.

**Risk**: Backend profile routing breaks existing chat
**Mitigation**: Keep existing llm service untouched, add new services incrementally, test each before next.

**Risk**: .gitignore doesn't cover GGUF files, user commits them
**Mitigation**: Explicitly verify `.gitignore` has `*.gguf` before downloads.

---

## Dependencies

- Depends on: Previous implementation (commit 74509fc)
- Depends on: CUDA GPU with 8GB+ VRAM
- Depends on: Stable internet connection for downloads
- Blocked by: None (ready to implement)

---

## Open Questions

1. **Should we expose service URLs in profile metadata?**
   - Recommendation: Yes, add `service_url` field to LLMProfile
   - Allows flexible routing without hardcoding in factory

2. **What happens if user selects profile that doesn't match the service?**
   - Example: Select Qwen 7B profile, but it's mapped to llm_chat service (which loads Llama 8B)
   - **This is a critical architectural issue!**

   **Resolution**: Profiles must match the loaded model per service:
   - llm_chat service loads Llama 8B → Only llama-3.1-8b-instruct profile works
   - llm_teacher service loads Qwen 3B → Only qwen2.5-3b-instruct profile works
   - llm service loads Qwen 7B → Only qwen2.5-7b-instruct profile works

   **Therefore**: Each profile is tied to ONE specific service. User selects profile, we route to that profile's service.

   **Revised architecture**:
   ```python
   LLM_PROFILES = {
       "qwen2.5-7b-instruct": {
           "service_url": "http://llm:8080",  # Existing service
           "model_file": "qwen2.5-7b-instruct-q4_k_m.gguf"
       },
       "qwen2.5-3b-instruct": {
           "service_url": "http://llm_teacher:8082",  # New service
           "model_file": "qwen2.5-3b-instruct-q4_k_m.gguf"
       },
       "llama-3.1-8b-instruct": {
           "service_url": "http://llm_chat:8081",  # New service
           "model_file": "llama-3.1-8b-instruct-q4_k_m.gguf"
       }
   }
   ```

3. **Should chat and teacher be able to use the SAME profile?**
   - Yes, they can both use Qwen 7B (default)
   - But they can ALSO use different profiles (the whole point!)
   - Implementation: Load `chat_profile_id` and `teacher_profile_id` separately, create 2 providers

---

## Evidence

### Before Fix

**Frontend bundle check:**
```bash
docker compose exec frontend grep -r "LLMSettingsPanel" /usr/share/nginx/html/assets/
# Output: (empty - NOT FOUND)
```

**Browser test:**
- Opening `http://localhost:3007/?mode=chat`
- No ⚙️ button visible
- F12 Console: No errors (code just not present)

**Backend test (working):**
```bash
curl -s http://localhost:8000/api/v1/llm-profiles | jq '.profiles | length'
# Output: 3
```

### After Fix

[TBE: Evidence will be added during implementation]

---

## Conclusion

This hotfix will make the LLM Profiles feature **actually visible and functional** to users. The core issue is a stale frontend Docker build - once rebuilt, combined with downloaded models and multi-service setup, users will be able to select different models for Chat vs Teacher.

**Critical path:**
1. Rebuild frontend (5 min) ✅ Immediate fix for visibility
2. Download models (15 min) ⏳ Required for functionality
3. Start services (2 min) ⏳ Required for multi-model routing
4. Validate (5 min) ⏳ Confirm end-to-end flow

Total estimated time: ~30 minutes.
