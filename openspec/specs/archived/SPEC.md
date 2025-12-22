# FillTheWord - Especificação Funcional MVP

## Fluxos Principais do Usuário

### RF-01: Obter Próximo Cartão
**Usuário**: Obter um novo cartão com palavra oculta usando SRS SM-2  
**Sistema**: Selecionar cartão baseado em algoritmo SM-2 (ease_factor, interval, repetitions)

**Fluxo**:
1. Usuário clica "Next Card" ou inicia sessão
2. API GET `/api/cards/next`
3. System seleciona cartão baseado em:
   - Nível SM-2: new (0), learning (1), review (2), relearn (3), mature (4)
   - Prioridade: cartões due > novos > revisão
4. Return JSON: `{id, sentence_text, gap_start, gap_end, word_id, language, difficulty, grammar_hint}`
5. Frontend exibe: "The ___ is on the table" (gap visual)

**Algoritmo SM-2**:
- **new**: nunca revisado, apresentar primeiro
- **learning**: em fase de aprendizagem (intervalo < 7 dias)
- **review**: em fase de revisão (intervalo >= 7 dias)
- **relearn**: falhou recentemente, precisa reaprender
- **mature**: completamente aprendido (intervalo longo)

**Edge Cases**:
- Primeira sessão: selecionar cartões novos aleatoriamente
- Sem cartões disponíveis: exibir "Todos os cartões revisados!"
- Conexão offline: usar cache local de cards

### RF-02: Submeter Resposta
**Usuário**: Digitar palavra para preencher lacuna  
**Sistema**: Validar resposta com tolerância e registrar progresso SM-2

**Fluxo**:
1. Usuário digita palavra e clica "Check"
2. API POST `/api/cards/{id}/answer`
3. Body: `{answer: "book", response_time: 3.2}`
4. System valida com tolerância:
   - **Case insensitive**: "Book" = "book"
   - **Plural tolerance**: "books" aceito para "book" se contexto permitir
   - **Article tolerance**: "a book"/"the book" para "book"
   - **Synonym support**: "color"/"colour" baseado em sinônimos configurados
5. Return: `{correct: true, correct_answer: "book", user_answer: "book", pronunciation: "/bʊk/", sm2_update: {new_level: "learning", next_review: "2024-01-15T10:00:00Z"}}`
6. Frontend: feedback visual (✅ verde, ❌ vermelho) + hint se incorreto

**Tolerância de Resposta**:
```python
def is_correct(user_answer, correct_answer, context_hints):
    # Base comparison
    if normalize(user_answer) == normalize(correct_answer):
        return True
    
    # Plural tolerance
    if user_answer.strip().lower() == correct_answer.strip().lower() + 's':
        return is_plural_context(context_hints)
    
    # Article tolerance  
    if user_answer.strip().lower().endswith(correct_answer.strip().lower()):
        return is_article_context(user_answer.split()[0])
    
    # Synonym check
    return user_answer.strip().lower() in get_synonyms(correct_answer)
```

**Atualização SM-2**:
- **Success (correct)**: 
  - `repetitions += 1`
  - `ease_factor = max(1.3, ease_factor + 0.1)`
  - `interval = floor(interval * ease_factor)` se repetitions > 1
  - `next_review = now + interval days`
- **Failure (incorrect)**:
  - `repetitions = 0`
  - `ease_factor = max(1.3, ease_factor - 0.2)`
  - `interval = 1`
  - `next_review = now + 1 day`

### RF-03: Reproduzir Áudio TTS Local
**Usuário**: Ouvir pronúncia da frase completa ou palavra isolada  
**Sistema**: Gerar/stream áudio usando TTS local com cache em disco

**Fluxo Frase**:
1. Usuário clica ícone de áudio da frase
2. API GET `/api/tts/sentence/{id}`
3. System:
   - Check cache disco: `audio/<language>/sentence/<slug>.wav`
   - Generate se missing via Coqui/Piper TTS
   - Cache em disco para uso futuro
4. Return: `{audio_url: "/api/audio/en/sentence/book_on_table.wav", duration_ms: 2500}`
5. Frontend: reproduzir áudio imediatamente

**Fluxo Palavra**:
1. Usuário clica ícone de áudio da palavra
2. API GET `/api/tts/word/{id}`
3. Sistema similar com cache: `audio/<language>/word/<slug>.wav`
4. Return: `{audio_url: "/api/audio/en/word/book.wav", duration_ms: 800, pronunciation: "/bʊk/"}`

**Cache de Áudio em Disco**:
```
audio/
├── en/
│   ├── sentence/
│   │   ├── book_on_table.wav
│   │   ├── cat_sleeping.wav
│   │   └── ...
│   └── word/
│       ├── book.wav
│       ├── cat.wav
│       └── ...
├── pt/
│   ├── sentence/
│   └── word/
└── es/
    ├── sentence/
    └── word/
```

**Performance**:
- **Cache hit**: < 50ms (static file serving)
- **TTS generation**: 500-1500ms (primeira vez)
- **Arquivo médio**: 50-200KB (WAV, 22kHz, mono)
- **Cache permanente**: Sem TTL, remover manualmente se necessário

**TTS Voices por Idioma**:
```yaml
voices:
  en: "lessac-glow_tts"      # Inglês americano claro
  pt: "pt_br_female-glow_tts" # Português brasileiro
  es: "es_male-glow_tts"     # Espanhol neutro
```

## Requisitos Não Funcionais (MVP)

### Performance
- API response < 200ms (card selection)
- TTS generation < 2s (first time)
- Audio cache hit < 50ms
- Frontend load < 1s

### Confiabilidade
- Funciona offline após setup inicial
- Cache de áudio persistente
- Dados locais seguros (PostgreSQL)

### Usabilidade
- Interface intuitiva e focada
- Feedback imediato de respostas
- Teclado navigation completo
- Mobile responsive

### Acessibilidade
- TTS para todo conteúdo
- Interface WCAG 2.1 AA
- Suporte a leitores de tela
- Controles de teclado

## Implementação de Dicas Contextuais

### Grammar Hints
Dicas gramaticais para ajudar o usuário:

```json
{
  "grammar_hint": "Use article 'the' for specific things",
  "context_type": "determiner",
  "example": "The book (not just any book)"
}
```

### Difficulty Levels
- **Nível 1**: Palavras comuns, estrutura simples
- **Nível 2**: Vocabulário intermediário
- **Nível 3**: Estrutura complexa, menos comum
- **Nível 4**: Avançado, múltiplos significados
- **Nível 5**: Especializado, difícil

### Synonym Support
```json
{
  "word": "color",
  "synonyms": ["colour"],
  "accepted_variations": ["color", "colour"]
}
```

## Sistema SM-2 Detalhado

### Níveis de Aprendizagem
1. **New (0)**: Nunca visto, primeira apresentação
2. **Learning (1)**: Em aprendizagem ativa, intervalos curtos
3. **Review (2)**: Em fase de revisão, intervalos médios
4. **Relearn (3)**: Falhou recentemente, reaprendendo
5. **Mature (4)**: Dominado, intervalos longos

### Fórmulas SM-2
```python
# Success
new_interval = min(
    current_interval * ease_factor,
    180  # max 180 days
)
new_repetitions = current_repetitions + 1
new_ease_factor = min(
    current_ease_factor + 0.1,
    2.5  # max ease factor
)

# Failure
new_interval = 1
new_repetitions = 0
new_ease_factor = max(
    current_ease_factor - 0.2,
    1.3  # min ease factor
)
```

### Card Selection Priority
1. Cartões due (next_review <= now) ordenados por: due date
2. Cartões novos ordenados por: difficulty (easy first)
3. Cartões de revisão ordenados por: last_review + interval

### Example Response
```json
{
  "card": {
    "id": "card-123",
    "sentence": "The ___ is on the table.",
    "gap_start": 4,
    "gap_end": 4,
    "word": "book",
    "language": "en",
    "difficulty": 2,
    "grammar_hint": "Use a noun for furniture"
  },
  "progress": {
    "sm2_level": "learning",
    "repetitions": 3,
    "ease_factor": 2.3,
    "interval_days": 7,
    "next_review": "2024-01-18T10:00:00Z"
  }
}
```
