# Change: Chat Coach - Fix Response Duplication + Rich Analysis Panel

**Status:** 📋 Planned
**Created:** 2025-12-25
**Author:** Claude (executor)
**Related Specs:** 2025-12-chat-coach-mode-v1

---

## Overview

**Problems:**
1. **Response Duplication:** LLM generates a 2nd turn (often in quotes, simulating student's speech)
2. **Poor Analysis Panel:** Lacks rich signals and doesn't update frequently during typing (throttle issues)

**Impact:** Chat Coach feels unnatural and unhelpful despite having real LLM

---

## Root Cause Analysis

### Issue 1: Duplicate Response

**Current code (chat.py:668-691):**
```python
# 1. Build context including system from DB
messages = _build_context_messages(str(conversation.id), db, limit=10)

# 2. Build new system prompt from lesson_frame
lesson_frame = conversation.lesson_frame_json
system_prompt = f"""You are an English conversation tutor...
Think step-by-step internally. Answer naturally and briefly in 1-2 sentences...
"""

# 3. Pass both to provider
async for token in llm_provider.chat_stream(messages, system_prompt, generation_config):
    ...
```

**Problem:**
- `_build_context_messages()` includes old `system` message from DB
- New `system_prompt` parameter may be ignored if messages already has `role="system"`
- LLM sees outdated/conflicting system prompt → generates extra turn

**Evidence (from provider code):**
```python
# llamacpp_provider.py:119
has_system = any(msg.get("role") == "system" for msg in messages)
if not has_system and system_prompt:
    messages = [{"role": "system", "content": system_prompt}] + messages
```
**Bug:** Only injects system_prompt if NO system message exists in context!

### Issue 2: Analysis Panel

**Current problems:**
1. `suggested_next_words` not exposed to frontend (exists in MockLLMProvider but not sent)
2. Throttle causes panel to go "dead" (no updates when typing fast)
3. No topic/intent signals
4. No rewrite suggestion

---

## Proposed Solution

### A) Fix Context/Prompt (Backend)

**A1. Ensure Single System Prompt:**
```python
# In _build_context_messages(), add flag:
def _build_context_messages(conversation_id: str, db: Session,
                          limit: int = 10, exclude_system: bool = False):
    if exclude_system:
        # Only return non-system messages
        ...

# In handle_user_message:
messages = _build_context_messages(str(conversation.id), db, limit=10, exclude_system=True)
```

**A2. Strengthen System Prompt:**
```python
system_prompt = f"""You are an English conversation tutor helping a {cefr} level student.

Learning Goal: {learning_goal}
Topic: {topic}
Expected Intent: {expected_intent}

IMPORTANT:
- Reply as the assistant ONLY.
- Never write the student's next message.
- Do not include quoted example replies.
- No role labels like "User:", "Assistant:", "Student:".
- Answer naturally and briefly in 1-3 sentences.
- Always ask one relevant follow-up question.
- If user writes PT/ES, encourage English gently.
"""
```

**A3. Add Stop Sequences:**
```python
generation_config = {
    "temperature": 0.5,
    "max_tokens": 300,
    "top_p": 0.9,
    "stop": ["\n\"", "\nUser:", "\nUSER:", "\nStudent:", "\nSTUDENT:",
            "","",""]
}
```

**A4. Defensive Sanitization:**
```python
def _sanitize_assistant_response(response: str) -> str:
    """Remove extra user simulation from LLM response."""
    lines = response.split('\n')

    # Remove quoted paragraph at the end (looks like user simulation)
    if len(lines) >= 2 and not lines[-2].strip():
        if lines[-1].strip().startswith('"'):
            lines = lines[:-1]

    # Truncate at role labels
    for i, line in enumerate(lines):
        if line.strip().startswith(('User:', 'USER:', 'Student:', 'STUDENT:')):
            lines = lines[:i]
            break

    return '\n'.join(lines).strip()
```

### B) Enrich Analysis Panel (Backend + Frontend)

**B1. Backend Schema (chat.py):**
```python
class DraftFeedbackOut(BaseModel):
    # Existing fields
    draft: str
    bar_score: int
    issues: List[IssueOut]
    micro_tip: Optional[str] = None

    # NEW FIELDS
    suggested_next_words: List[str] = []
    topic: Optional[str] = None
    intent: Optional[str] = None
    rewrite: Optional[str] = None
```

**B2. Expose from MockLLMProvider:**
```python
# Already returns these, just need to pass through:
# - suggested_next_words
# - detected_errors (has topic/intent info)
```

**B3. Throttle Solution:**
```python
# In handle_draft_update, cache last feedback by conversation_id
_feedback_cache: Dict[str, DraftFeedbackOut] = {}

if not should_run_micro_eval:
    # Reuse last feedback
    last_feedback = _feedback_cache.get(str(conversation.id))
    if last_feedback:
        # Update with current draft
        last_feedback.draft = draft
        await websocket.send_json(last_feedback)
        return
```

**B4. Frontend (AnalysisPanel.tsx):**
```tsx
// Show suggested next words as chips
{feedback.suggested_next_words && feedback.suggested_next_words.length > 0 && (
  <div className="suggested-words">
    <span>Try:</span>
    {feedback.suggested_next_words.map(word => (
      <span key={word} className="chip">{word}</span>
    ))}
  </div>
)}

// Show topic/intent as badges
{(feedback.topic || feedback.intent) && (
  <div className="context-tags">
    {feedback.topic && <span className="badge topic">{feedback.topic}</span>}
    {feedback.intent && <span className="badge intent">{feedback.intent}</span>}
  </div>
)}

// Show rewrite suggestion
{feedback.rewrite && (
  <div className="rewrite-suggestion">
    <h4>Suggested Rewrite:</h4>
    <p>{feedback.rewrite}</p>
  </div>
)}
```

---

## Acceptance Criteria (Measurable)

### Chat Quality
- **10 messages sent:** 0 occurrences with block looking like "user's speech"
  - No paragraph starting with quotes after blank line
  - No "User:", "Student:" labels

### Analysis Panel
- **Typing for 5s:** Panel updates at least 5 times
- **Shows:** issues OR micro_tip + suggested_next_words
- **No dead periods:** Panel always shows something (cached or fresh)

### No Regression
- **Spec4/Lingvist:** Sanity manual test passes
- **Existing tests:** All pass

---

## Changes Required

### Backend
1. `api/app/api/api_v1/endpoints/chat.py`:
   - Fix `_build_context_messages()` to exclude system when flag set
   - Strengthen system_prompt (add constraints)
   - Add stop sequences to generation_config
   - Add `_sanitize_assistant_response()` helper
   - Update `_build_draft_feedback()` to include new fields
   - Implement feedback cache for throttle

2. `api/app/schemas/chat.py`:
   - Add `suggested_next_words`, `topic`, `intent`, `rewrite` to DraftFeedbackOut

### Frontend
3. `frontend/src/services/api.ts`:
   - Update DraftFeedbackEvent interface

4. `frontend/src/components/AnalysisPanel.tsx`:
   - Render suggested_next_words chips
   - Render topic/intent badges
   - Render rewrite suggestion
   - Ensure panel persists on Enter

---

## Implementation Order

1. **Fix duplication** (chat.py: context + prompt + stop + sanitize)
2. **Enrich schema** (schemas + chat.py: expose fields)
3. **Fix throttle** (chat.py: cache logic)
4. **Update UI** (AnalysisPanel.tsx)
5. **Add tests** (sanitization test)
6. **Validate** (manual UI + regression)

---

## Validation Plan

1. Manual UI test:
   - "hello" → natural response, no extra block
   - "lets go" → issue + suggestion, no duplication
   - "I go market yesterday" → tense issue + "went" suggestion

2. Unit test:
   - Test `_sanitize_assistant_response()` with various patterns

3. Regression:
   - Test Spec4 smoke test
   - Run existing tests

---

## References

- **Parent Spec:** 2025-12-chat-coach-mode-v1
- **Previous Change:** 2025-12-chat-coach-llm-local-fix-v1
- **Chat Endpoint:** `/api/app/api/api_v1/endpoints/chat.py`
- **Schema:** `/api/app/schemas/chat.py`
- **Frontend:** `/frontend/src/components/AnalysisPanel.tsx`
