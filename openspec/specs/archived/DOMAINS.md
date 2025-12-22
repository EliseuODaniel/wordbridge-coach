# FillTheWord - Modelo de Domínio Simplificado

## Entidades Principais

### Language
Idiomas suportados pelo sistema com configurações de TTS.

**Attributes**:
- `id` (UUID, PK)
- `code` (string, unique) - Ex: "en", "pt", "es"
- `name` (string) - Ex: "English", "Português", "Español"
- `voice_model` (string) - Coqui/Piper TTS voice name
- `is_active` (boolean)
- `created_at` (datetime)

**Invariants**:
- Language code must be ISO 639-1 (2 letters)
- Cannot delete if associated with active cards

### Deck
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
- difficulty_level must be 1-5
- Must have at least one associated card to be active

### Word
Vocabulário individual usado nas frases.

**Attributes**:
- `id` (UUID, PK)
- `text` (string, unique by language)
- `language_id` (UUID, FK)
- `pronunciation` (string, optional) - IPA notation
- `frequency_rank` (int, optional) - Common word frequency (1=most common)
- `audio_path` (string, optional) - Path to cached TTS audio
- `difficulty` (int, 1-5) - Derived from frequency and complexity
- `created_at` (datetime)

**Invariants**:
- Text cannot be empty
- Difficulty must be 1-5
- Text unique within language
- audio_path format: "audio/<language>/word/<slug>.wav"

### Synonym
Sinônimos aceitos para validação de respostas.

**Attributes**:
- `id` (UUID, PK)
- `word_id` (UUID, FK) - Word principal
- `synonym_text` (string) - Texto do sinônimo
- `language_id` (UUID, FK)
- `is_primary` (boolean) - Se é a forma principal
- `created_at` (datetime)

**Invariants**:
- synonym_text cannot be empty
- Must belong to same language as main word

### Card
Entidade principal que combina frase e palavra para aprendizado.

**Attributes**:
- `id` (UUID, PK)
- `sentence_text` (string) - Ex: "The ___ is on the table."
- `word_id` (UUID, FK) - Palavra que fica oculta
- `deck_id` (UUID, FK) - Deck do card
- `language_id` (UUID, FK)
- `gap_start` (int) - Posição inicial da lacuna
- `gap_end` (int) - Posição final da lacuna
- `difficulty` (int, 1-5) - Complexidade geral do card
- `grammar_hint` (string, optional) - Dica gramatical
- `context_type` (string, enum) - Ex: "determiner", "verb", "noun"
- `is_active` (boolean)
- `created_at` (datetime)

**Invariants**:
- gap_start <= gap_end
- gap range must correspond to placeholder "___" in sentence_text
- Word must belong to sentence language
- Must have exactly one gap placeholder

### CardProgress
Progresso individual do usuário por card usando algoritmo SM-2.

**Attributes**:
- `id` (UUID, PK)
- `card_id` (UUID, FK)
- `sm2_level` (enum) - "new", "learning", "review", "relearn", "mature"
- `repetitions` (int, default 0) - Número de repetições corretas
- `ease_factor` (float, default 2.5) - Fator de facilidade SM-2
- `interval_days` (int, default 1) - Dias até próxima revisão
- `last_review` (datetime, optional)
- `next_review` (datetime, optional)
- `total_reviews` (int, default 0)
- `correct_reviews` (int, default 0)
- `average_response_time` (float, seconds, optional)
- `created_at` (datetime)
- `updated_at` (datetime)

**Invariants**:
- Unique card_id (single user implicit in MVP)
- ease_factor between 1.3 and 2.5
- interval_days >= 1 and <= 180
- correct_reviews <= total_reviews
- next_review >= last_review when both exist

### AudioCache
Metadados para gerenciamento de cache de áudio em disco.

**Attributes**:
- `id` (UUID, PK)
- `text_hash` (string) - Hash do texto para cache key
- `audio_path` (string) - Caminho do arquivo em disco
- `language_id` (UUID, FK)
- `audio_type` (enum) - "word", "sentence"
- `voice_model` (string) - Voice usada para gerar
- `duration_ms` (int) - Duração do áudio
- `file_size_bytes` (int) - Tamanho do arquivo
- `created_at` (datetime)

**Invariants**:
- audio_path must follow pattern: "audio/<language>/<type>/<hash>.wav"
- text_hash must be consistent hash of source text + voice

## Algoritmo SM-2 Detalhado

### Estados de Aprendizagem

```python
class SM2Level(Enum):
    NEW = "new"           # Nunca visto
    LEARNING = "learning" # Aprendendo ativamente
    REVIEW = "review"     # Revisão programada
    RELEARN = "relearn"   # Reaprendendo após falha
    MATURE = "mature"     # Completamente dominado
```

### Transições de Estado

```
NEW → LEARNING (primeira resposta correta)
LEARNING → REVIEW (após 3 respostas corretas consecutivas)
REVIEW → MATURE (após 7 dias de intervalo)
LEARNING/REVIEW/RELEARN → RELEARN (qualquer resposta incorreta)
RELEARN → LEARNING (resposta correta após falha)
```

### Fórmulas SM-2

**Para resposta correta**:
```python
def update_sm2_correct(progress):
    progress.repetitions += 1
    
    if progress.repetitions == 1:
        progress.interval_days = 1
    elif progress.repetitions == 2:
        progress.interval_days = 6
    else:
        progress.interval_days = min(
            int(progress.interval_days * progress.ease_factor),
            180  # máximo 180 dias
        )
    
    progress.ease_factor = min(
        progress.ease_factor + 0.1,
        2.5  # máximo ease factor
    )
    
    # Atualiza nível
    if progress.repetitions >= 7 and progress.interval_days >= 7:
        progress.sm2_level = SM2Level.MATURE
    elif progress.repetitions >= 3:
        progress.sm2_level = SM2Level.REVIEW
    else:
        progress.sm2_level = SM2Level.LEARNING
```

**Para resposta incorreta**:
```python
def update_sm2_incorrect(progress):
    progress.repetitions = 0
    progress.interval_days = 1
    progress.ease_factor = max(
        progress.ease_factor - 0.2,
        1.3  # mínimo ease factor
    )
    progress.sm2_level = SM2Level.RELEARN
```

### Validação de Respostas

```python
class ResponseValidator:
    def __init__(self, card: Card):
        self.card = card
        self.word = card.word
        self.synonyms = [syn.synonym_text for syn in card.word.synonyms]
    
    def is_correct(self, user_answer: str) -> bool:
        clean_answer = self.normalize(user_answer)
        correct_word = self.normalize(self.word.text)
        
        # Comparação direta
        if clean_answer == correct_word:
            return True
        
        # Verifica sinônimos
        for synonym in self.synonyms:
            if clean_answer == self.normalize(synonym):
                return True
        
        # Tolerância a plural (context-aware)
        if self.is_plural_context():
            if clean_answer == correct_word + 's':
                return True
        
        # Tolerância a artigos
        if self.is_article_context(clean_answer):
            article, word = clean_answer.split(' ', 1)
            if word == correct_word and article in ['a', 'an', 'the']:
                return True
        
        return False
    
    def normalize(self, text: str) -> str:
        return text.strip().lower().replace('  ', ' ')
    
    def is_plural_context(self) -> bool:
        # Verifica se contexto permite plural
        context_indicators = ['are', 'were', 'many', 'several', 'they']
        return any(indicator in self.card.sentence_text.lower() 
                  for indicator in context_indicators)
    
    def is_article_context(self, answer: str) -> bool:
        return len(answer.split()) == 2
```

### Sistema de Cache de Áudio

```python
class AudioCacheManager:
    def __init__(self, cache_root: str = "audio"):
        self.cache_root = cache_root
    
    def get_audio_path(self, text: str, language_code: str, 
                      audio_type: str, voice: str) -> str:
        text_hash = hashlib.md5(f"{text}_{voice}".encode()).hexdigest()
        return f"{self.cache_root}/{language_code}/{audio_type}/{text_hash}.wav"
    
    def cache_exists(self, text: str, language_code: str, 
                    audio_type: str, voice: str) -> bool:
        path = self.get_audio_path(text, language_code, audio_type, voice)
        return os.path.exists(path)
    
    def save_audio(self, audio_data: bytes, text: str, 
                  language_code: str, audio_type: str, voice: str,
                  duration_ms: int):
        path = self.get_audio_path(text, language_code, audio_type, voice)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, 'wb') as f:
            f.write(audio_data)
        
        # Salva metadados no banco
        audio_cache = AudioCache(
            text_hash=hashlib.md5(f"{text}_{voice}".encode()).hexdigest(),
            audio_path=path,
            language_id=get_language_id(language_code),
            audio_type=audio_type,
            voice_model=voice,
            duration_ms=duration_ms,
            file_size_bytes=len(audio_data)
        )
        audio_cache.save()
```

## Regras de Negócio

### Card Selection Priority
```python
def select_next_card():
    now = datetime.utcnow()
    
    # 1. Cartões due para revisão
    due_cards = CardProgress.objects.filter(
        next_review__lte=now,
        sm2_level__in=[SM2Level.LEARNING, SM2Level.REVIEW, SM2Level.MATURE]
    ).order_by('next_review', 'ease_factor')
    
    if due_cards.exists():
        return due_cards.first().card
    
    # 2. Cartões novos
    new_cards = Card.objects.filter(
        cardprogress__isnull=True,
        is_active=True
    ).order_by('difficulty', 'word__frequency_rank')
    
    return new_cards.first() if new_cards.exists() else None
```

### Progress Tracking
```python
def record_answer(card: Card, user_answer: str, response_time: float):
    progress, created = CardProgress.objects.get_or_create(
        card=card,
        defaults={
            'sm2_level': SM2Level.NEW,
            'repetitions': 0,
            'ease_factor': 2.5,
            'interval_days': 1
        }
    )
    
    validator = ResponseValidator(card)
    is_correct = validator.is_correct(user_answer)
    
    # Atualiza estatísticas
    progress.total_reviews += 1
    if is_correct:
        progress.correct_reviews += 1
        update_sm2_correct(progress)
    else:
        update_sm2_incorrect(progress)
    
    # Atualiza tempo médio de resposta
    if progress.average_response_time is None:
        progress.average_response_time = response_time
    else:
        alpha = 0.3  # fator de smoothing
        progress.average_response_time = (
            alpha * response_time + 
            (1 - alpha) * progress.average_response_time
        )
    
    progress.last_review = datetime.utcnow()
    progress.next_review = datetime.utcnow() + timedelta(days=progress.interval_days)
    progress.save()
    
    return {
        'correct': is_correct,
        'correct_answer': card.word.text,
        'sm2_update': {
            'new_level': progress.sm2_level.value,
            'next_review': progress.next_review.isoformat(),
            'interval_days': progress.interval_days
        }
    }
```

### Example Schema (SQL)
```sql
-- Core tables
CREATE TABLE languages (
    id UUID PRIMARY KEY,
    code VARCHAR(2) UNIQUE NOT NULL,
    name VARCHAR(50) NOT NULL,
    voice_model VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE decks (
    id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    language_id UUID REFERENCES languages(id),
    difficulty_level INTEGER CHECK (difficulty_level BETWEEN 1 AND 5),
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE words (
    id UUID PRIMARY KEY,
    text VARCHAR(100) NOT NULL,
    language_id UUID REFERENCES languages(id),
    pronunciation VARCHAR(200),
    frequency_rank INTEGER,
    audio_path VARCHAR(500),
    difficulty INTEGER CHECK (difficulty BETWEEN 1 AND 5),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(language_id, text)
);

CREATE TABLE synonyms (
    id UUID PRIMARY KEY,
    word_id UUID REFERENCES words(id),
    synonym_text VARCHAR(100) NOT NULL,
    language_id UUID REFERENCES languages(id),
    is_primary BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE cards (
    id UUID PRIMARY KEY,
    sentence_text TEXT NOT NULL,
    word_id UUID REFERENCES words(id),
    deck_id UUID REFERENCES decks(id),
    language_id UUID REFERENCES languages(id),
    gap_start INTEGER NOT NULL,
    gap_end INTEGER NOT NULL,
    difficulty INTEGER CHECK (difficulty BETWEEN 1 AND 5),
    grammar_hint TEXT,
    context_type VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    CHECK (gap_start <= gap_end)
);

CREATE TABLE card_progress (
    id UUID PRIMARY KEY,
    card_id UUID REFERENCES cards(id) UNIQUE,
    sm2_level VARCHAR(20) NOT NULL DEFAULT 'new',
    repetitions INTEGER DEFAULT 0,
    ease_factor FLOAT DEFAULT 2.5 CHECK (ease_factor >= 1.3 AND ease_factor <= 2.5),
    interval_days INTEGER DEFAULT 1 CHECK (interval_days >= 1 AND interval_days <= 180),
    last_review TIMESTAMP,
    next_review TIMESTAMP,
    total_reviews INTEGER DEFAULT 0,
    correct_reviews INTEGER DEFAULT 0,
    average_response_time FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CHECK (correct_reviews <= total_reviews)
);

CREATE TABLE audio_cache (
    id UUID PRIMARY KEY,
    text_hash VARCHAR(64) NOT NULL,
    audio_path VARCHAR(500) NOT NULL,
    language_id UUID REFERENCES languages(id),
    audio_type VARCHAR(20) NOT NULL,
    voice_model VARCHAR(100) NOT NULL,
    duration_ms INTEGER NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```
