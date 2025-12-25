# Change: Chat Coach - Real LLM (OpenAI + Local LLM)

**Status:** 📋 Planned
**Created:** 2025-12-25
**Author:** OpenSpec Process
**Related Specs:** 2025-12-chat-coach-mode-v1

---

## Overview

Replace MockLLMProvider with real LLM for natural, contextual conversations in Chat Coach, supporting both cloud (OpenAI) and local (llama.cpp) providers, while maintaining full backward compatibility with Spec4/Lingvist.

**Current State:** Chat Coach uses MockLLMProvider with heuristic-based responses (v5)
**Target State:** Chat Coach uses local LLM (llama.cpp) or OpenAI API via HTTP (no SDK), with strict mode to prevent silent fallback

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

### 4. Offline-First Design with Local LLM Preference
- **Primary:** Local LLM (llama.cpp) running on user's machine (8GB VRAM)
- **Optional:** Cloud LLM (OpenAI) with explicit opt-in
- Feature flags control provider selection
- Strict mode prevents silent fallback to Mock
- Local LLM works completely offline (no network required)

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

## Local LLM (8GB VRAM)

### Runtime Options

#### Opção A: Docker (llama.cpp server)
**File:** `docker-compose.yml`

Add `llm` service:
- Image: `ghcr.io/ggerganov/llama.cpp:server`
- Expose port: `8080` (internal)
- Network: `filltheword-net`
- Volume: `llm_models:/models`
- Command: Server pointing to `/models/model.gguf`
- GPU: Optional (via deploy.resources.reservations.devices)

**API Environment:**
```yaml
CHAT_LLM_PROVIDER=llamacpp
CHAT_LLM_BASE_URL=http://llm:8080/v1
CHAT_LLM_MODEL=qwen2.5-7b-instruct
CHAT_LLM_STRICT=true
```

#### Opção B: Host (LM Studio)
**File:** `docker-compose.yml`

API service uses:
```yaml
CHAT_LLM_BASE_URL=http://host.docker.internal:1234/v1
```

**Prerequisites:**
- LM Studio running on host
- Port `1234` exposed
- Model loaded in LM Studio

### Feature Flags (Local LLM)

#### CHAT_LLM_PROVIDER
- **Values:** `mock` | `openai_http` | `llamacpp`
- **Default:** `llamacpp` (changed from `mock`)
- **Purpose:** Explicit provider selection

#### CHAT_LLM_BASE_URL
- **Format:** URL with `/v1` suffix
  - Docker: `http://llm:8080/v1`
  - Host: `http://host.docker.internal:1234/v1`
- **Default:** (empty)
- **Required:** Only when CHAT_LLM_PROVIDER=llamacpp or openai_http

#### CHAT_LLM_MODEL
- **Format:** Model name (identifier in server)
  - llama.cpp: Filename without `.gguf` (e.g., `qwen2.5-7b-instruct`)
  - OpenAI: Model name (e.g., `gpt-4o-mini`)
- **Default:** `qwen2.5-7b-instruct`
- **Purpose:** Model selection

#### CHAT_LLM_STRICT
- **Values:** `true` | `false`
- **Default:** `false`
- **Purpose:** Prevent silent fallback to Mock
- **Behavior:**
  - If `true` and provider fails → Send WebSocket error event
  - If `false` and provider fails → Fallback to Mock silently

#### CHAT_LLM_NETWORK_ENABLED
- **Values:** `true` | `false`
- **Default:** `false`
- **Purpose:** Master switch for EXTERNAL providers only
- **Behavior:**
  - Local LLM (`llamacpp`) ignores this flag
  - OpenAI (`openai_http`) respects this flag

### Performance Notes (8GB VRAM)

#### Recommended Models
- **Primary:** Qwen2.5-7B-Instruct GGUF (Q4_K_M)
  - Multilingual (EN, PT, ES)
  - Good quality
  - Fits in 8GB VRAM
  - ~5GB VRAM usage

- **Alternative:** Mistral-7B-Instruct-v0.3 GGUF Q4
  - English-focused
  - Fast inference
  - ~4.5GB VRAM usage

#### Quantization Trade-offs
- **Q4_K_M:** Best balance (quality + size)
- **Q5_K_M:** Better quality, ~6GB VRAM
- **Q3_K_M:** Fits easily, lower quality

### Acceptance Criteria

1. **No Silent Mock Fallback:**
   - When `CHAT_LLM_PROVIDER=llamacpp` and `CHAT_LLM_STRICT=true`
   - Provider must be `LlamaCppLLMProvider`, NOT `MockLLMProvider`
   - On error → WebSocket error event (no fallback)

2. **Natural Conversation:**
   - User: "hi, how are you?"
   - Response: Natural greeting (NOT template)
   - No "professor mecânico" patterns

3. **Panel Functionality:**
   - micro_tip appears when `issues=[]`
   - Issues detected when errors present
   - Panel does NOT zero on Enter

4. **Offline Operation:**
   - Local LLM works with `CHAT_LLM_NETWORK_ENABLED=false`
   - No external network calls



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

#### 2.1b Local LLM Provider Implementation
**File:** `/api/app/llm/llamacpp_provider.py`

```python
class LlamaCppLLMProvider(LLMProviderBase):
    def __init__(
        self,
        base_url: str,
        model: str = "qwen2.5-7b-instruct",
        timeout: int = 60,
        strict: bool = False
    ):
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.strict = strict
        self.client = httpx.AsyncClient(timeout=timeout)

    async def chat_stream(self, messages, system_prompt, generation_config):
        # Call llama.cpp server (OpenAI-compatible)
        # POST {base_url}/chat/completions with stream=true
        # No API key required
        # Stream tokens via async generator
        # If strict=True, raise on error; else fallback to Mock

    async def micro_eval(self, context, lesson_frame, draft, student_profile):
        # Use heuristic evaluation (separate from Mock)
        # TODO: Extract logic from Mock to helper module

    async def autocomplete(self, context, lesson_frame, draft, student_profile):
        # Use heuristic autocomplete (separate from Mock)
        # TODO: Extract logic from Mock to helper module
```

**Key Decisions:**
- OpenAI-compatible API (same endpoints, no API key)
- Base URL includes `/v1` suffix
- Filter `generation_config` to only send supported params:
  - `temperature`, `max_tokens`, `top_p`, `frequency_penalty`, `presence_penalty`
  - Ignore internal params like `lesson_frame`
- Strict mode: Raise exception instead of silent Mock fallback
- micro_eval/autocomplete: Keep heuristic (can refactor later)


#### 2.2 Factory Pattern (Updated)
**File:** `/api/app/llm/factory.py`

```python
def get_llm_provider_from_env() -> LLMProviderBase:
    """Read feature flags and return appropriate provider."""
    provider = os.getenv("CHAT_LLM_PROVIDER", "llamacpp")
    strict = os.getenv("CHAT_LLM_STRICT", "false").lower() == "true"

    # Local LLM (llamacpp) - ignores CHAT_LLM_NETWORK_ENABLED
    if provider == "llamacpp":
        base_url = os.getenv("CHAT_LLM_BASE_URL")
        if not base_url:
            msg = "CHAT_LLM_PROVIDER=llamacpp but CHAT_LLM_BASE_URL not set"
            if strict:
                raise ValueError(msg)
            logger.warning(f"{msg}, falling back to Mock")
            return MockLLMProvider()

        model = os.getenv("CHAT_LLM_MODEL", "qwen2.5-7b-instruct")
        timeout = int(os.getenv("CHAT_OPENAI_TIMEOUT_S", "60"))

        logger.info(f"Using LlamaCppLLMProvider (model={model}, base_url={base_url}, strict={strict})")
        return LlamaCppLLMProvider(base_url=base_url, model=model, timeout=timeout, strict=strict)

    # OpenAI (external) - respects CHAT_LLM_NETWORK_ENABLED
    if provider == "openai_http":
        network_enabled = os.getenv("CHAT_LLM_NETWORK_ENABLED", "false").lower() == "true"
        if not network_enabled:
            if strict:
                raise ValueError("CHAT_LLM_NETWORK_ENABLED=false but CHAT_LLM_STRICT=true")
            logger.info("CHAT_LLM_NETWORK_ENABLED=false, using MockLLMProvider")
            return MockLLMProvider()

        api_key = os.getenv("CHAT_OPENAI_API_KEY")
        if not api_key:
            msg = "CHAT_OPENAI_API_KEY not set"
            if strict:
                raise ValueError(msg)
            logger.warning(f"{msg}, falling back to Mock")
            return MockLLMProvider()

        model = os.getenv("CHAT_OPENAI_MODEL", "gpt-4o-mini")
        timeout = int(os.getenv("CHAT_OPENAI_TIMEOUT_S", "30"))

        logger.info(f"Using OpenAILLMProvider (model={model}, strict={strict})")
        return OpenAILLMProvider(api_key=api_key, model=model, timeout=timeout, strict=strict)

    # Mock (explicit or default)
    logger.info("Using MockLLMProvider")
    return MockLLMProvider()
```

**Key Changes:**
- Default provider changed from `mock` to `llamacpp`
- Local LLM ignores `CHAT_LLM_NETWORK_ENABLED`
- `CHAT_LLM_STRICT` controls error behavior (raise vs fallback)
- Clear logging: "Using X Provider (strict=Y)"

#### 2.3 Update Chat Endpoint (Enhanced)
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

**Additional Changes:**

1. **generation_config Cleanup:**
   - Remove internal objects (e.g., `lesson_frame`) from `generation_config`
   - Only keep standard LLM params: `temperature`, `max_tokens`, `top_p`, etc.

2. **System Prompt Construction:**
   - Build `system_prompt` from `lesson_frame_json`
   - Example:
   ```python
   lesson_frame = conversation.lesson_frame_json
   system_prompt = f"""You are an English conversation tutor helping a {lesson_frame.get('cefr_target', 'A2')} level student.

   Learning Goal: {lesson_frame.get('learning_goal', 'conversation practice')}
   Topic: {lesson_frame.get('topic', 'general')}
   Expected Intent: {lesson_frame.get('expected_intent', 'general conversation')}

   Keep responses conversational and natural. Respond to what the user actually says.
   """
   ```

3. **Provider Logging:**
   - Log after initialization:
   ```python
   logger.info(f"Chat Coach LLM provider: {get_provider_name(llm_provider)} (strict={strict}, base_url={base_url})")
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

### FASE 3 - Apply (Infrastructure: Local Runtime)

#### 3.1 Docker Compose - llama.cpp Service
**File:** `docker-compose.yml`

Add `llm` service:

```yaml
services:
  api:
    # ... existing config ...
    environment:
      - CHAT_LLM_PROVIDER=llamacpp
      - CHAT_LLM_BASE_URL=http://llm:8080/v1
      - CHAT_LLM_MODEL=qwen2.5-7b-instruct
      - CHAT_LLM_STRICT=true
    depends_on:
      - llm

  llm:
    image: ghcr.io/ggerganov/llama.cpp:server
    container_name: filltheword-llm
    restart: unless-stopped
    ports:
      - "8080:8080"  # Internal only (not exposed to host)
    volumes:
      - llm_models:/models
    environment:
      - MODEL_PATH=/models/model.gguf
      - HOST=0.0.0.0
      - PORT=8080
      - N_GPU_LAYERS=-1  # -1 = offload all to GPU (if available)
      - N_CTX=4096       # Context window size
    command: >
      /llama-server
      --model /models/model.gguf
      --host 0.0.0.0
      --port 8080
      --ctx-size 4096
      --n-gpu-layers -1
    networks:
      - filltheword-net
    # GPU support (optional, requires nvidia-docker)
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

volumes:
  llm_models:
    driver: local

networks:
  filltheword-net:
    driver: bridge
```

#### 3.2 Model Download Script
**File:** `scripts/download_model.sh`

```bash
#!/bin/bash
# Download Qwen2.5-7B-Instruct GGUF model

set -e

MODEL_URL="https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_k_m.gguf"
MODEL_FILE="llm_models/qwen2.5-7b-instruct-q4_k_m.gguf"

# Create directory
mkdir -p llm_models

# Check if model already exists
if [ -f "$MODEL_FILE" ]; then
    echo "Model already exists: $MODEL_FILE"
    echo "Skipping download."
    exit 0
fi

echo "Downloading Qwen2.5-7B-Instruct GGUF (Q4_K_M)..."
echo "This may take a while (~5GB)..."

# Download
curl -L -o "$MODEL_FILE" "$MODEL_URL"

echo "Download complete: $MODEL_FILE"
echo "Model size: $(du -h "$MODEL_FILE" | cut -f1)"
```

**Usage:**
```bash
chmod +x scripts/download_model.sh
./scripts/download_model.sh
```

#### 3.3 .gitignore Update
**File:** `.gitignore`

```gitignore
# LLM models (large files, not committed)
llm_models/*.gguf
llm_models/
!llm_models/.gitkeep
```

Create `.gitkeep`:
```bash
touch llm_models/.gitkeep
git add llm_models/.gitkeep
```

#### 3.4 Model Setup Instructions

**Step 1: Download Model**
```bash
# Option A: Using script
./scripts/download_model.sh

# Option B: Manual download
# Visit: https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF
# Download: qwen2.5-7b-instruct-q4_k_m.gguf
# Save to: llm_models/qwen2.5-7b-instruct-q4_k_m.gguf
```

**Step 2: Verify Model**
```bash
ls -lh llm_models/
# Should show: qwen2.5-7b-instruct-q4_k_m.gguf (~5GB)
```

**Step 3: Start Services**
```bash
docker compose up -d --build
```

**Step 4: Verify LLM Service**
```bash
# Check logs
docker logs filltheword-llm

# Test API (optional)
curl http://localhost:8080/v1/models
```

#### 3.5 Alternative: Host-Based LM Studio

If using LM Studio instead of Docker llama.cpp:

**1. Update docker-compose.yml (API service):**
```yaml
environment:
  - CHAT_LLM_BASE_URL=http://host.docker.internal:1234/v1
```

**2. LM Studio Setup:**
- Open LM Studio
- Load model: Qwen2.5-7B-Instruct-GGUF
- Start server on port `1234`
- Enable "CORS" and "Allow External Connections"

**3. Test Connection:**
```bash
curl http://host.docker.internal:1234/v1/models
```

---

### FASE 4 - Validate

#### 4.1 Unit Tests (Local LLM)
**File:** `/api/tests/test_chat_coach_llamacpp_provider.py`

```python
@pytest.mark.asyncio
async def test_llamacpp_provider_chat_stream():
    """Test llama.cpp provider with MockTransport."""
    # Mock SSE response
    def handler(request):
        # Return SSE stream with tokens
        return httpx.Response(
            200,
            content=b'data: {"choices":[{"delta":{"content":"Hello"}}]}\n\n'
                    b'data: {"choices":[{"delta":{"content":" world"}}]}\n\n'
                    b'data: [DONE]\n\n',
            headers={"Content-Type": "text/event-stream"}
        )

    transport = httpx.MockTransport(handler)
    provider = LlamaCppLLMProvider(base_url="http://test:8080/v1")
    provider.client = httpx.AsyncClient(transport=transport)

    tokens = []
    async for token in provider.chat_stream(messages, system_prompt, generation_config):
        tokens.append(token)

    assert "".join(tokens) == "Hello world"

@pytest.mark.asyncio
async def test_llamacpp_provider_strict_mode():
    """Test strict mode raises on error."""
    provider = LlamaCppLLMProvider(
        base_url="http://invalid:9999/v1",
        strict=True
    )

    with pytest.raises(Exception):
        tokens = []
        async for token in provider.chat_stream(messages, system_prompt, generation_config):
            tokens.append(token)

@pytest.mark.asyncio
async def test_llamacpp_provider_filters_generation_config():
    """Test that generation_config is filtered."""
    provider = LlamaCppLLMProvider(base_url="http://test:8080/v1")

    # Mock handler to inspect request
    def handler(request):
        payload = json.loads(request.content)
        # Should NOT include lesson_frame
        assert "lesson_frame" not in payload
        # Should include standard params
        assert "temperature" in payload
        assert "max_tokens" in payload
        return httpx.Response(200, content=b'data: [DONE]\n\n')

    transport = httpx.MockTransport(handler)
    provider.client = httpx.AsyncClient(transport=transport)

    # Call with generation_config containing lesson_frame
    gen_config = {
        "temperature": 0.7,
        "max_tokens": 1000,
        "lesson_frame": {"topic": "past_simple"}  # Should be filtered
    }

    async for token in provider.chat_stream(messages, system_prompt, gen_config):
        pass
```

#### 4.2 Unit Tests (OpenAI Provider - Existing)
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

#### 4.2 Manual Validation (Local LLM)

**Prerequisites:**
```bash
# 1. Download model
./scripts/download_model.sh

# 2. Start services
docker compose up -d --build

# 3. Verify LLM service
docker logs filltheword-llm
# Should show: "llama server listening at..."
```

**Conversation Test Cases:**
1. **Natural Greeting:** User: "hi, how are you?" → Assistant: Natural greeting (NOT template)
2. **PT Greeting:** User: "ola, tudo bem?" → Assistant: Responds naturally, may mention comma
3. **Grammar Error:** User: "I go to market yesterday" → Assistant: Corrects to "went"
4. **Meta-Question:** User: "what should I practice?" → Assistant: Explains Chat Coach
5. **No Issues:** User: "Yesterday I went to the market" → Assistant: Affirms + asks follow-up

**Panel Test Cases:**
1. **Typing with errors:** Bar score drops (e.g., 45), issues show in right panel
2. **Press Enter:** Panel KEEPS showing feedback (does NOT reset to 100)
3. **Start new message:** Type new draft → Panel clears, fresh feedback appears
4. **Perfect sentence:** Type "Yesterday I went to the market" → issues=[], micro_tip shows
5. **micro_tip content:** Should be contextual (e.g., "Well done! Tell me more about it.")

**Feature Flag Test Cases:**
1. `CHAT_LLM_PROVIDER=llamacpp` + strict=false → Falls back to Mock on error
2. `CHAT_LLM_PROVIDER=llamacpp` + strict=true → Raises error (WS error event) on failure
3. `CHAT_LLM_PROVIDER=mock` → Uses MockLLMProvider
4. `CHAT_LLM_PROVIDER=openai_http` + network=false → Uses Mock (respects network flag)
5. `CHAT_LLM_PROVIDER=llamacpp` + network=false → Uses LlamaCpp (ignores network flag)

**Performance Test (8GB VRAM):**
- Monitor GPU: `nvidia-smi` or equivalent
- Expected VRAM usage: ~5GB for Qwen2.5-7B Q4_K_M
- Token generation speed: ~20-50 tokens/s (depends on GPU)

#### 4.3 Offline Tests (No Network)

**Test Setup:**
```bash
# Disconnect from network (optional)
# Or just ensure CHAT_LLM_PROVIDER=llamacpp (local)
```

**Test Cases:**
1. **Local LLM Works Offline:**
   - Set `CHAT_LLM_PROVIDER=llamacpp`
   - Set `CHAT_LLM_NETWORK_ENABLED=false`
   - Verify: Chat Coach works normally
   - Verify: No external network calls (check logs)

2. **Strict Mode Error:**
   - Stop LLM service: `docker stop filltheword-llm`
   - Set `CHAT_LLM_STRICT=true`
   - Try to send message
   - Verify: WebSocket error event sent
   - Verify: User sees error message (not silent fallback)

3. **Non-Strict Mode Fallback:**
   - Stop LLM service: `docker stop filltheword-llm`
   - Set `CHAT_LLM_STRICT=false`
   - Try to send message
   - Verify: Falls back to Mock silently
   - Verify: Conversation continues (no error)

#### 4.4 Manual Validation (OpenAI - Optional)

**Test Setup:**
```bash
# Set OpenAI credentials
export CHAT_LLM_PROVIDER=openai_http
export CHAT_LLM_NETWORK_ENABLED=true
export CHAT_OPENAI_API_KEY=sk-...
export CHAT_OPENAI_MODEL=gpt-4o-mini
docker compose restart api
```

**Test Cases:**
1. **Natural Conversation:** Send message → Verify natural response from OpenAI
2. **Error Handling:** Invalid API key → Verify fallback or error (depending on strict mode)


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

### Backend (Local LLM)
- [ ] `LlamaCppLLMProvider` implements `LLMProviderBase` correctly
- [ ] `chat_stream()` calls llama.cpp server via HTTP (OpenAI-compatible)
- [ ] SSE streaming works (tokens arrive incrementally)
- [ ] `generation_config` filtering works (lesson_frame removed)
- [ ] Strict mode raises exception on error
- [ ] Non-strict mode falls back to Mock on error
- [ ] micro_eval uses heuristic (not MockLLMProvider directly)
- [ ] autocomplete uses heuristic (not MockLLMProvider directly)

### Backend (OpenAI)
- [ ] `OpenAILLMProvider` implements `LLMProviderBase` correctly
- [ ] `chat_stream()` calls OpenAI API via HTTP and streams tokens
- [ ] Timeout handling works (no unhandled exceptions)
- [ ] Fallback to Mock on API error (if not strict)

### Factory
- [ ] Default provider changed to `llamacpp`
- [ ] `CHAT_LLM_PROVIDER=llamacpp` creates `LlamaCppLLMProvider`
- [ ] `CHAT_LLM_PROVIDER=openai_http` creates `OpenAILLMProvider`
- [ ] `CHAT_LLM_PROVIDER=mock` creates `MockLLMProvider`
- [ ] Local LLM ignores `CHAT_LLM_NETWORK_ENABLED`
- [ ] OpenAI respects `CHAT_LLM_NETWORK_ENABLED`
- [ ] `CHAT_LLM_STRICT=true` prevents fallback
- [ ] Clear logging on startup

### Chat Endpoint
- [ ] `chat.py` uses factory instead of hardcoded provider
- [ ] `generation_config` cleanup (remove lesson_frame)
- [ ] `system_prompt` constructed from `lesson_frame_json`
- [ ] Provider logged on startup

### Frontend
- [ ] `DraftFeedbackOut` schema includes `micro_tip` field
- [ ] `_build_draft_feedback()` generates micro_tip when issues=[]
- [ ] Frontend types include `micro_tip?: string`
- [ ] `AnalysisPanel` renders micro_tip when issues=[]
- [ ] Panel persists on Enter (regression test)

### Infrastructure
- [ ] `llm` service added to docker-compose.yml
- [ ] `llm_models` volume created
- [ ] GPU support configured (optional)
- [ ] `download_model.sh` script works
- [ ] `.gitignore` excludes `.gguf` files

### Integration
- [ ] Chat Coach works with local LLM (llamacpp)
- [ ] Chat Coach works with OpenAI (openai_http)
- [ ] Chat Coach works with Mock (mock)
- [ ] Local LLM works offline (network disabled)
- [ ] Spec4/Lingvist unaffected (smoke test)

### Documentation
- [ ] Environment variables documented in README.md
- [ ] Model download instructions clear
- [ ] 8GB VRAM requirements documented
- [ ] Privacy note about local vs cloud LLM
- [ ] Change file updated with validation evidence

### Tests
- [ ] Unit tests for LlamaCppLLMProvider with MockTransport
- [ ] Unit tests for strict mode error handling
- [ ] Unit tests for generation_config filtering
- [ ] Manual validation: Natural conversation (not template)
- [ ] Manual validation: Panel works (issues + micro_tip)
- [ ] Manual validation: Offline operation
- [ ] Performance test: ~5GB VRAM usage


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
