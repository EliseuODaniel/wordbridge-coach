# FillTheWord - Modelo de Domínio Completo

## Visão Geral
Modelo de domínio completo incluindo todas as entidades do texto-base com algoritmo SM-2 completo e entidades User/UserCardState/ReviewEvent.

## Entidades Principais
### Language
Idiomas suportados pelo sistema com configurações de TTS específicas.

**Attributes**:
- `id` (UUID, PK)
- `code` (string, unique) - Ex: "en", "pt", "es", "fr"
- `name` (string) - Ex: "English", "Português", "Español", "Français"
- `voice_model` (string) - Coqui/Piper TTS voice name
- `voice_type` (string) - "male", "female", "neutral"
- `is_active` (boolean)
- `created_at` (datetime)

**Idiomas Suportados (texto-base)**:
- **EN (English)**: 
  - Voice: "lessac-glow_tts" (American English clear)
  - Code: "en"
  - Voice Type: "female"
  
- **ES (Español)**:
  - Voice: "es_male-glow_tts" (Spanish neutral)
  - Code: "es" 
  - Voice Type: "male"

- **FR (Français)**:
  - Voice: "fr_female-glow_tts" (French standard)
  - Code: "fr"
  - Voice Type: "female"

- **PT (Português)**:
  - Voice: "pt_br_female-glow_tts" (Portuguese Brazilian)
  - Code: "pt"
  - Voice Type: "female"

**Invariants**:
- Language code deve ser ISO 639-1 (2 letras)
- Não pode deletar se houver cards associados ativos
- Apenas idiomas com modelos TTS disponíveis podem estar ativos
Categorias de conteúdo organizadas por dificuldade e tópico.

**Attributes**:
- `id` (UUID, PK)
- `name` (string) - Ex: "Daily English", "Business Vocabulary"
- `language_id` (UUID, FK)
- `difficulty_level` (int, 1-5)
- `description` (string, optional)
- `card_count` (int, computed)
- `is_active` (boolean)
- `created_at` (datetime)

**Invariants**:
- difficulty_level deve ser 1-5
- Deve ter pelo menos um card associado para estar ativo

### Word
Vocabulário individual usado nas frases com campos adicionais do texto-base.

**Attributes**:
- `id` (UUID, PK)
- `lemma` (string) - Forma base do dicionário (ex: "book", "run", "beautiful")
- `text` (string, unique by language) - Forma específica usada na frase
- `part_of_speech` (enum) - noun, verb, adjective, adverb, preposition, etc.
- `features` (JSON) - Propriedades gramaticais específicas do idioma
- `language_id` (UUID, FK)
- `pronunciation` (string, optional) - IPA notation
- `pt_translation` (string, optional) - Tradução PT-BR da palavra (ex: "book" → "livro") - ⚠️ NOVO (Lingvist mode)
- `frequency_rank` (int, optional) - Common word frequency (1=most common)
- `audio_path` (string, optional) - Path to cached TTS audio
- `difficulty` (int, 1-5) - Derived from frequency and complexity
- `created_at` (datetime)

**Part of Speech Values**:
- `noun`: Substantivos (book, table, cat)
- `verb`: Verbos (run, eat, study)
- `adjective`: Adjetivos (beautiful, big, red)
- `adverb`: Advérbios (quickly, very, here)
- `preposition`: Preposições (in, on, at)
- `article`: Artigos (a, an, the)
- `pronoun`: Pronomes (he, she, it)
- `conjunction`: Conjunções (and, but, or)

**Features Examples (JSON)**:
```json
// Noun
{
  "number": "singular|plural",
  "gender": "masculine|feminine|neuter",
  "countable": true,
  "proper": false
}

// Verb
{
  "tense": "present|past|future",
  "aspect": "simple|continuous|perfect",
  "transitive": true,
  "regular": true
}

// Adjective
{
  "degree": "positive|comparative|superlative",
  "position": "attributive|predicative"
}
```

**Invariants**:
- lemma deve ser a forma base do dicionário
- part_of_speech deve ser um valor válido
- text deve ser único por idioma
- difficulty deve ser 1-5
### Sentence
Frases usadas nos cartões, com tradução associada.

**Attributes**:
- `id` (UUID, PK)
- `text` (string) - Frase completa
- `translation` (string) - Tradução da frase
- `word_id` (UUID, FK) - Palavra target da lacuna
- `language_id` (UUID, FK)
- `type` (enum) - "example", "usage", "definition"
- `difficulty` (int, 1-5)
- `audio_path` (string, optional) - Path to cached TTS audio
- `gap_start` (int) - Posição inicial da lacuna
- `gap_end` (int) - Posição final da lacuna
- `created_at` (datetime)

**Invariants**:
- gap_start < gap_end
- gap_end <= len(text)
- Frase deve conter exatamente uma lacuna

### Card
Cartão de estudo com lacuna para preenchimento.

**Attributes**:
- `id` (UUID, PK)
- `sentence_id` (UUID, FK)
- `deck_id` (UUID, FK)
- `grammar_hint` (string) - Dica gramatical sobre a palavra
- `difficulty` (int, 1-5)
- `position` (int) - Posição da lacuna (legacy, usar gap_start/gap_end)
- `gap_start` (int) - Índice inicial da lacuna
- `gap_end` (int) - Índice final da lacuna
- `is_active` (boolean)
- `created_at` (datetime)

**Derived Fields**:
- `sentence_with_gap` - Texto com lacuna visual: "The ___ is on the table"
- `target_word` - Palavra que preenche a lacuna
- `context_before` - Texto antes da lacuna
- `context_after` - Texto depois da lacuna

**Invariants**:
- deck_id deve apontar para deck ativo
- gap_start < gap_end
- grammar_hint deve ser útil não vaga

### User
Usuário do sistema para controle de progresso individual com idiomas configurados.

**Attributes**:
- `id` (UUID, PK)
- `username` (string, unique)
- `email` (string, unique, optional)
- `password_hash` (string, optional)
- `native_language_id` (UUID, FK Language) - **Idioma nativo do usuário**
- `target_language_id` (UUID, FK Language) - **Idioma que está aprendendo**
- `language_preference` (string, default "en") - Interface language
- `word_goal_rank` (int, default 100) - **Objetivo de vocabulário** Spec4: {100, 500, 1500, 3000, 5000, 10000}
- `daily_new_limit` (int, default 10)
- `easiness_factor` (float, default 2.5)
- `mode` (string, default "spec4") - **Modo de aprendizado**: "spec4" | "lingvist"
  - "spec4": Scheduler SM-2 clássico com 25% new / 75% review fixo
  - "lingvist": Scheduler adaptativo com relearn queue + new_share dinâmico
- `accuracy_last_20` (float, optional) - **Accuracy das últimas 20 respostas** (0.0-1.0)
  - Usado para ajustar new_share no modo lingvist
  - Null se usuário tem menos de 20 respostas
- `created_at` (datetime)
- `last_login` (datetime, optional)

**Language Combinations Suportadas**:
- **EN Learners**: native_language="pt/es/fr", target_language="en"
- **PT Learners**: native_language="en/es/fr", target_language="pt"  
- **ES Learners**: native_language="en/pt/fr", target_language="es"
- **FR Learners**: native_language="en/pt/es", target_language="fr"

**Settings**:
- `new_cards_per_day`: 5-20 (default: 10)
- `auto_play_audio`: boolean (default: true)
- `show_hints`: boolean (default: true)
- `keyboard_shortcuts`: boolean (default: true)
- `grammar_hints`: boolean (default: true)
- `translation_enabled`: boolean (default: true)

**Invariants**:
- username deve ser único
- native_language != target_language
- native_language e target_language devem ser idiomas suportados
- daily_new_limit deve ser 1-50
- easiness_factor deve ser 1.3-2.5

### UserCardState
Estado individual do cartão para cada usuário com algoritmo SM-2 completo.

**Attributes**:
- `id` (UUID, PK)
- `user_id` (UUID, FK)
- `card_id` (UUID, FK)
- `repetitions` (int, default 0) - Número de repetições corretas
- `easiness_factor` (float, default 2.5) - Fator de facilidade SM-2
- `interval_days` (int, default 1) - Intervalo em dias
- `next_review_at` (datetime) - Próxima revisão
- `last_reviewed_at` (datetime, optional) - Última revisão
- `status` (enum) - "new", "learning", "review", "relearn", "mature"
- `total_reviews` (int, default 0) - Total de revisões
- `correct_reviews` (int, default 0) - Revisões corretas
- `is_relearn` (boolean, default false) - **Está na fila de relearn?** (Lingvist mode)
  - True: quality < 3, precisa revisar em minutos
  - False: seguindo scheduler SM-2 normal
- `relearn_due` (datetime, optional) - **Quando revisar novamente** (Lingvist mode)
  - Setado quando is_relearn = true
  - Intervalos progressivos: 10min → 30min → 2h → 6h → 24h
- `created_at` (datetime)
- `updated_at` (datetime)

**SM-2 Status Mapping**:
- **new**: repetitions = 0, nunca revisado
- **learning**: repetitions < 3, interval < 7 dias
- **review**: repetitions >= 3, interval >= 7 dias
- **relearn**: falhou após ser review/mature
- **mature**: interval >= 21 dias

**Invariants**:
- easiness_factor >= 1.3
- interval_days >= 1
- next_review_at >= last_reviewed_at

### ReviewEvent
Registro individual de cada sessão de revisão para analytics e ajuste SM-2.

**Attributes**:
- `id` (UUID, PK)
- `user_id` (UUID, FK)
- `card_id` (UUID, FK)
- `sentence_id` (UUID, FK, nullable) - **Qual frase foi usada** (Spec4: sempre preenchido para variedade)
- `quality` (int, 0-5) - Qualidade da resposta SM-2
- `response_time_ms` (int) - Tempo de resposta em milissegundos
- `user_answer` (string) - Resposta do usuário
- `correct_answer` (string) - Resposta correta
- `was_correct` (boolean) - Se a resposta estava correta
- `hints_used` (int, default 0) - Quantidade de dicas usadas
- `attempts` (int, default 1) - **Número de tentativas** para acertar - ⚠️ NOVO
- `typed_answer` (string, nullable) - Resposta digitada no modo Lingvist - ⚠️ NOVO
- `hints_used_lingvist` (JSON, nullable) - Hints usados no modo Lingvist - ⚠️ NOVO
- `attempt_index` (int, default 1) - Índice da tentativa (1ª, 2ª, 3ª...) - ⚠️ NOVO
- `previous_easiness` (float) - Easiness factor antes da revisão
- `new_easiness` (float) - Easiness factor após revisão
- `previous_interval` (int) - Intervalo antes da revisão
- `new_interval` (int) - Intervalo após revisão
- `session_id` (UUID, optional) - ID da sessão de estudo
- `created_at` (datetime)

**SM-2 Quality Scale**:
- **0**: Falha completa (esquecimento total)
- **1**: Falha com algum reconhecimento
- **2**: Falha mas lembrada com hesitação
- **3**: Resposta correta com dificuldade
- **4**: Resposta correta com alguma hesitação
- **5**: Resposta perfeita e rápida

**Invariants**:
- quality deve ser 0-5
- response_time_ms > 0
- previous_easiness/new_easiness >= 1.3
- **Spec4**: `sentence_id` deve ser preenchido sempre que possível (para variedade de frases)
- **Lingvist**: `typed_answer` deve ser preenchido, `hints_used_lingvist` rastreia hints progressivos

**Examples (Lingvist mode)**:
```json
{
  "typed_answer": "box",
  "hints_used_lingvist": {
    "grammar_tag": true,
    "length_mask": true,
    "first_letter": true,
    "revealed_letters": "b _ _ k",
    "translation": true,
    "semantic": false
  },
  "attempt_index": 3
}
```

## Algoritmo SM-2 Completo

### Cálculo do Próximo Intervalo

```python
def calculate_sm2_next(quality, repetitions, easiness_factor, interval_days):
    """
    Calculate next SM-2 values based on quality (0-5)
    """
    # Update easiness factor
    easiness_factor = max(1.3, easiness_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
    
    # Update repetitions and interval
    if quality < 3:
        # Failed review - reset repetitions
        repetitions = 0
        interval_days = 1
    else:
        # Successful review
        repetitions += 1
        
        if repetitions == 1:
            interval_days = 1
        elif repetitions == 2:
            interval_days = 6
        else:
            interval_days = round(interval_days * easiness_factor)
    
    # Update status
    if repetitions == 0:
        status = "relearn"
    elif repetitions < 3 and interval_days < 7:
        status = "learning"
    elif repetitions >= 3 and interval_days >= 7 and interval_days < 21:
        status = "review"
    else:
        status = "mature"
    
    return {
        "repetitions": repetitions,
        "easiness_factor": easiness_factor,
        "interval_days": interval_days,
        "next_review_at": datetime.now() + timedelta(days=interval_days),
        "status": status
    }
```

### Lógica de Seleção de Cartões

```python
def select_next_card(user_id, daily_new_limit):
    """
    Select next card based on SM-2 priorities
    """
    # Priority 1: Due cards for review
    due_cards = UserCardState.objects.filter(
        user_id=user_id,
        next_review_at__lte=now(),
        status__in=["review", "relearn", "mature"]
    ).order_by('next_review_at')
    
    if due_cards.exists():
        return due_cards.first()
    
    # Priority 2: New cards (respect daily limit)
    new_today_count = ReviewEvent.objects.filter(
        user_id=user_id,
        card__usercardstate__status="new",
        created_at__date=today()
    ).count()
    
    if new_today_count < daily_new_limit:
        new_cards = UserCardState.objects.filter(
            user_id=user_id,
            status="new"
        ).order_by('?').first()
        
        if new_cards:
            return new_cards
    
    # Priority 3: Learning cards
    learning_cards = UserCardState.objects.filter(
        user_id=user_id,
        status="learning"
    ).order_by('next_review_at').first()
    
    return learning_cards
```

## Relacionamentos

### Diagrama Simplificado
```
User (1) ──── (N) UserCardState (N) ──── (1) Card
  │                                      │
  │                                      │
  └── (N) ReviewEvent (N) ───────────────┘
                      │
                      │
               Sentence (1) ──── (N) Word
                      │
                      │
                   Deck (N)
```

### Key Relationships
- User → UserCardState (1:N): Cada usuário tem estado por cartão
- Card → UserCardState (1:N): Cada cartão tem estado por usuário
- UserCardState → ReviewEvent (1:N): Cada revisão gera evento
- Card → Sentence (1:1): Cada cartão tem uma frase
- Sentence → Word (N:1): Várias frases podem usar mesma palavra (via `Sentence.word_id`)
- Sentence → Deck (N:1): Frases pertencem a um deck
- Word → WordSentence (1:N): Palavra pode ter múltiplos mapeamentos para sentenças (Spec4)
- Sentence → WordSentence (N:M): Sentença pode ser mapeada para múltiplas palavras (Spec4)

## Entidades Spec4 (Progressão de Vocabulário)

### WordSentence
Tabela de relacionamento N:M entre Word e Sentence para suportar múltiplas frases por palavra.

**Attributes**:
- `id` (UUID, PK)
- `word_id` (UUID, FK Word.id)
- `sentence_id` (UUID, FK Sentence.id)
- `is_primary` (boolean, default False) - Marca a frase principal da palavra
- `created_at` (datetime)

**Invariants**:
- Apenas um WordSentence por word pode ter `is_primary=True`
- Deve existir Card correspondente para cada Sentence mapeada

### UserFrequencyProgress
Progresso do usuário no vocabulário ordenado por frequência (Spec4: janela dinâmica).

**Attributes**:
- `id` (UUID, PK)
- `user_id` (UUID, FK User.id, unique)
- `word_goal_rank` (int) - Objetivo final do usuário: {100, 500, 1500, 3000, 5000, 10000}
- `current_window_end_rank` (int) - Fim da janela atual de vocabulário ativo (ex: 100, 200, 300...)
- `max_contiguous_mastered_rank` (int) - Maior rank tal que TODAS as palavras 1..rank foram acertadas ≥1 vez
- `created_at` (datetime)
- `updated_at` (datetime)

**Exemplo de Progressão**:
```
Inicial: word_goal_rank=500, current_window_end_rank=100, max_contiguous_mastered_rank=0
Após acertar rank 1: max_contiguous_mastered_rank=1
Após acertar ranks 1..100: max_contiguous_mastered_rank=100 → window expande para 200
Após acertar ranks 1..200: max_contiguous_mastered_rank=200 → window expande para 300
...
```

**Invariants**:
- `current_window_end_rank <= word_goal_rank`
- `max_contiguous_mastered_rank <= current_window_end_rank`
- `max_contiguous_mastered_rank` avança apenas contiguamente (sem buracos)

### UserSessionStats
Estatísticas diárias de sessão para controle de mix novas/revisões (Spec4).

**Attributes**:
- `id` (UUID, PK)
- `user_id` (UUID, FK User.id)
- `date` (date) - Data da sessão (YYYY-MM-DD)
- `cards_shown` (int, default 0) - Total de cards mostrados
- `new_cards_shown` (int, default 0) - Cards novos mostrados
- `created_at` (datetime)
- `updated_at` (datetime)

**Fórmula de Mix (Spec4)**:
```
new_share = new_cards_shown / cards_shown
target_new_share = 0.25  # 25%

Se new_share < target_new_share: introduzir palavra nova
Senão: priorizar revisões
```

**Invariants**:
- `new_cards_shown <= cards_shown`
- Uma entrada por `(user_id, date)`

## Entidades Chat Coach (Conversacional com Real-time Feedback)

**Status**: 📝 Proposed (see [change proposal](../changes/2025-12-chat-coach-mode-v1.md))

### ChatConversation
Conversa entre aluno e professor (AI). Contém metadados da sessão, perfil do aluno e objetivos pedagógicos atuais.

**Attributes**:
- `id` (UUID, PK)
- `user_id` (UUID, FK → User.id)
- `title` (string) - Título da conversa (ex: "Practice Past Simple")
- `student_profile_json` (JSONB) - Perfil do aluno com CEFR estimado e erros comuns
  ```json
  {
    "cefr_level": "A2",
    "common_errors": ["past_simple", "articles", "prepositions"],
    "strengths": ["vocabulary", "basic_fluency"],
    "weaknesses": ["grammar", "irregular_verbs"]
  }
  ```
- `lesson_frame_json` (JSONB) - Objetivo pedagógico do turno atual (ver schema abaixo)
- `session_summary` (text) - Resumo incremental do que aconteceu na conversa
- `created_at` (timedatezone)
- `updated_at` (timedatezone)

**Indexes**:
- `idx_chat_conversations_user_id` on `user_id`
- `idx_chat_conversations_created_at` on `created_at DESC`

**Invariants**:
- `user_id` deve existir em `users`
- `lesson_frame_json` deve conter todos os campos obrigatórios do Lesson Frame
- Título default = "New Chat" se não fornecido

### ChatMessage
Mensagem individual dentro de uma conversa (user, assistant, or system).

**Attributes**:
- `id` (UUID, PK)
- `conversation_id` (UUID, FK → ChatConversation.id, ON DELETE CASCADE)
- `role` (enum) - "system" | "user" | "assistant"
- `content` (text) - Conteúdo da mensagem
- `metadata_json` (JSONB, optional) - Metadados extras
  ```json
  {
    "lesson_frame_snapshot": { ... },
    "scores": { "grammar": 80, "spelling": 100 },
    "tokens": 150
  }
  ```
- `created_at` (timedatezone)

**Indexes**:
- `idx_chat_messages_conversation_id` on `conversation_id`
- `idx_chat_messages_created_at` on `created_at ASC`

**Invariants**:
- `conversation_id` deve existir em `chat_conversations`
- `role` deve ser um dos valores válidos
- Primeira mensagem sempre é "system" (prompt inicial)
- Mensagens "user" e "assistant" devem alternar (não duas user seguidas)

**Important**: `draft_update` events **NÃO** são persistidos (são efêmeros, só para feedback em tempo real). Apenas mensagens finais são salvas.

### ChatLessonHistory (Opcional, Fase 2)
Histórico de Lesson Frames por conversa para análise de progresso pedagógico.

**Attributes**:
- `id` (UUID, PK)
- `conversation_id` (UUID, FK → ChatConversation.id)
- `lesson_frame_json` (JSONB) - Snapshot do Lesson Frame em um ponto no tempo
- `created_at` (timedatezone)

**Invariants**:
- Uma entrada por mudança significativa de Lesson Frame
- Útil para analytics: "Como os objetivos pedagógicos evoluíram durante a conversa?"

### Lesson Frame Schema (JSON)
Estrutura JSON para `lesson_frame_json` (usado em ChatConversation e ChatLessonHistory):

```typescript
interface LessonFrame {
  cefr_target: "A1" | "A2" | "B1" | "B2" | "C1" | "C2";
  learning_goal: string;        // ex: "past_simple_regular_verbs"
  expected_intent: string;       // ex: "describe_recent_activity"
  topic: string;                 // ex: "weekend_plans"
  rubric: {
    grammar: string[];           // ex: ["past_tense_consistency"]
    vocab: string[];             // ex: ["yesterday", "last_weekend"]
    style: string[];             // ex: ["short_clear_sentences"]
  };
  scoring_hints: {
    avoid: string[];             // ex: ["present_continuous_for_past"]
    encourage: string[];         // ex: ["time_markers", "regular_-ed"]
  };
}
```

**Exemplo Completo**:
```json
{
  "cefr_target": "A2",
  "learning_goal": "past_simple_regular_verbs",
  "expected_intent": "describe_recent_activity",
  "topic": "weekend_plans",
  "rubric": {
    "grammar": [
      "past_tense_consistency",
      "article_usage",
      "subject_verb_agreement"
    ],
    "vocab": [
      "yesterday",
      "last_weekend",
      "went",
      "visited",
      "played"
    ],
    "style": [
      "short_clear_sentences",
      "time_markers_at_start"
    ]
  },
  "scoring_hints": {
    "avoid": [
      "present_continuous_for_past_events_unless_explaining_context",
      "run-on_sentences"
    ],
    "encourage": [
      "time_markers_at_beginning",
      "regular_verbs_ed_ending",
      "irregular_verbs_went_was"
    ]
  }
}
```

### Relacionamentos Chat Coach

```
User (1) ←→ (N) ChatConversation
ChatConversation (1) ←→ (N) ChatMessage
ChatConversation (1) ←→ (N) ChatLessonHistory [opcional]
```

### Diferenças para Modelos Existente

| Aspecto | Spec4 / Lingvist | Chat Coach |
|---------|------------------|------------|
| Persistência | Cada exercício (Card) | Cada mensagem (ChatMessage) |
| Feedback | Pós-submissão | Tempo real (não persistido) |
| Progresso | SM-2 (UserCardState) | Lesson Frame (pedagógico) |
| Seleção | Algoritmo de prioridade | N/A (conversa aberta) |
| Histórico | ReviewEvent | ChatMessage + ChatLessonHistory |

### Queries Importantes

**Buscar conversas recentes do usuário**:
```sql
SELECT id, title, created_at, updated_at,
  (SELECT COUNT(*) FROM chat_messages WHERE conversation_id = chat_conversations.id) AS message_count
FROM chat_conversations
WHERE user_id = $1
ORDER BY updated_at DESC
LIMIT 20;
```

**Buscar histórico de mensagens com paginação**:
```sql
SELECT id, role, content, created_at
FROM chat_messages
WHERE conversation_id = $1
ORDER BY created_at ASC
LIMIT 50 OFFSET $2;
```

**Atualizar lesson_frame após resposta do assistant**:
```sql
UPDATE chat_conversations
SET
  lesson_frame_json = $2,
  session_summary = session_summary || '\n\n' || $3,
  updated_at = NOW()
WHERE id = $1;
```

## Corpora Pipeline

### Fontes de Dados
- **Tatoeba**: Sentenças paralelas com tradução
- **ParaCrawl**: Corpus paralelo de alta qualidade
- **OpenSubtitles**: Legendas de filmes/series

### Processamento
1. **Download**: Scripts para baixar corpora
2. **Parsing**: Extrair sentenças e traduções
3. **Alignment**: Alinhar sentenças por palavra
4. **Filtering**: Filtrar por qualidade e complexidade
5. **Gap Creation**: Criar lacunas automáticas
6. **Validation**: Validação gramatical humana

### Seed Data
- 100 palavras iniciais (frequency rank 1-100)
- 300 sentenças (3 por palavra média)
- 3 decks por dificuldade
- Pronúncias IPA para todas palavras
