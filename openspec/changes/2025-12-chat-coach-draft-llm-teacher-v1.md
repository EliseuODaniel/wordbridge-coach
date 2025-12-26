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

### CRITICAL REQUIREMENT: Chat vs Teacher Separation

**UX Principle:**
- **Left column (Chat)**: Natural conversation only, NO meta-commentary, NO "Please note..." blocks
- **Right panel (Analysis)**:
  - Existing: LT issues, highlights, suggestions
  - **NEW**: "Professor (LLM)" section with pedagogical analysis

**Technical Requirements:**
1. Teacher analysis MUST NEVER appear as a chat message
2. Teacher analysis delivered via separate WebSocket event: `teacher_analysis`
3. Teacher analysis persisted in `ChatMessage.metadata_json` (key: `teacher_analysis`), NOT in `content`
4. Chat reply uses strict "conversation only" prompt
5. Layout: No global scroll; only message list has internal scrollbar
6. Auto-scroll: New messages scroll to bottom UNLESS user manually scrolled up

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

### CA1: LT Detects "ioy" Typo (COMPLETED ✅)
**Status:** Validated - LT correctly detects "ioy" as spelling error with highlight at position 12-15

### CA2: Feedback Persists After Send
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

### CA6: Chat Reply Natural (No Meta-Commentary)
**Given** user sends "I enjoyed to sleep"
**When** assistant responds
**Then** chat message contains ONLY natural conversation:
- No "Please note that..." blocks
- No meta-commentary about grammar
- No explanations or corrections
- Example valid reply: "That's great! Sleep is important for health."

### CA7: Teacher Analysis in Right Panel
**Given** user sends "I enjoyed to sleep"
**When** assistant responds
**Then** right panel shows "Professor (LLM)" section with:
- `rewrite`: "I enjoyed sleeping."
- `corrections`: [{"mistake":"enjoyed to sleep","fix":"enjoyed sleeping","why":"After 'enjoy', use gerund (-ing) not infinitive"}]
- `teacher_summary`: Brief feedback (max 200 chars)
- `next_practice`: 2-3 suggested practice sentences

### CA8: Layout - No Global Scroll
**Given** user opens Chat Coach page
**When** page renders
**Then**:
- Browser window has NO global scrollbar
- Message list (left column) has internal scrollbar
- Right panel is fixed (may have its own internal scroll if content is long)
- Both columns fill viewport height (`h-screen`)

### CA9: Auto-Scroll Behavior
**Given** user is at bottom of message list
**When** new message arrives
**Then** message list automatically scrolls to bottom

**Given** user manually scrolled up to read previous messages
**When** new message arrives
**Then** NO auto-scroll; show "Jump to latest" button (optional)

---

## Implementation Plan

### Phase 1: Diagnose + Fix LT (COMPLETED ✅)
1. ✅ Create diagnostic script for LT
2. ✅ Test "hi, how are ioy?" via direct LT API
3. ✅ Test via WebSocket
4. ✅ Fix DB session management
5. ✅ Fix LT category parsing (dict vs string)
6. ✅ Add regression test
7. ✅ Validate CA1

### Phase 1.5: Teacher LLM Backend (NEW)
1. Design separate teacher prompt (JSON output only)
2. Add `generate_teacher_analysis()` function to LLM provider
3. Update `handle_user_message()` to call teacher LLM after chat reply
4. Send `teacher_analysis` WS event with JSON payload
5. Persist in `ChatMessage.metadata_json['teacher_analysis']`
6. Add defensive sanitization to chat reply (remove meta-commentary)
7. Validate CA6, CA7

### Phase 2: Frontend Teacher Panel (NEW)
1. Create `TeacherAnalysisPanel.tsx` component
2. Handle `teacher_analysis` WS event in `ChatCoachSession.tsx`
3. Render teacher data in right panel (separate from LT issues)
4. Ensure teacher analysis never renders as chat message
5. Validate CA7

### Phase 3: Layout & Scroll (NEW)
1. Update `ChatCoachSession.tsx` layout:
   - Main wrapper: `h-screen overflow-hidden`
   - Left col: `flex-1 overflow-y-auto` for message list
   - Right panel: `w-80` or similar, `h-full overflow-y-auto`
2. Implement auto-scroll logic:
   - Track scroll position
   - Auto-scroll to bottom on new messages if near bottom
   - Show "Jump to latest" button if user scrolled up
3. Validate CA8, CA9

### Phase 4: Token-Aware Suggestions (DEFERRED)
1. Create WordCompletionService
2. Build next-word model script
3. Create NextWordService
4. Integrate into draft_update
5. Validate CA3

### Phase 5: GPU + Model (DEFERRED)
1. Update docker-compose.yml for CUDA
2. Download Qwen2.5-7B Q4_K_M model
3. Configure llama.cpp with GPU offload
4. Verify GPU usage in logs
5. Validate CA5

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
