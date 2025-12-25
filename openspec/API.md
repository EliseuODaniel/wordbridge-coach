# FillTheWord API Specification

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication

Current MVP: No authentication required (multi-user demo with local profiles)

## Endpoints

### Users

#### List All Users
```http
GET /api/v1/users
```

**Response**:
```json
[
  {
    "id": "uuid-string",
    "username": "john_doe",
    "language_preference": "pt",
    "created_at": "2025-12-12T20:30:00Z"
  },
  {
    "id": "uuid-string",
    "username": "marie_dupont",
    "language_preference": "fr",
    "created_at": "2025-12-12T19:15:00Z"
  }
]
```

#### Create User
```http
POST /api/v1/users
```

**Request Body**:
```json
{
  "username": "new_user",
  "language_preference": "en",
  "target_language": "en",
  "mode": "spec4"
}
```

**Optional Fields**:
- `language_preference`: Native/interface language (pt, es, fr, en). Default: "pt"
- `target_language`: Learning target language (en, fr). Default: "en"
- `mode`: Learning mode ("spec4" | "lingvist"). Default: "spec4" - ⚠️ NOVO

**Examples**:
```json
// Spec4 mode (default, clássico)
{
  "username": "john_doe",
  "language_preference": "pt",
  "target_language": "en",
  "mode": "spec4"
}

// Lingvist mode (adaptativo)
{
  "username": "jane_doe",
  "language_preference": "pt",
  "target_language": "en",
  "mode": "lingvist"
}

// French learner
{
  "username": "marie_dupont",
  "language_preference": "fr",
  "target_language": "fr",
  "mode": "spec4"
}
```

**Response**:
```json
{
  "id": "new-uuid-string",
  "username": "new_user",
  "language_preference": "en",
  "mode": "spec4",
  "created_at": "2025-12-12T21:00:00Z"
}
```

**Error Response** (409 Conflict):
```json
{
  "error": "Username already exists",
  "message": "Username 'new_user' is already taken"
}
```

#### Get User by ID
```http
GET /api/v1/users/{user_id}
```

**Response**:
```json
{
  "id": "uuid-string",
  "username": "john_doe",
  "language_preference": "en",
  "created_at": "2025-12-12T20:30:00Z"
}
```

**Error Response** (404 Not Found):
```json
{
  "error": "User not found",
  "message": "User with ID {user_id} not found"
}
```

#### Update User
```http
PATCH /api/v1/users/{user_id}
```

**Request Body**:
```json
{
  "username": "new_username",
  "language_preference": "fr",
  "target_language": "fr",
  "word_goal_rank": 1500,
  "mode": "lingvist"
}
```

**Optional Fields**:
- `username`: New display name
- `language_preference`: Native interface language (pt, es, fr, en)
- `target_language`: Learning target language (en, fr)
- `word_goal_rank` (Spec4): Vocabulary goal from {100, 500, 1500, 3000, 5000, 10000}
- `mode`: Learning mode ("spec4" | "lingvist") - ⚠️ NOVO

**Response**: Same as GET user with updated values

**Error Response** (409 Conflict):
```json
{
  "error": "Username already exists",
  "message": "Username 'new_username' is already taken"
}
```

**Behavior**:
- Changing `target_language` resets user progress and initializes new cards for the new language.
- **Spec4**: Changing `word_goal_rank` adjusts `UserFrequencyProgress.current_window_end_rank = min(current, new_goal)` to respect new limit.

#### Delete User
```http
DELETE /api/v1/users/{user_id}
```

**Response**:
```json
{
  "message": "User deleted successfully",
  "deleted_records": {
    "user": 1,
    "card_states": 45,
    "word_stats": 12,
    "review_events": 23
  }
}
```

**Behavior**: Cascades delete all user data including UserCardState, UserWordStats, and ReviewEvent records.

### Cards

#### Get Next Card
```http
GET /api/v1/cards/next
```

**Query Parameters**:
- `user_id` (optional, string): User ID for demo user if not provided

**Response**:
```json
{
  "card_id": "uuid-card-real",
  "word_id": "uuid-word",
  "sentence_id": "uuid-sentence",
  "word": "book",
  "sentence": "The ___ is on the table.",
  "gap": {"start": 4, "end": 7},
  "sentence_translation": "O livro está na mesa.",
  "grammar_hint": "Use the word for furniture",
  "memory_stage": "NEW",
  "is_new": true,
  "audio_word_url": "http://localhost:8001/api/tts/word/{card_id}?text=book&lang=en",
  "audio_sentence_url": "http://localhost:8001/api/tts/sentence/{card_id}?text=The book is on the table.&lang=en"
}
```

#### Get Next Card (Spec4 - Variedade + Progressão)
```http
GET /api/v1/cards/next-spec4
```

**Spec4 Algorithm**: Implementa progressão de vocabulário com janela dinâmica e variedade de frases.

**Query Parameters**:
- `user_id` (optional, string): User ID for demo user if not provided
- `exclude_card_id` (optional, string): Card ID to exclude from selection (avoid repeating same card)

**Response**:
```json
{
  "card_id": "uuid-card-real",  // SEMPRE Card.id UUID existente no banco
  "word_id": "uuid-word",       // Word.id separado
  "sentence_id": "uuid-sentence",
  "word": "book",
  "sentence": "The ___ is on the table.",
  "gap": {"start": 4, "end": 7},
  "sentence_translation": "O livro está na mesa.",
  "grammar_hint": "noun, singular",
  "memory_stage": "NEW",  // Uppercase SM-2: NEW/LEARNING/REVIEW/MATURE/RELEARN
  "is_new": true,
  "audio_word_url": "http://localhost:8001/api/tts/word/{card_id}?text=book&lang=en",
  "audio_sentence_url": "http://localhost:8001/api/tts/sentence/{card_id}?text=The book is on the table.&lang=en"
}
```

**Spec4 Features**:
- **Mix 25% novas / 75% revisões**: Controlado via `UserSessionStats`
- **Janela dinâmica**: Expande automaticamente (100 → 200 → 300...)
- **Variedade de frases**: Prefere frases nunca vistas, evita últimas K=10 usadas
- **Gating prefixal**: Só introduz rank N+1 se ranks 1..N foram acertados ≥1 vez
- **Reforço de erros**: Palavras com baixa accuracy aparecem mais frequentemente

**Critical Contract**:
- `card_id` é **SEMPRE** um `Card.id` real existente na tabela `Card`
- `word_id` é **SEMPRE** o `Word.id` separado (para variedade de frases)
- `sentence_id` indica qual frase foi selecionada (para rastrear variedade)
- `exclude_card_id` deve ser o `card_id` retornado anteriormente

**Audio URLs**:
- As URLs `audio_word_url` e `audio_sentence_url` retornadas pelo endpoint são **root-relative** (`/api/tts/...`)
- No runtime, funcionam via frontend origin (nginx/vite proxy para `http://tts:8001/api/tts/...`)
- Exemplo: `/api/tts/word/{card_id}?text=book&lang=en` → proxy para TTS service → retorna audio binary

#### Get Next Card (Lingvist - Inline Cloze + Hints + Audio pós-acerto)
```http
GET /api/v1/cards/next-lingvist
```

**Status**: 📋 Proposed (ver [change proposal](openspec/changes/2025-12-lingvist-mode-v1.md))

**Lingvist Algorithm**: Reutiliza Spec4, mas com payload enriquecido para input inline, hints progressivos e áudio pós-acerto.

**Query Parameters**:
- `user_id` (optional, string): User ID for demo user if not provided
- `exclude_card_id` (optional, string): Card ID to exclude from selection

**Response**:
```json
{
  "card_id": "550e8400-e29b-41d4-a716-446655440000",
  "word_id": "660e8400-e29b-41d4-a716-446655440000",
  "sentence_id": "770e8400-e29b-41d4-a716-446655440000",
  "word": "book",
  "sentence": "The ___ is on the table.",
  "gap": {"start": 4, "end": 7},
  "correct_answer": "book",  // ⚠️ NOVO: campo explícito (não em Spec4)
  "grammar_tag_pt": "substantivo, masculino, singular",  // ⚠️ NOVO
  "word_translation_pt": "livro",  // ⚠️ NOVO
  "sentence_translation_pt": "O livro está na mesa.",  // ⚠️ NOVO
  "sentence_source": "Dracula",  // ⚠️ NOVO: se aplicável
  "is_new": true,
  "micro_progress": {  // ⚠️ NOVO
    "current": 3,
    "total": 10,
    "new_words": 2
  },
  "audio_word_url": "/api/tts/word/{card_id}?text=book&lang=en",
  "audio_sentence_url": "/api/tts/sentence/{card_id}?text=The book is on the table.&lang=en"
}
```

**Diferenças de Spec4**:
- `correct_answer`: Campo explícito para validação client-side
- `grammar_tag_pt`: Tag gramatical em PT-BR (ex: "substantivo, plural")
- `word_translation_pt`: Tradução PT-BR da palavra-alvo
- `sentence_translation_pt`: Tradução PT-BR da frase completa
- `micro_progress`: Progresso da sessão (X/Y)
- Mesmo Spec4 features: mix, gating, variedade, anti-repetição

**Mix Recomendado**: 20% novas / 80% revisão (mais conservativo que Spec4)

**Critical Contracts**:
- Mesmo que Spec4: `card_id` real, `word_id` separado, `sentence_id` para variedade
- `correct_answer` é o valor esperado do campo `gap` após preenchimento

**Behavior**:
- Input inline na lacuna (sem botão "Check")
- Auto-submit ao digitar `correct_answer` (normalizado)
- Hints progressivos aparecem após erros/tempo preso
- Áudio da frase toca **apenas** após acerto (não ao carregar card)
- Próximo card avança **apenas** após áudio terminar (ou timeout 3s)

**Empty Values**:
- `grammar_tag_pt` → vazio se não disponível
- `word_translation_pt` → vazio se não traduzido
- `sentence_translation_pt` → vazio se não traduzido (mostra "Tradução indisponível" no UI)
- `sentence_source` → vazio se template ou gerado

#### Submit Answer
```http
POST /api/v1/cards/{card_id}/answer
```

**Request Body**:
```json
{
  "answer": "book",
  "response_time_ms": 2500,
  "attempts": 1,
  "hints_used": 0
}
```

**Optional Fields**:
- `attempts`: Number of attempts taken (default: 1) - ⚠️ NOVO
- `hints_used`: Number of hints used (default: 0) - ⚠️ NOVO

**Response**:
```json
{
  "correct": true,
  "correct_answer": "book",
  "sentence_full": "The book is on the table.",
  "quality": 5,
  "next_review_at": "2025-12-15T10:30:00Z"
}
```

**Side Effects**:
1. **Creates/Updates `UserCardState`**: SM-2 progress (repetitions, easiness_factor, interval_days, next_review_at)
2. **Creates `ReviewEvent`**: Analytics com `sentence_id` preenchido (Spec4: obrigatório para variedade)
3. **Updates `UserSessionStats`**: Incrementa `cards_shown` e `new_cards_shown` (Spec4: controle de mix)
4. **Updates `UserWordStats`**: Accuracy e mastery por palavra
5. **Updates `UserFrequencyProgress`**: `max_contiguous_mastered_rank` (Spec4: progressão de vocabulário)
6. **Updates `User.accuracy_last_20`**: Calcula accuracy das últimas 20 respostas - ⚠️ NOVO
7. **Manages `UserCardState.is_relearn/relearn_due`**: Se mode="lingvist", quality < 3 entra em relearn queue - ⚠️ NOVO

**Spec4 Critical**: `ReviewEvent.sentence_id` é **SEMPRE** preenchido com `card.sentence_id` para suportar variedade de frases.

### Chat Coach (Conversational Training with Real-time Feedback)

**Status**: 📝 Proposed (see [change proposal](../changes/2025-12-chat-coach-mode-v1.md))

The Chat Coach module uses a hybrid REST + WebSocket architecture:
- **REST endpoints** for conversation and message management
- **WebSocket** for real-time draft feedback and streaming responses

#### REST Endpoints

##### Create Conversation
```http
POST /api/v1/chat/conversations
```

**Request Body**:
```json
{
  "user_id": "uuid-string",
  "title": "Practice Past Simple"
}
```

**Response**:
```json
{
  "id": "new-conversation-uuid",
  "user_id": "uuid-string",
  "title": "Practice Past Simple",
  "student_profile_json": {
    "cefr_level": "A2",
    "common_errors": ["past_simple", "articles"]
  },
  "lesson_frame_json": {
    "cefr_target": "A2",
    "learning_goal": "conversation_start",
    "expected_intent": "introduction",
    "topic": "getting_started",
    "rubric": {
      "grammar": [],
      "vocab": [],
      "style": ["friendly"]
    }
  },
  "session_summary": "",
  "created_at": "2025-12-25T10:00:00Z",
  "updated_at": "2025-12-25T10:00:00Z"
}
```

##### List Conversations
```http
GET /api/v1/chat/conversations?user_id={user_id}
```

**Query Parameters**:
- `user_id` (required, string): User ID

**Response**:
```json
[
  {
    "id": "conversation-uuid-1",
    "title": "Practice Past Simple",
    "created_at": "2025-12-25T10:00:00Z",
    "updated_at": "2025-12-25T10:15:00Z",
    "message_count": 15
  },
  {
    "id": "conversation-uuid-2",
    "title": "Business English",
    "created_at": "2025-12-24T14:30:00Z",
    "updated_at": "2025-12-24T15:00:00Z",
    "message_count": 8
  }
]
```

##### Get Conversation Messages
```http
GET /api/v1/chat/conversations/{conversation_id}/messages
```

**Response**:
```json
[
  {
    "id": "message-uuid-1",
    "conversation_id": "conversation-uuid",
    "role": "system",
    "content": "You are an English teacher. Your student is A2 level.",
    "created_at": "2025-12-25T10:00:00Z"
  },
  {
    "id": "message-uuid-2",
    "conversation_id": "conversation-uuid",
    "role": "assistant",
    "content": "Hello! Let's practice past simple. What did you do last weekend?",
    "created_at": "2025-12-25T10:00:01Z"
  },
  {
    "id": "message-uuid-3",
    "conversation_id": "conversation-uuid",
    "role": "user",
    "content": "I go to the beach.",
    "created_at": "2025-12-25T10:00:10Z"
  }
]
```

##### Delete Conversation
```http
DELETE /api/v1/chat/conversations/{conversation_id}
```

**Response**: `204 No Content`

#### WebSocket Endpoint

##### Connect to Chat
```http
WS /api/v1/chat/ws/{conversation_id}
```

**Connection Parameters**:
- `conversation_id` (path parameter): UUID of conversation

**Query Parameters**:
- `user_id` (optional): User ID for validation

**WebSocket Message Types**:

###### Client → Server Events

**draft_update** (sent while typing)
```json
{
  "type": "draft_update",
  "conversation_id": "uuid-string",
  "draft_text": "I go to the",
  "cursor": 12,
  "client_ts_ms": 1735132810000
}
```

**user_message** (send final message)
```json
{
  "type": "user_message",
  "conversation_id": "uuid-string",
  "content": "I go to the beach yesterday.",
  "client_ts_ms": 1735132815000
}
```

**request_autocomplete** (after idle time)
```json
{
  "type": "request_autocomplete",
  "conversation_id": "uuid-string",
  "draft_text": "I go",
  "client_ts_ms": 1735132812000,
  "mode": "soft"
}
```

**ping** (heartbeat)
```json
{
  "type": "ping",
  "ts": 1735132810000
}
```

###### Server → Client Events

**draft_feedback** (response to draft_update)
```json
{
  "type": "draft_feedback",
  "conversation_id": "uuid-string",
  "bar_score_raw": 45.0,
  "bar_score_components": {
    "spelling": 100.0,
    "grammar": 20.0,
    "syntax": 80.0,
    "lesson_alignment": 30.0,
    "naturalness": 50.0
  },
  "lesson_alignment_score": 30.0,
  "issues": [
    {
      "category": "grammar",
      "title": "Verb tense",
      "explanation": "Use past simple for yesterday: 'go' → 'went'",
      "highlight_spans": [
        {"start": 2, "end": 4}
      ],
      "suggestions": ["went", "traveled", "drove"]
    }
  ],
  "ghost_suggestion": "went to the",
  "server_ts_ms": 1735132810050
}
```

**assistant_stream_token** (streaming response)
```json
{
  "type": "assistant_stream_token",
  "conversation_id": "uuid-string",
  "token": "That"
}
```

**assistant_done** (end of streaming)
```json
{
  "type": "assistant_done",
  "conversation_id": "uuid-string",
  "full_content": "That's great! But remember, we use past simple for yesterday. Can you try again?",
  "lesson_frame": {
    "cefr_target": "A2",
    "learning_goal": "past_simple_regular_verbs",
    "expected_intent": "describe_recent_activity",
    "topic": "weekend_plans",
    "rubric": {
      "grammar": ["past tense consistency"],
      "vocab": ["yesterday", "last weekend", "went", "visited"],
      "style": ["short clear sentences"]
    },
    "scoring_hints": {
      "avoid": ["present continuous for past events"],
      "encourage": ["time markers", "irregular verbs"]
    }
  },
  "summary_update": "Student practiced past simple. Made error with 'go' instead of 'went'. Needs more practice with irregular verbs."
}
```

**error**
```json
{
  "type": "error",
  "message": "Conversation not found",
  "code": "NOT_FOUND"
}
```

**pong** (response to ping)
```json
{
  "type": "pong",
  "ts": 1735132810000
}
```

#### Feature Flags (Environment Variables)

```bash
# LLM Configuration
CHAT_LLM_PROVIDER=mock              # mock | llamacpp | openai | anthropic
CHAT_LLM_BASE_URL=http://llm:8080   # llama.cpp server URL

# Real-time Feedback
CHAT_MICRO_EVAL_MIN_INTERVAL_MS=100 # Minimum interval between LLM calls (10 Hz max)
CHAT_IDLE_SOFT_MS=1200              # Time before first autocomplete suggestion
CHAT_IDLE_HARD_MS=2500              # Time before extended autocomplete

# UI Smoothing
CHAT_EMA_ALPHA=0.4                  # Exponential moving average alpha (0-1)

# Concurrency
CHAT_MAX_CONCURRENT_DRAFT_UPDATES=5 # Max concurrent draft updates per connection
```

#### Rate Limiting

- **draft_update**: Client should throttle to ~50ms (20 Hz max)
- **micro_eval** (LLM calls): Backend throttles to `CHAT_MICRO_EVAL_MIN_INTERVAL_MS` (default: 100ms = 10 Hz)
- **request_autocomplete**: Only sent after idle time (tracked by backend)
- **Fast analyzers** (spelling/grammar/syntax): No throttling (run on every draft_update)

#### Performance Targets

- **draft_feedback latency**: <200ms p95 (fast analyzers) / <500ms p95 (with LLM)
- **assistant_stream_first_token**: <500ms
- **WebSocket connection**: <100ms
- **Ghost suggestion**: <1500ms after idle_soft

See [change proposal](../changes/2025-12-chat-coach-mode-v1.md) for complete implementation details.

### Statistics

#### Get Basic Stats
```http
GET /api/v1/stats/basic
```

**Query Parameters**:
- `user_id` (optional, string): User ID for demo user if not provided

**Response**:
```json
{
  "cards_total": 150,
  "new_count": 45,
  "learning_count": 67,
  "review_count": 23,
  "mature_count": 15,
  "reviews_today": 12,
  "accuracy_today": 0.75,
  "new_cards_today": 8,
  "upcoming_reviews": {
    "2025-12-13": 5,
    "2025-12-14": 8,
    "2025-12-15": 12,
    "2025-12-16": 6,
    "2025-12-17": 9,
    "2025-12-18": 11,
    "2025-12-19": 7
  }
}
```

### Settings

#### Get User Settings
```http
GET /api/v1/settings/
```

**Query Parameters**:
- `user_id` (optional, string): User ID for demo user if not provided

**Response**:
```json
{
  "daily_new_limit": 10,
  "easiness_factor": 2.5
}
```

#### Update User Settings
```http
PATCH /api/v1/settings/
```

**Query Parameters**:
- `user_id` (optional, string): User ID for demo user if not provided

**Request Body**:
```json
{
  "daily_new_limit": 15,
  "easiness_factor": 2.6
}
```

**Response**: Same as GET (updated values)

### Insights

#### Get Word Insights
```http
GET /api/v1/insights/word/{word_id}
```

**Parameters**:
- `word_id`: Word identifier

**Response**:
```json
{
  "word_id": "uuid-string",
  "word": "book",
  "rank": 237,
  "coverage_pct": 78.5,
  "frequency_score": 0.0234,
  "band": 1,
  "grammar_info": {
    "part_of_speech": "noun",
    "classification": "noun, singular",
    "grammar_hint": "Use the correct word"
  },
  "frequency_description": "This word is among the 500 most frequent words in English.",
  "coverage_description": "Coverage up to here: 78% of word usage"
}
```

#### Get User Theme Performance
```http
GET /api/v1/insights/user/{user_id}/themes
```

**Parameters**:
- `user_id`: User identifier

**Response**:
```json
{
  "themes": [
    {
      "theme_id": "uuid-string",
      "name": "Daily actions",
      "attempts": 45,
      "correct": 38,
      "accuracy": 0.844,
      "avg_response_time_ms": 1250,
      "last_practiced_at": "2025-12-12T14:30:00Z",
      "difficulty_words": ["arrive", "leave", "stay"]
    },
    {
      "theme_id": "uuid-string",
      "name": "Travel",
      "attempts": 23,
      "correct": 16,
      "accuracy": 0.696,
      "avg_response_time_ms": 2100,
      "last_practiced_at": "2025-12-11T09:15:00Z",
      "difficulty_words": ["airport", "passport", "luggage"]
    }
  ]
}
```

#### Get User Daily Progress
```http
GET /api/v1/insights/user/{user_id}/daily
```

**Parameters**:
- `user_id`: User identifier
- `days` (optional, query): Number of days to include (default: 30)

**Response**:
```json
{
  "daily_stats": [
    {
      "date": "2025-12-12",
      "cards_answered": 25,
      "new_words_learned": 3,
      "reviews_done": 22,
      "accuracy": 0.80,
      "cumulative_mastered_words": 156
    },
    {
      "date": "2025-12-11",
      "cards_answered": 18,
      "new_words_learned": 2,
      "reviews_done": 16,
      "accuracy": 0.72,
      "cumulative_mastered_words": 153
    }
  ],
  "summary": {
    "total_days": 15,
    "avg_daily_cards": 22.3,
    "avg_accuracy": 0.76,
    "total_new_words": 28,
    "vocabulary_growth": 156
  }
}
```

#### Get Recent Performance
```http
GET /api/v1/insights/user/{user_id}/recent
```

**Parameters**:
- `user_id`: User identifier
- `responses` (optional, query): Number of recent responses to analyze (default: 30)

**Response**:
```json
{
  "recent_responses": [
    {
      "card_id": "uuid-string",
      "word": "book",
      "was_correct": true,
      "response_time_ms": 1450,
      "quality": 5,
      "timestamp": "2025-12-12T15:45:30Z"
    },
    {
      "card_id": "uuid-string",
      "word": "arrive",
      "was_correct": false,
      "response_time_ms": 3200,
      "quality": 2,
      "timestamp": "2025-12-12T15:42:15Z"
    }
  ],
  "metrics": {
    "accuracy_recent": 0.73,
    "avg_response_time_ms": 1825,
    "trend_direction": "improving",
    "session_cards": 15
  }
}
```

## TTS (Text-to-Speech) API

### Base URL
```
http://localhost:8001
```

### Generate Word Audio
```http
GET /api/tts/word/{card_id}?text={word}&lang={language}
```

**Parameters**:
- `card_id`: Card identifier
- `text`: Word to synthesize
- `lang`: Language code (en, pt, es, fr)

### Generate Sentence Audio
```http
GET /api/tts/sentence/{card_id}?text={sentence}&lang={language}
```

**Parameters**:
- `card_id`: Card identifier
- `text`: Full sentence to synthesize
- `lang`: Language code (en, pt, es, fr)

## Error Responses

### 404 Not Found
```json
{
  "error": "Resource not found",
  "message": "Card not found"
}
```

### 400 Bad Request
```json
{
  "error": "Invalid input",
  "message": "daily_new_limit must be between 5 and 20"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "message": "Database connection failed"
}
```

## Data Models

### MemoryStage
- `new`: Card never seen or 0 repetitions
- `learning`: Card with repetitions but interval < 21 days
- `review`: Card with interval >= 21 days and interval < 180 days
- `mature`: Card with interval >= 180 days

### SM-2 Algorithm
- Quality: 0-5 scale (5 = perfect response)
- Easiness Factor: 1.3 - 2.5 range
- Interval calculation based on repetitions and performance

## Voice Models
- **en**: lessac-glow_tts (female, American English)
- **pt**: pt_br_female-glow_tts (female, Brazilian Portuguese)
- **es**: es_male-glow_tts (male, Spanish neutral)
- **fr**: fr_FR-siwis-medium (female, French native voice from Piper TTS)
