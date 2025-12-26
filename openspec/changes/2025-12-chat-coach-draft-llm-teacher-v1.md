# Change Proposal: Chat Coach Draft - LLM Teacher + LT Fixes

**Status:** 🟡 Proposal
**Created:** 2025-12-26
**Author:** User (via Claude)
**Scope:** Chat Coach Draft Feedback Enhancement

---

## Problem Statement

The Chat Coach draft feedback system has several critical issues that reduce its effectiveness:

1. **LanguageTool False Negatives**
   - Obvious typos are not detected: "hi, how are ioy?" should flag "ioy" as spelling error
   - Suspected causes: wrong language code, pipeline overwrites, or filtering issues

2. **Poor Suggestions**
   - Suggestions are contextually irrelevant
   - Example: "I like to sleep." suggests "enjoy" (doesn't fit grammatically or contextually)
   - Need token-aware completion (prefix match + next-word prediction)

3. **Missing Teacher Feedback**
   - Right panel only shows grammar issues, no pedagogical guidance
   - No "teacher voice" explaining *why* something is wrong or how to improve
   - LLM is underutilized (could provide personalized coaching)

4. **GPU Not Confirmed**
   - Local LLM (llama.cpp) may be running CPU-only
   - 8GB VRAM available but not utilized
   - Need faster inference for real-time feedback

---

## Proposed Solution

### 1. Fix LanguageTool Pipeline (High Priority)

**Diagnosis First:**
- Create script to test LT directly with "hi, how are ioy?"
- Test WebSocket draft_update with same text
- Compare results to identify where issues are lost

**Fixes:**
- Ensure correct language code (en-US for English chat, not user preference)
- Prevent micro_eval heuristic from overwriting LT issues
- In `handle_user_message`, reuse cached draft feedback instead of sending "No issues"
- Add regression test for "ioy" case

### 2. Token-Aware Suggestions

**Backend Components:**

**a) WordCompletionService** (Prefix Match)
- Detect current token (text after last space/punctuation)
- If token.length >= 2 and is alpha:
  - Query WordFrequency/Word for prefix match on lemma/text
  - Return top 8 by rank

**b) NextWordService** (N-gram Prediction)
- Build bigram/trigram model from existing sentence bank:
  - Script: `api/scripts/build_next_word_model.py`
  - Output: `api/data/en_next_word_model.json`
- Use last 1-2 complete tokens to predict next word (top 8)

**c) Smart Routing**
- If user is mid-word: prioritize prefix completions
- If user just finished word or after punctuation: prioritize next-word
- Combine results into `suggested_next_words` (5-8 items)

### 3. Teacher Feedback via Local LLM (Idle, Cached)

**Design Principles:**
- **DO NOT** call LLM on every keystroke (too slow)
- Only call on:
  - `request_autocomplete` event (user idle)
  - Server-side idle detection in `draft_update`
- Throttle: max 1 request per 800-1200ms per conversation

**Prompt Strategy:**
```
You are an English teacher. Analyze this student draft: "{text}"

Return JSON:
{
  "teacher_feedback_bullets": [
    "Good use of present continuous!",
    "Remember: 'I' is always capitalized",
    "Try: 'How are you?' instead of 'How is you?'"
  ],
  "rewrite": "Hi, how are you?",
  "better_next_words": ["doing", "feeling", "going"]
}
```

**Robust Parsing:**
- Extract JSON from LLM response
- On parse failure: graceful degradation (show partial feedback or skip)
- Cache results per conversation_id + draft_hash

### 4. GPU + Better Model (8GB VRAM)

**Docker Configuration:**
- Use CUDA image: `ghcr.io/ggml-org/llama.cpp:server-cuda`
- Enable GPU: `gpus: all` + device reservations
- Command flags:
  - `--n-gpu-layers 999` (offload all layers to GPU)
  - `-c 4096` (context size)
  - `--parallel 2` (parallel processing)

**Model Selection:**
- **Preferred:** Qwen2.5-7B Instruct GGUF Q4_K_M (~4.7GB)
  - Good English understanding
  - Fast inference
  - Fits in 8GB VRAM
- **Alternative:** Llama 3.1 8B Instruct Q4 (~5GB)

**Download Script:**
- Update `scripts/download_model.sh`
- Auto-download and symlink to `llm_models/model.gguf`

**GPU Verification:**
- Check logs for "BLAS", "CUDA", "GPU", or "n_gpu_layers > 0"
- Benchmark: inference time should be <500ms for short prompts

### 5. Frontend Updates

**AnalysisPanel Enhancements:**
- Show issues with highlights (existing)
- Add "Teacher Feedback (LLM)" section:
  - Bullet points from teacher_feedback_bullets
  - Styled differently from grammar issues (e.g., light blue background)
- Improve suggestion chips:
  - Combine suggested_next_words + better_next_words
  - Group by type (completion vs next-word)
  - Visual distinction

**ChatCoachSession Behavior:**
- Ensure draft feedback persists after sending message
- Do not clear panel on user_message
- Update teacher feedback when available (async)

---

## Acceptance Criteria

### CA1: LT Detects "ioy" Typo
**Given** user types "hi, how are ioy?" (without sending)
**When** draft_update event is sent
**Then** draft_feedback includes:
- Issue with category="spelling" or "typo"
- highlight_spans covering "ioy" (e.g., start=10, end=13)
- suggestions containing "you" or "boy"

### CA2: Feedback Persists After Send
**Given** user has draft with "hi, how are ioy?"
**When** user presses Enter (sends message)
**Then** right panel continues showing:
- Same grammar issues (not cleared)
- Same highlight positions
- Same suggestions

### CA3: Contextually Relevant Suggestions
**Given** user types "I like to sleep."
**When** draft_update event is sent
**Then** suggested_next_words includes:
- At least 3 plausible options: because/so/and/when/in/every
- Does NOT include "enjoy" (wrong context)

### CA4: Teacher Feedback Appears
**Given** user types a sentence and stops (idle ~800ms)
**When** server detects idle
**Then** draft_feedback includes:
- `teacher_feedback_bullets`: array with 2-4 items
- Each bullet is concise (max 100 chars)
- Bullets are helpful and accurate

### CA5: GPU Confirmed
**Given** llama.cpp container is running
**When** checking logs with `docker compose logs llm | grep -iE "cuda|gpu|offload|n_gpu_layers"`
**Then** output shows:
- "BLAS = 1" or "CUDA" or "GPU"
- "n_gpu_layers > 0" (e.g., "n_gpu_layers = 28")
- No "CPU only" messages

---

## Implementation Plan

### Phase 1: Diagnose + Fix LT (Critical Path)
1. Create diagnostic script for LT
2. Test "hi, how are ioy?" via direct LT API
3. Test via WebSocket
4. Fix language code + overwrite issues
5. Add regression test
6. Validate CA1, CA2

### Phase 2: Token-Aware Suggestions
1. Create WordCompletionService
2. Build next-word model script
3. Create NextWordService
4. Integrate into draft_update
5. Validate CA3

### Phase 3: Teacher LLM (Idle)
1. Design teacher prompt (JSON output)
2. Add idle detection to draft_update
3. Implement LLM call with throttle
4. Parse JSON + graceful degradation
5. Integrate into DraftFeedbackOut
6. Validate CA4

### Phase 4: GPU + Model
1. Update docker-compose.yml for CUDA
2. Download Qwen2.5-7B Q4_K_M model
3. Configure llama.cpp with GPU offload
4. Verify GPU usage in logs
5. Validate CA5

### Phase 5: Frontend
1. Update AnalysisPanel for teacher feedback
2. Improve suggestion chips display
3. Ensure feedback persistence
4. Full E2E validation

---

## Non-Goals

- Real-time streaming LLM responses (too slow for typing)
- Multi-language support (English only for now)
- Advanced error recovery (graceful degradation is enough)
- Spec4/Lingvist integration changes (this is chat-only)

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| LT still has false negatives | Medium | Add heuristic fallback for common patterns |
| LLM JSON parse fails frequently | High | Strong validation + regex extraction as backup |
| GPU offload fails (OOM) | Medium | Fallback to CPU automatically |
| Teacher feedback too slow | Medium | Background thread + cache + optional display |

---

## Success Metrics

- **Accuracy:** "hi, how are ioy?" detection rate: 100%
- **Suggestion Quality:** At least 70% of suggestions are contextually relevant
- **Performance:** LT response <200ms, Teacher LLM <800ms
- **GPU Usage:** >80% model layers on GPU
- **User Experience:** No UI freezes, smooth typing

---

## Open Questions

1. Should teacher feedback be editable by user? (Decision: No, read-only for v1)
2. Cache duration for teacher feedback? (Decision: Per conversation_id + draft_hash, infinite until new draft)
3. Fallback if LLM is down? (Decision: Hide teacher feedback section, still show LT issues)

---

## Related Changes

- Depends on: `openspec/changes/2025-12-chat-coach-realtime-draft-coach-v1.md` (LanguageTool integration)
- Supersedes: N/A (new feature)
- Blocked by: N/A

---

## References

- LanguageTool API: https://languagetool.org/http-api/
- Qwen2.5 Model: https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF
- llama.cpp CUDA: https://github.com/ggerganov/llama.cpp/tree/master/examples/server
