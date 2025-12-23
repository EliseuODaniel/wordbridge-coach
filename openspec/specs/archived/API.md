# FillTheWord - API Specification MVP

## Base URL
- Development: `http://localhost:8000`
- Production: `http://localhost:8000` (local deployment)

## Authentication
MVP não requer autenticação. Todos os endpoints são públicos.

## Core Endpoints

### Cards

#### GET /api/cards/next
Obtém próximo cartão para estudo baseado em algoritmo SM-2.

**Query Parameters**:
- `language` (string, optional): Idioma dos cards ("en", "pt", "es"). Default: "en"
- `difficulty_min` (int, optional): Dificuldade mínima (1-5). Default: 1
- `difficulty_max` (int, optional): Dificuldade máxima (1-5). Default: 5
- `deck_id` (UUID, optional): ID do deck específico

**Response (200)**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "sentence_text": "The ___ is on the table.",
  "word_id": "550e8400-e29b-41d4-a716-446655440001",
  "gap_start": 4,
  "gap_end": 4,
  "language": "en",
  "difficulty": 2,
  "grammar_hint": "Use a noun for furniture",
  "context_type": "determiner",
  "progress": {
    "sm2_level": "learning",
    "repetitions": 3,
    "ease_factor": 2.3,
    "interval_days": 7,
    "last_review": "2024-01-10T14:30:00Z",
    "next_review": "2024-01-17T14:30:00Z",
    "total_reviews": 8,
    "correct_reviews": 6,
    "accuracy_rate": 0.75
  }
}
```

**Error Responses**:
- `404`: "No cards available for the specified criteria"
- `400`: "Invalid difficulty range"

**Selection Algorithm**:
1. Cartões due para revisão (`next_review <= now`) ordenados por `next_review`
2. Se nenhum due: cartões novos ordenados por `difficulty` (fácil primeiro)
3. Filtra por `language`, `difficulty_range`, `deck_id` se especificado

#### POST /api/cards/{card_id}/answer
Submete resposta do usuário e atualiza progresso SM-2.

**Path Parameters**:
- `card_id` (UUID): ID do cartão

**Request Body**:
```json
{
  "answer": "book",
  "response_time": 2.5
}
```

**Response (200)**:
```json
{
  "correct": true,
  "correct_answer": "book",
  "user_answer": "book",
  "pronunciation": "/bʊk/",
  "grammar_feedback": null,
  "sm2_update": {
    "previous_level": "learning",
    "current_level": "review",
    "repetitions": 4,
    "ease_factor": 2.4,
    "interval_days": 17,
    "next_review": "2024-01-27T14:30:00Z",
    "accuracy_improvement": "+0.05"
  },
  "audio_urls": {
    "word_audio": "/api/tts/word/550e8400-e29b-41d4-a716-446655440001",
    "sentence_audio": "/api/tts/sentence/550e8400-e29b-41d4-a716-446655440000"
  }
}
```

**Error Responses**:
- `404`: "Card not found"
- `400`: "Invalid answer format" (empty answer, too long, etc.)

**Answer Validation Rules**:
- Case insensitive: "Book" = "book"
- Plural tolerance: "books" aceito se contexto permitir
- Article tolerance: "a book"/"the book" aceito como "book"
- Synonym support: "color"/"colour" baseado em sinônimos configurados
- Whitespace trimming: "  book  " → "book"

**SM-2 Update Logic**:
```python
if correct:
    progress.repetitions += 1
    progress.ease_factor = min(2.5, progress.ease_factor + 0.1)
    if progress.repetitions == 1:
        progress.interval_days = 1
    elif progress.repetitions == 2:
        progress.interval_days = 6
    else:
        progress.interval_days = min(180, progress.interval_days * progress.ease_factor)
else:
    progress.repetitions = 0
    progress.interval_days = 1
    progress.ease_factor = max(1.3, progress.ease_factor - 0.2)
```

### TTS (Text-to-Speech)

#### GET /api/tts/sentence/{sentence_id}
Obtém áudio TTS da frase completa com cache em disco.

**Path Parameters**:
- `sentence_id` (UUID): ID implícito do card (usa sentence do card)

**Query Parameters**:
- `voice` (string, optional): Override default voice model
- `speed` (float, optional): Speed multiplier (0.5-2.0). Default: 1.0

**Response (200)**:
```json
{
  "audio_url": "/api/audio/en/sentence/abc123def456.wav",
  "duration_ms": 2500,
  "voice": "lessac-glow_tts",
  "cache_status": "hit",  // "hit" or "generated"
  "sentence_text": "The book is on the table.",
  "language": "en"
}
```

**Cache Logic**:
1. Check cache disco: `audio/<language>/sentence/<hash>.wav`
2. Se existe e is newer than 0 days: return cache hit
3. Se não existe: generate via TTS service, save to disk, return generated

**Error Responses**:
- `404`: "Sentence not found"
- `500`: "TTS generation failed"
- `503`: "TTS service unavailable"

#### GET /api/tts/word/{word_id}
Obtém áudio TTS da palavra isolada.

**Path Parameters**:
- `word_id` (UUID): ID da palavra

**Query Parameters**:
- `voice` (string, optional): Override default voice model
- `speed` (float, optional): Speed multiplier (0.5-2.0). Default: 1.0

**Response (200)**:
```json
{
  "audio_url": "/api/audio/en/word/def456ghi789.wav",
  "duration_ms": 800,
  "pronunciation": "/bʊk/",
  "voice": "lessac-glow_tts",
  "cache_status": "hit",
  "word_text": "book",
  "language": "en"
}
```

**Cache Logic**: Similar ao sentence TTS, usando path `audio/<language>/word/<hash>.wav`

#### GET /api/audio/{language}/{type}/{hash}.wav
Static file serving para áudio cacheado (servido diretamente pelo framework).

**Path Parameters**:
- `language` (string): "en", "pt", "es"
- `type` (string): "sentence", "word"  
- `hash` (string): MD5 hash do texto+voice

**Response**: Audio file (WAV format, 22kHz, mono)
**Headers**: 
- `Content-Type: audio/wav`
- `Cache-Control: max-age=31536000` (1 year cache)

### Content Discovery

#### GET /api/decks
Lista todos os decks disponíveis.

**Query Parameters**:
- `language` (string, optional): Filtrar por idioma
- `difficulty` (int, optional): Filtrar por nível de dificuldade

**Response (200)**:
```json
{
  "decks": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440003",
      "name": "Daily English",
      "language": "en",
      "difficulty_level": 2,
      "description": "Common everyday vocabulary",
      "card_count": 150,
      "is_active": true
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440004",
      "name": "Business Vocabulary",
      "language": "en", 
      "difficulty_level": 4,
      "description": "Professional business terms",
      "card_count": 80,
      "is_active": true
    }
  ]
}
```

#### GET /api/languages
Lista todos os idiomas suportados.

**Response (200)**:
```json
{
  "languages": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440005",
      "code": "en",
      "name": "English",
      "voice_model": "lessac-glow_tts",
      "is_active": true,
      "deck_count": 3,
      "card_count": 500
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440006",
      "code": "pt",
      "name": "Português", 
      "voice_model": "pt_br_female-glow_tts",
      "is_active": true,
      "deck_count": 1,
      "card_count": 200
    }
  ]
}
```

### System Status

#### GET /api/health
Health check básico do sistema.

**Response (200)**:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2024-01-10T14:30:00Z",
  "services": {
    "database": "connected",
    "tts_service": "available",
    "audio_cache": "accessible"
  },
  "stats": {
    "total_cards": 700,
    "active_decks": 4,
    "cache_size_mb": 45,
    "last_updated": "2024-01-10T10:15:00Z"
  }
}
```

#### GET /api/stats/overview
Estatísticas gerais do app (MVP simples).

**Response (200)**:
```json
{
  "total_cards": 700,
  "cards_reviewed": 125,
  "accuracy_rate": 0.78,
  "cards_due_today": 8,
  "cards_new": 75,
  "cards_learning": 25,
  "cards_review": 15,
  "cards_mature": 10,
  "study_streak_days": 3,
  "avg_response_time": 2.8
}
```

## Error Handling

### Standard Error Response Format
```json
{
  "error": {
    "code": "CARD_NOT_FOUND",
    "message": "Requested card does not exist",
    "details": {
      "card_id": "550e8400-e29b-41d4-a716-446655440000"
    },
    "timestamp": "2024-01-10T14:30:00Z"
  }
}
```

### Common HTTP Status Codes
- `200`: Success
- `400`: Bad Request (validation error)
- `404`: Not Found
- `500`: Internal Server Error
- `503`: Service Unavailable (TTS service down)

### Error Codes Reference
- `CARD_NOT_FOUND`: Card ID não existe
- `INVALID_DIFFICULTY_RANGE`: difficulty_min > difficulty_max ou fora de 1-5
- `EMPTY_ANSWER`: Resposta vazia
- `TTS_GENERATION_FAILED`: Falha ao gerar áudio
- `AUDIO_CACHE_ERROR`: Problema com cache de áudio

## Performance Specifications

### Response Time Targets
- **Card selection**: < 100ms (database query)
- **Answer processing**: < 50ms (validation + SM-2 update)
- **TTS cache hit**: < 20ms (static file serving)
- **TTS generation**: < 1500ms (first time only)
- **Health check**: < 10ms

### Cache Strategy
- **Audio files**: Permanent cache em disco
- **Database queries**: Connection pooling, indexes otimizados
- **Static files**: Long-term browser cache (1 year)

### Scalability Considerations
- Single-user MVP: sem necessidade de rate limiting
- Local deployment: recursos limitados pela máquina local
- Cache growth: Monitorar uso de disco para áudio cache

## Example API Flow

### Complete Study Session Flow
```bash
# 1. Get next card
curl "http://localhost:8000/api/cards/next?language=en"

# 2. Submit answer
curl -X POST "http://localhost:8000/api/cards/{card_id}/answer" \
  -H "Content-Type: application/json" \
  -d '{"answer": "book", "response_time": 2.5}'

# 3. Get word audio (optional)
curl "http://localhost:8000/api/tts/word/{word_id}"

# 4. Get sentence audio (optional) 
curl "http://localhost:8000/api/tts/sentence/{card_id}"

# 5. Play audio files
curl "http://localhost:8000/api/audio/en/word/abc123.wav" --output word.wav
curl "http://localhost:8000/api/audio/en/sentence/def456.wav" --output sentence.wav

# 6. Get next card (repeat loop)
curl "http://localhost:8000/api/cards/next?language=en"
```

## Integration Notes

### Frontend Integration
- Usar `axios` ou `fetch` para chamadas API
- Implementar retry logic para TTS generation (503 errors)
- Cache audio URLs no frontend para evitar requests duplicados
- Usar `HTMLAudioElement` para reproduzir arquivos WAV

### TTS Service Integration
- TTS service roda em container separado (port 8001)
- API service faz HTTP requests para TTS service
- Implementar fallback voice se primary voice falhar
- Configurar timeout de 30 segundos para TTS generation

### Database Integration
- Usar SQLAlchemy com connection pooling
- Implementar indexes otimizados para queries frequentes
- Considerar read replicas se performance se tornar problema
- Backup diário dos dados (PostgreSQL pg_dump)
