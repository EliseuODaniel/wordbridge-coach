# Chat Coach - WebSocket Examples

## Connection

**Endpoint:** `ws://localhost:8000/api/v1/chat/ws/{conversation_id}`

```bash
# Using websocat
websocat ws://localhost:8000/api/v1/chat/ws/741aa782-6d71-443e-8124-365e5f582b6f

# Using wscat (Node.js)
wscat -c ws://localhost:8000/api/v1/chat/ws/741aa782-6d71-443e-8124-365e5f582b6f

# Using Python
import asyncio
import websockets

async def test_chat():
    uri = "ws://localhost:8000/api/v1/chat/ws/741aa782-6d71-443e-8124-365e5f582b6f"
    async with websockets.connect(uri) as ws:
        await ws.send('{"type":"ping","ts":1735132810000}')
        response = await ws.recv()
        print(response)

asyncio.run(test_chat())
```

---

## Event 1: draft_update (While Typing)

**Client → Server:**

```json
{
  "type": "draft_update",
  "conversation_id": "741aa782-6d71-443e-8124-365e5f582b6f",
  "draft_text": "I go to the",
  "cursor": 12,
  "client_ts_ms": 1735132810000
}
```

**Server → Client (draft_feedback):**

```json
{
  "type": "draft_feedback",
  "conversation_id": "741aa782-6d71-443e-8124-365e5f582b6f",
  "bar_score_raw": 45.0,
  "bar_score_components": {
    "spelling": 100.0,
    "grammar": 20.0,
    "syntax": 100.0,
    "lesson_alignment": 30.0,
    "naturalness": 50.0
  },
  "lesson_alignment_score": 30.0,
  "issues": [
    {
      "category": "grammar",
      "title": "Verb tense",
      "explanation": "Use past simple: 'go' → 'went'",
      "highlight_spans": [
        {"start": 2, "end": 4}
      ],
      "suggestions": ["went", "traveled", "stayed"]
    }
  ],
  "ghost_suggestion": null,
  "server_ts_ms": 1735132810050
}
```

**Key Points:**
- `draft_update` pode ser enviado a cada tecla (client throttle ~50ms)
- Backend roda `micro_eval()` apenas se passou `CHAT_MICRO_EVAL_MIN_INTERVAL_MS` (default: 90ms)
- `bar_score_raw` (0-100) é média ponderada: spelling(20%) + grammar(25%) + syntax(10%) + lesson_alignment(30%) + naturalness(15%)
- `issues` contém 1-3 problemas detectados (spelling, grammar, syntax, semantic, style)

---

## Event 2: request_autocomplete (After Idle)

**Client → Server:**

```json
{
  "type": "request_autocomplete",
  "conversation_id": "741aa782-6d71-443e-8124-365e5f582b6f",
  "draft_text": "I go",
  "client_ts_ms": 1735132812000,
  "mode": "soft"
}
```

**Server → Client (draft_feedback com ghost_suggestion):**

```json
{
  "type": "draft_feedback",
  "conversation_id": "741aa782-6d71-443e-8124-365e5f582b6f",
  "bar_score_raw": 50.0,
  "bar_score_components": {
    "spelling": 100,
    "grammar": 50,
    "syntax": 100,
    "lesson_alignment": 50,
    "naturalness": 50
  },
  "lesson_alignment_score": 50.0,
  "issues": [],
  "ghost_suggestion": "went to the",
  "server_ts_ms": 1735132812050
}
```

**Key Points:**
- `mode`: "soft" (1.2s idle) ou "hard" (2.5s idle)
- `ghost_suggestion` aparece no frontend como texto cinza após cursor
- Usuário aceita com TAB

---

## Event 3: user_message (Send Final Message)

**Client → Server:**

```json
{
  "type": "user_message",
  "conversation_id": "741aa782-6d71-443e-8124-365e5f582b6f",
  "content": "I go to the beach yesterday.",
  "client_ts_ms": 1735132815000
}
```

**Server → Client (streaming):**

```json
{"type": "assistant_stream_token", "conversation_id": "741aa782-6d71-443e-8124-365e5f582b6f", "token": "That "}
{"type": "assistant_stream_token", "conversation_id": "741aa782-6d71-443e-8124-365e5f582b6f", "token": "'s "}
{"type": "assistant_stream_token", "conversation_id": "741aa782-6d71-443e-8124-365e5f582b6f", "token": "great!"}
{"type": "assistant_stream_token", "conversation_id": "741aa782-6d71-443e-8124-365e5f582b6f", "token": "But "}
{"type": "assistant_stream_token", "conversation_id": "741aa782-6d71-443e-8124-365e5f582b6f", "token": "remember, "}
{"type": "assistant_stream_token", "conversation_id": "741aa782-6d71-443e-8124-365e5f582b6f", "token": "we "}
{"type": "assistant_stream_token", "conversation_id": "741aa782-6d71-443e-8124-365e5f582b6f", "token": "use "}
{"type": "assistant_stream_token", "conversation_id": "741aa782-6d71-443e-8124-365e5f582b6f", "token": "past "}
{"type": "assistant_stream_token", "conversation_id": "741aa782-6d71-443e-8124-365e5f582b6f", "token": "simple."}
```

**Server → Client (final):**

```json
{
  "type": "assistant_done",
  "conversation_id": "741aa782-6d71-443e-8124-365e5f582b6f",
  "full_content": "That's great! But remember, we use past simple.",
  "lesson_frame": {
    "cefr_target": "A2",
    "learning_goal": "past_simple_practice",
    "expected_intent": "describe_recent_activity",
    "topic": "weekend_plans",
    "rubric": {
      "grammar": ["past_tense_consistency"],
      "vocab": ["yesterday", "last_weekend"],
      "style": ["short_clear_sentences"]
    },
    "scoring_hints": {
      "avoid": ["present_continuous_for_past_events"],
      "encourage": ["time_markers", "irregular_verbs"]
    }
  },
  "summary_update": "Student practiced past simple. Made error with 'go' instead of 'went'."
}
```

**Key Points:**
- Mensagens user e assistant são persistidas no banco
- Streaming token-by-token (50ms delay no MockLLMProvider)
- `lesson_frame` pode ser atualizado pelo professor (no MVP, mantém o mesmo)
- `summary_update` é delta para o `session_summary`

---

## Event 4: ping (Heartbeat)

**Client → Server:**

```json
{
  "type": "ping",
  "ts": 1735132810000
}
```

**Server → Client:**

```json
{
  "type": "pong",
  "ts": 1735132810000
}
```

---

## Error Handling

**Error: Conversation not found**

```json
{
  "type": "error",
  "message": "Conversation not found",
  "code": "NOT_FOUND"
}
```

**Error: Unknown event type**

```json
{
  "type": "error",
  "message": "Unknown event type: invalid_type",
  "code": "UNKNOWN_EVENT"
}
```

---

## Complete Example (Python)

```python
import asyncio
import websockets
import json

CONVERSATION_ID = "741aa782-6d71-443e-8124-365e5f582b6f"
WS_URL = f"ws://localhost:8000/api/v1/chat/ws/{CONVERSATION_ID}"

async def test_chat_coach():
    async with websockets.connect(WS_URL) as ws:
        # Test 1: draft_update
        print("=== Test 1: draft_update ===")
        await ws.send(json.dumps({
            "type": "draft_update",
            "conversation_id": CONVERSATION_ID,
            "draft_text": "I go to the",
            "cursor": 12,
            "client_ts_ms": int(asyncio.get_event_loop().time() * 1000)
        }))
        response = await ws.recv()
        print(f"Received: {response}\n")

        # Test 2: user_message
        print("=== Test 2: user_message ===")
        await ws.send(json.dumps({
            "type": "user_message",
            "conversation_id": CONVERSATION_ID,
            "content": "Hello teacher!",
            "client_ts_ms": int(asyncio.get_event_loop().time() * 1000)
        }))

        # Receive streaming tokens
        while True:
            response = await ws.recv()
            data = json.loads(response)
            print(f"Token: {data.get('token', '')}")

            if data.get("type") == "assistant_done":
                print(f"\nFull response: {data['full_content']}")
                print(f"Lesson frame updated: {data['lesson_frame']}")
                break

asyncio.run(test_chat_coach())
```

---

## Throttling Behavior

**Scenario:** Usuário digita muito rápido (3 draft_updates em 100ms)

```
t=0ms:    draft_update "I" → micro_eval executado (ts=0)
t=50ms:   draft_update "I go" → ignorado (throttle: 50ms < 90ms)
t=100ms:  draft_update "I go to" → micro_eval executado (ts=100, 100ms >= 90ms)
```

**Log output:**
```
[Micro-eval] conversation_id=xxx, draft="I", scores=[...]
[Throttle] Skipped micro-eval (50ms < 90ms)
[Micro-eval] conversation_id=xxx, draft="I go to", scores=[...]
```

Resultado: Backend respeita throttle (10-15 Hz máximo), UI pode atualizar por tecla.
