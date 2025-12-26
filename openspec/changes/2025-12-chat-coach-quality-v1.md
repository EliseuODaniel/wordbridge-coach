# Change: Chat Coach - Fix Response Duplication + Rich Analysis Panel

**Status:** 🔥 Hotfix In Progress
**Created:** 2025-12-25
**Updated:** 2025-12-25 (Hotfix for critical issues)
**Author:** Claude (executor)
**Related Specs:** 2025-12-chat-coach-mode-v1

---

## Overview

**Original Problems:**
1. **Response Duplication:** LLM generates a 2nd turn (often in quotes, simulating student's speech)
2. **Poor Analysis Panel:** Lacks rich signals and doesn't update frequently during typing (throttle issues)

**Hotfix Issues (CRITICAL - discovered during testing):**
1. **Empty Response Bug:** Stop sequences include empty strings `''`, causing LLM to generate 0 tokens
2. **Hidden Rich Signals:** AnalysisPanel returns early when `issues=[]`, hiding all rich signals

**Impact:** Chat Coach completely broken (no responses) and analysis panel appears empty

---

## Root Cause Analysis

### CRITICAL: Hotfix Issue 1 - Empty Stop Strings

**Location:** `api/app/api/api_v1/endpoints/chat.py:761`

**Current code:**
```python
generation_config = {
    "temperature": 0.5,
    "max_tokens": 300,
    "top_p": 0.9,
    "stop": ['\n"', '\nUser:', '\nUSER:', '\nStudent:', '\nSTUDENT:', '', ''],  # ← BUG HERE
    "frequency_penalty": 0.0,
    "presence_penalty": 0.0
}
```

**Problem:**
- Empty strings `''` in stop list cause Llama.cpp to stop immediately
- LLM generates 0 tokens → empty response
- User sees no assistant message at all

**Evidence:**
- Llama.cpp treats empty string as "stop on next token"
- Since next token is at position 0, generation never starts

### CRITICAL: Hotfix Issue 2 - AnalysisPanel Early Return

**Location:** `frontend/src/components/AnalysisPanel.tsx:30-49`

**Current code:**
```tsx
// Case 1: No issues + micro_tip available
if (issues.length === 0 && micro_tip) {
    return (
      <div className="text-center py-4">
        <div className="bg-blue-900">💡 {micro_tip}</div>
      </div>
    );
}

// Case 2: No issues + no micro_tip
if (issues.length === 0) {
    return <div className="text-center py-4"><p>No issues detected.</p></div>;
}

// Case 3: Has issues (only reaches here if issues.length > 0)
```

**Problem:**
- When `issues.length === 0`, function returns early
- Never renders: `suggested_next_words`, `topic`, `intent`, `rewrite`
- User sees empty panel even when backend sends rich signals

**Impact:**
- Panel appears dead/useless even when working correctly
- Users can't see helpful suggestions (next words, topic, intent, rewrite)

### Issue 3: Duplicate Response (Original)

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

## HOTFIX SOLUTION (Critical Issues)

### Hotfix A) Fix Empty Stop Strings

**A1. Filter empty strings in chat.py (api/app/api/api_v1/endpoints/chat.py):**
```python
# Build stop sequences without empty strings
stop_sequences = [
    '\n\n"',
    '\nUser:', '\nUSER:', '\nStudent:', '\nSTUDENT:',
    '">', '<|',
]

# Filter out any empty strings or whitespace-only strings
stop_sequences = [s for s in stop_sequences if isinstance(s, str) and s.strip()]

generation_config = {
    "temperature": 0.5,
    "max_tokens": 300,
    "top_p": 0.9,
    "stop": stop_sequences,  # ← Clean list without ''
    "frequency_penalty": 0.0,
    "presence_penalty": 0.0
}
```

**A2. Add defensive filter in llamacpp_provider.py (api/app/llm/llamacpp_provider.py):**
```python
def _filter_generation_config(config: dict) -> dict:
    """Filter and validate generation config before passing to llama.cpp."""
    filtered = {}

    for key, value in config.items():
        if key == "stop":
            # Handle stop sequences
            if isinstance(value, list):
                # Filter out empty/whitespace strings
                filtered_stop = [s for s in value if isinstance(s, str) and s.strip()]
                if filtered_stop:
                    filtered[key] = filtered_stop
            elif isinstance(value, str):
                # Single stop string
                if value.strip():
                    filtered[key] = value
            # else: ignore empty stop
        else:
            filtered[key] = value

    return filtered
```

**A3. Add empty response detection (optional but recommended):**
```python
# After streaming loop in handle_user_message
if not full_response.strip():
    # Send error to client
    await websocket.send_json(ErrorOut(
        type="error",
        message="Assistant returned empty response. Please try again.",
        code="EMPTY_LLM_RESPONSE"
    ).model_dump())
    return  # Don't persist empty message
```

### Hotfix B) Fix AnalysisPanel Early Return

**B1. Remove early returns in AnalysisPanel.tsx (frontend/src/components/AnalysisPanel.tsx):**
```tsx
const AnalysisPanel: React.FC<AnalysisPanelProps> = ({
  issues, micro_tip, suggested_next_words, topic, intent, rewrite, className = ''
}) => {
  // REMOVED: Early returns for issues.length === 0
  // Now always render rich signals first

  return (
    <div className={`space-y-3 ${className}`}>
      <h3 className="text-sm font-semibold text-gray-300 mb-3">Feedback</h3>

      {/* Rich signals - ALWAYS RENDER THESE FIRST */}
      {(topic || intent) && (
        <div className="flex flex-wrap gap-2 mb-3">
          {topic && <span className="badge topic">🏷️ Topic: {topic}</span>}
          {intent && <span className="badge intent">🎯 Intent: {intent}</span>}
        </div>
      )}

      {suggested_next_words && suggested_next_words.length > 0 && (
        <div className="suggested-words">
          <span>✨ Try these words:</span>
          {suggested_next_words.map(word => (
            <span key={word} className="chip">{word}</span>
          ))}
        </div>
      )}

      {rewrite && (
        <div className="rewrite-suggestion">
          <h4>💡 Suggested Rewrite:</h4>
          <p>"{rewrite}"</p>
        </div>
      )}

      {micro_tip && (
        <div className="micro-tip">
          <p>💡 {micro_tip}</p>
        </div>
      )}

      {/* Issues - render if present, otherwise show "no issues" message */}
      {issues.length > 0 ? (
        issues.map((issue, index) => (
          <div key={index} className="issue-card">
            {/* Render issue */}
          </div>
        ))
      ) : (
        <div className="no-issues">
          <p className="text-gray-500 text-sm">✅ No issues detected. Great job!</p>
        </div>
      )}
    </div>
  );
};
```

### Hotfix C) Enrich draft_feedback Data

**C1. Add topic/intent/rewrite to MockLLMProvider.micro_eval() (api/app/llm/mock_provider.py):**
```python
async def micro_eval(self, context: str, lesson_frame: dict, draft: str, student_profile: dict):
    analysis = self._analyze_text(draft, lesson_frame)

    # ... existing code ...

    return {
        # ... existing fields ...
        "top_issues": detected_errors,

        # NEW: Add rich signals
        "suggested_next_words": analysis.get("suggested_next_words", []),
        "topic": analysis.get("topic"),
        "intent": analysis.get("intent"),
        "rewrite": analysis.get("rewrite"),  # Priority: use analysis rewrite first
    }
```

**C2. Prioritize rewrite in _build_draft_feedback() (api/app/api/api_v1/endpoints/chat.py):**
```python
# Extract rich signals from eval_result (if available)
suggested_next_words = eval_result.get("suggested_next_words", [])
topic = eval_result.get("topic")
intent = eval_result.get("intent")

# Use rewrite from eval_result as priority
rewrite = eval_result.get("rewrite")

# Fallback: if no rewrite from eval_result, use first suggestion from first issue
if not rewrite and issues and issues[0].get("suggestions"):
    rewrite = issues[0]["suggestions"][0]
```

---

## Acceptance Criteria (Updated for Hotfix)

### Critical - Chat Response
- **Send "hello":** Assistant responds with streaming text (NOT empty)
- **Send "lets go":** Assistant responds with streaming text (NOT empty)
- **No empty responses:** 10 messages → all have visible assistant replies

### Critical - Analysis Panel
- **Type "I go" (no errors yet):** Panel shows topic/intent/suggested_next_words
- **Panel NEVER empty:** Always shows at least one signal (tip, topic, words, or issues)
- **Rich signals visible:** topic, intent, rewrite appear when available

### Original - Chat Quality
- **10 messages sent:** 0 occurrences with block looking like "user's speech"

### Original - Analysis Panel
- **Typing for 5s:** Panel updates at least 5 times
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
