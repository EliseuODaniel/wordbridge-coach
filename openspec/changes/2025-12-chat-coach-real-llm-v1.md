# Change: Chat Coach - Real LLM (OpenAI via HTTP)

**Status:** 📋 Planned
**Created:** 2025-12-25
**Author:** OpenSpec Process
**Related Specs:** 2025-12-chat-coach-mode-v1

---

## Overview

Replace MockLLMProvider with real OpenAI API calls for natural, contextual conversations in Chat Coach, while maintaining full backward compatibility with Spec4/Lingvist.

**Current State:** Chat Coach uses MockLLMProvider with heuristic-based responses (v5)
**Target State:** Chat Coach uses OpenAI API via HTTP (no SDK) for chat_stream(), with Mock fallback

---

## Goals

### 1. Natural, Contextual Conversation
- Assistant responds to user's actual message content (not just excerpts)
- Maintains conversation history awareness
- Handles edge cases naturally:
  - Greetings in PT/ES ("ola", "olá", "oi", "hola", "buen día")
  - Meta-questions ("what should I practice?", "how does this work?")
  - Short phrases and incomplete sentences

### 2. Always-Useful Right Panel
- **When issues exist:** Show specific, actionable feedback with canonical categories
- **When issues=[]:** Show `micro_tip` with helpful guidance
  - Examples: "Good start! Try expanding with...", "Try asking a question about..."
- **Critical:** Panel MUST NOT zero on Enter (already fixed in v1.3)

### 3. Backward Compatibility
- **Spec4/Lingvist remain 100% intact**
- Chat Coach continues to be additive (no changes to existing flows)
- No database migrations required
- No breaking changes to WebSocket protocol

### 4. Offline-First Design
- Feature flags control network access
- Graceful degradation to Mock when:
  - Network disabled
  - API key missing
  - Timeout/error occurs
  - Explicit CHAT_LLM_PROVIDER=mock

---

## Non-Goals

- [ ] Lesson frame evolution (not now)
- [ ] Streaming rework (keep current WebSocket flow)
- [ ] Database schema changes
- [ ] Frontend architecture changes
- [ ] Prompt engineering optimization (use sensible defaults)

---

## Privacy & Security

### External API Usage
- **Provider:** OpenAI API (https://api.openai.com)
- **Data Sent:** Conversation messages (system + user roles), current draft text
- **Data Received:** Streaming tokens for assistant response
- **Storage:** Messages stored in local PostgreSQL (no external PII sent to OpenAI beyond user_id if present)

### User Privacy
- User ID sent to OpenAI for context (may be UUID, not email/name)
- No additional PII sent beyond message content
- API key stored in environment variable (never committed)
- Network access can be disabled via `CHAT_LLM_NETWORK_ENABLED=false`

### Compliance Notes
- Users must be informed that Chat Coach uses external API when enabled
- Acceptable under "offline-first with optional cloud enhancement" model
- Fallback to Mock ensures functionality without network

---

## Feature Flags

### CHAT_LLM_PROVIDER
- **Values:** `mock` | `openai_http`
- **Default:** `mock`
- **Purpose:** Explicit provider selection
- **Override:** Takes precedence over CHAT_LLM_NETWORK_ENABLED

### CHAT_LLM_NETWORK_ENABLED
- **Values:** `true` | `false`
- **Default:** `false`
- **Purpose:** Master switch for network access
- **Behavior:** If `false`, forces Mock even if CHAT_LLM_PROVIDER=openai_http

### CHAT_OPENAI_API_KEY
- **Format:** `sk-...` (OpenAI API key)
- **Default:** (empty)
- **Required:** Only when CHAT_LLM_PROVIDER=openai_http
- **Storage:** Environment variable, NOT in .env (committed)

### CHAT_OPENAI_MODEL
- **Values:** `gpt-4o-mini` | `gpt-4o` | `gpt-3.5-turbo`
- **Default:** `gpt-4o-mini`
- **Purpose:** Model selection for chat_stream()

### CHAT_OPENAI_TIMEOUT_S
- **Values:** Integer (seconds)
- **Default:** `30`
- **Purpose:** Request timeout for OpenAI API calls

---

## Implementation Plan

### FASE 2 - Apply (Backend)

#### 2.1 OpenAI Provider Implementation
**File:** `/api/app/llm/openai_provider.py`

```python
class OpenAILLMProvider(LLMProviderBase):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", timeout: int = 30):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def chat_stream(self, messages, lesson_frame, student_profile):
        # Call OpenAI Chat Completions API
        # Stream tokens via async generator
        # Fallback to Mock on error

    async def micro_eval(self, context, lesson_frame, draft, student_profile):
        # Delegate to MockLLMProvider.micro_eval() for now
        # (Real LLM eval not implemented in this change)

    async def autocomplete(self, context, lesson_frame, draft, student_profile):
        # Delegate to MockLLMProvider.autocomplete() for now
        # (Real LLM autocomplete not implemented in this change)
```

**Key Decisions:**
- Use `httpx.AsyncClient` (no OpenAI SDK)
- Timeout handling with httpx.TimeoutException
- Error fallback to MockLLMProvider on network/API failure
- Streaming via `async for` generator

#### 2.2 Factory Pattern
**File:** `/api/app/llm/factory.py`

```python
def get_llm_provider_from_env() -> LLMProviderBase:
    """Read feature flags and return appropriate provider."""
    provider = os.getenv("CHAT_LLM_PROVIDER", "mock")

    network_enabled = os.getenv("CHAT_LLM_NETWORK_ENABLED", "false").lower() == "true"
    if not network_enabled:
        return MockLLMProvider()

    if provider == "openai_http":
        api_key = os.getenv("CHAT_OPENAI_API_KEY")
        if not api_key:
            logger.warning("CHAT_OPENAI_API_KEY not set, falling back to Mock")
            return MockLLMProvider()

        model = os.getenv("CHAT_OPENAI_MODEL", "gpt-4o-mini")
        timeout = int(os.getenv("CHAT_OPENAI_TIMEOUT_S", "30"))

        return OpenAILLMProvider(api_key=api_key, model=model, timeout=timeout)

    # Default fallback
    return MockLLMProvider()
```

#### 2.3 Update Chat Endpoint
**File:** `/api/app/api/api_v1/endpoints/chat.py`

**Line 32 (BEFORE):**
```python
llm_provider = MockLLMProvider()
```

**Line 32 (AFTER):**
```python
from app.llm.factory import get_llm_provider_from_env
llm_provider = get_llm_provider_from_env()
```

#### 2.4 Improve Mock Heuristics
**File:** `/api/app/llm/mock_provider.py`

**Additions to `_analyze_text()`:**
- PT/ES greeting detection: "ola", "olá", "oi", "bom dia", "hola", "buen día"
- Lowercase "i" detection: standalone "i" in sentence
- Contraction detection: "im", "dont", "cant", "lets", "wont"
- Ensure `micro_eval()` generates `top_issues` for these cases

**Rationale:** Mock fallback should still be high-quality

---

### FASE 3 - Apply (Frontend)

#### 3.1 Backend Schema Update
**File:** `/api/app/api/api_v1/schemas/chat.py`

**Add to DraftFeedbackOut:**
```python
micro_tip: Optional[str] = None  # Shown when issues=[]
```

#### 3.2 Update Feedback Builder
**File:** `/api/app/api/api_v1/endpoints/chat.py`

**Modify `_build_draft_feedback()`:**
```python
def _build_draft_feedback(...):
    # ... existing logic ...

    # Generate micro_tip when no issues
    if not eval_result["top_issues"]:
        micro_tip = _generate_micro_tip(draft, lesson_frame)
    else:
        micro_tip = None

    return DraftFeedbackOut(
        # ... existing fields ...
        micro_tip=micro_tip
    )
```

#### 3.3 Frontend Type Updates
**File:** `/frontend/src/services/api.ts`

**Add to DraftFeedbackEvent interface:**
```typescript
micro_tip?: string;
```

#### 3.4 Update Analysis Panel
**File:** `/frontend/src/components/AnalysisPanel.tsx`

**Logic:**
- If `issues.length > 0`: Render existing issue list
- If `issues.length === 0 && micro_tip`: Render micro_tip in styled box
- If `issues.length === 0 && !micro_tip`: Show "Great job! No issues detected."

---

### FASE 4 - Validate

#### 4.1 Unit Tests
**File:** `/api/tests/test_chat_coach_openai_provider.py`

```python
@pytest.mark.asyncio
async def test_openai_provider_chat_stream():
    """Test OpenAI provider with MockTransport."""
    transport = httpx.MockTransport(...)
    provider = OpenAILLMProvider(api_key="test", client=transport)

    tokens = []
    async for token in provider.chat_stream(messages, {}, {}):
        tokens.append(token)

    assert len(tokens) > 0
    # Verify response is contextual

@pytest.mark.asyncio
async def test_openai_provider_timeout():
    """Test timeout handling."""
    provider = OpenAILLMProvider(api_key="test", timeout=0.001)

    # Should fallback to Mock on timeout
    tokens = []
    async for token in provider.chat_stream(messages, {}, {}):
        tokens.append(token)

    # Verify fallback occurred (no exception raised)

@pytest.mark.asyncio
async def test_portuguese_greeting_detection():
    """Test Mock detects PT greetings correctly."""
    provider = MockLLMProvider()

    test_cases = [
        "ola, how are you",
        "olá tudo bem",
        "oi, eu sou",
        "hola como estas",
    ]

    for text in test_cases:
        analysis = provider._analyze_text(text, {})
        # Verify greeting intent detected
        assert analysis["intent"] == "greeting"
        # Verify punctuation issue detected
        assert len(analysis["detected_errors"]) > 0
```

#### 4.2 Manual Validation Test Cases

**Conversation Test Cases:**
1. **PT/ES Greeting:** User: "ola, how are you" → Assistant: Greets back, mentions comma issue
2. **Meta-Question:** User: "what should I practice?" → Assistant: Explains Chat Coach usage
3. **Grammar Error:** User: "I go to market yesterday" → Assistant: Corrects to "went"
4. **No Issues:** User: "Yesterday I went to the market" → Assistant: Affirms + follows up

**Panel Test Cases:**
1. **Typing with errors:** Bar score drops, issues show
2. **Press Enter:** Panel KEEPS showing feedback (NOT zeros to 100)
3. **Start new message:** Panel clears, fresh feedback appears
4. **Perfect sentence:** issues=[], micro_tip shows

**Feature Flag Test Cases:**
1. `CHAT_LLM_PROVIDER=mock` → Uses Mock
2. `CHAT_LLM_NETWORK_ENABLED=false` → Uses Mock (even if provider=openai_http)
3. `CHAT_OPENAI_API_KEY missing` → Falls back to Mock with warning log
4. `CHAT_LLM_PROVIDER=openai_http + key set` → Uses OpenAI

---

### FASE 5 - Archive

#### 5.1 Update Change File
- Mark status as ✅ Applied
- Add validation evidence:
  - Test results (pytest output)
  - Screenshot of Chat Coach with OpenAI response
  - Log snippet showing "Using OpenAILLMProvider" or "Using MockLLMProvider"
- Link to next iteration (if any)

#### 5.2 Archive
- Move to `/openspec/changes/archived/2025-12-chat-coach-real-llm-v1.md`
- Reference in parent spec: `2025-12-chat-coach-mode-v1.md`

---

## Validation Checklist

### Backend
- [ ] `OpenAILLMProvider` implements `LLMProviderBase` correctly
- [ ] `chat_stream()` calls OpenAI API via HTTP and streams tokens
- [ ] Timeout handling works (no unhandled exceptions)
- [ ] Fallback to Mock on API error
- [ ] `factory.get_llm_provider_from_env()` respects all feature flags
- [ ] `chat.py` uses factory instead of hardcoded MockLLMProvider
- [ ] Mock heuristics detect PT/ES greetings, "i", contractions
- [ ] All existing tests still pass (10/10)

### Frontend
- [ ] `DraftFeedbackOut` schema includes `micro_tip` field
- [ ] `_build_draft_feedback()` generates micro_tip when issues=[]
- [ ] Frontend types include `micro_tip?: string`
- [ ] `AnalysisPanel` renders micro_tip when issues=[]
- [ ] Panel persists on Enter (regression test)

### Integration
- [ ] Chat Coach works with OpenAI (CHAT_LLM_PROVIDER=openai_http)
- [ ] Chat Coach works with Mock (CHAT_LLM_PROVIDER=mock)
- [ ] Chat Coach works offline (CHAT_LLM_NETWORK_ENABLED=false)
- [ ] Spec4/Lingvist unaffected (smoke test)

### Documentation
- [ ] Environment variables documented in README.md
- [ ] Privacy note about external API added
- [ ] Change file updated with validation evidence

---

## Open Questions

1. **Prompt Engineering:** What system prompt should OpenAI use?
   - **Proposed:** Use existing system message from conversation history
   - **Decision:** Keep simple for v1, optimize in later change

2. **micro_eval with OpenAI:** Should we implement real LLM-based evaluation?
   - **Decision:** NO for v1 (delegate to Mock), future change

3. **autocomplete with OpenAI:** Should we implement real LLM-based autocomplete?
   - **Decision:** NO for v1 (delegate to Mock), future change

4. **Cost Monitoring:** How to track OpenAI API usage?
   - **Decision:** Add logging in v1, metrics in later change

---

## References

- **Parent Spec:** `2025-12-chat-coach-mode-v1.md`
- **Previous Changes:** v1.1 (context), v1.2 (panel fix), v1.3 (conversational)
- **OpenAI API Docs:** https://platform.openai.com/docs/api-reference/chat
- **httpx Docs:** https://www.python-httpx.org/
