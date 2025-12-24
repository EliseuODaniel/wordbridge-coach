# FillTheWord MVP Specification

## Overview
FillTheWord is a spaced repetition vocabulary learning application that helps users learn new words through fill-in-the-gap exercises using smart algorithms.

## Vocabulary Learning Objective

FillTheWord has the primary goal of practicing the **10,000 most frequent English words**, prioritizing progressive mastery of high-frequency words before introducing less frequent words.

To achieve this, the system maintains a frequency dictionary (`WordFrequency`) containing at least 10,000 entries, each with:

- `word`: canonical form (lowercase)
- `rank`: integer from 1..10000 (1 = most frequent word)
- `frequency_score`: optional, normalized frequency score
- `coverage_pct`: cumulative coverage percentage (0-100)
- `band`: frequency band (1-4) for progressive unlocking

The data source uses open-source lists containing the 10,000 most frequent English words, ordered by frequency (e.g., lists derived from large corpora like the Google Trillion Word Corpus).

## Core Features (RF-01 to RF-06)

### RF-01: Memory Stage Visualization
Visual indicators showing card mastery level:
- **New (0 bolinhas)**: Gray, never seen card
- **Learning (1-2 bolinhas)**: Yellow, card in learning phase  
- **Review (3 bolinhas)**: Blue, card ready for review
- **Mature (4 bolinhas)**: Green, fully mastered card

### RF-02: Audio Playback
Text-to-speech functionality for vocabulary:
- **Word audio**: Pronunciation of target word
- **Sentence audio**: Full sentence with correct word
- **Language support**: EN, PT, ES, FR
- **URL endpoints**: `/api/tts/word/{id}` and `/api/tts/sentence/{id}`

### RF-03: SM-2 Algorithm
Spaced repetition algorithm for optimal learning:
- **Quality scale**: 0-5 (5 = perfect response)
- **Easiness factor**: 1.3-2.5 range
- **Interval calculation**: Based on repetitions and performance
- **Memory stages**: NEW → LEARNING → REVIEW → MATURE

### RF-04: Daily New Cards Limit
Configurable limit for new cards per day:
- **Default**: 10 cards per day
- **Range**: 5-20 cards (configurable)
- **Enforcement**: Backend respects limit in card selection
- **Priority**: Due cards → New cards (if under limit) → Learning cards

### RF-05: Real Statistics
Live statistics from database:
- **Total cards**: Active cards in target language
- **By stage**: New, Learning, Review, Mature counts
- **Today's activity**: Reviews, accuracy, new cards
- **Upcoming**: Next 7 days of due reviews

### RF-06: User Settings
Personalized learning configuration:
- **Daily new limit**: Cards per day (5-20 range)
- **Easiness factor**: SM-2 multiplier (1.3-2.5 range)
- **Persistence**: Saved per user in database

### RF-07: Word Insights (Frequency & Grammar)
Enhanced word information for better learning context:
- **Frequency visualization**: Interactive chart showing word rank vs coverage percentage
- **Coverage indicator**: Shows what percentage of language usage is covered up to this word
- **Grammar badge**: Displays part-of-speech and grammatical classification
- **Comparative context**: "This word is among the 500 most frequent" or similar insights

### RF-08: Learning Analytics Dashboard
Comprehensive performance insights with three visualization components:
- **Recent performance**: Session accuracy trend with last N responses
- **Theme cluster map**: Visual representation of performance by word themes/clusters
- **Progress over time**: Daily vocabulary growth and accuracy trends
- **Insights section**: Optional collapsible area below main study interface

## Intelligent Card Selection Algorithm

### Selection Principles
The card selection system is guided by three principles:

1. **Spaced Repetition (SRS)**: Cards with `next_review_at <= now()` have priority
2. **Frequency Importance**: Lower rank words (more common) are prioritized
3. **User Adaptation**: Words difficult for the user appear more frequently

### Frequency Bands
Vocabulary is divided into frequency bands with progressive unlocking:

- **Band 1**: ranks 1–1000 (most frequent words)
- **Band 2**: ranks 1001–3000
- **Band 3**: ranks 3001–6000
- **Band 4**: ranks 6001–10000

Users start with access to new words only in Band 1. Subsequent bands unlock when users achieve mastery thresholds:

- **Band 2**: 30% mastery of Band 1 words
- **Band 3**: 60% mastery of Bands 1-2 words
- **Band 4**: 80% mastery of Bands 1-3 words

### User Word Statistics
For each user and word, the system maintains statistics (`UserWordStats`):

- `total_attempts`, `correct_attempts`
- `last_result`: CORRECT/INCORRECT
- `mastery_score`: float in [0.0, 1.0]

These statistics update after each response using exponential moving average to calculate mastery.

### Card Selection Process
When deciding the next card, the backend:

1. **Builds candidate set**:
   - Cards due for review (`next_review_at <= now()`)
   - New eligible cards within unlocked bands, respecting daily new card limits

2. **Calculates priority score** for each card combining:
   - **SRS urgency** (W_SRS = 100.0): Overdue review priority
   - **Frequency importance** (W_FREQ = 10.0): Lower rank = higher priority
   - **Difficulty balance** (W_DIFF = 2.0): Low mastery = higher priority
   - **Novelty control** (W_NEW = 5.0): New cards get some boost

   Priority formula: `W_SRS * f_srs + W_FREQ * f_freq + W_DIFF * f_diff + W_NEW * f_new`

3. **Weighted sampling**: Selects next card by weighted random sampling based on priority scores

### Results
- Most frequent and yet-unmastered words appear with higher probability
- Already-mastered words appear only when SRS requests review
- Frequently-incorrect words appear more often until difficulty decreases

### Spec4: Variedade de Frases + Janela Dinâmica

**Endpoint**: `/api/v1/cards/next-spec4`

Spec4 é uma evolução do algoritmo de seleção que adiciona:
1. **Variedade de frases por palavra**: A mesma palavra aparece em frases diferentes
2. **Progressão por janela dinâmica**: 100 → 200 → 300... conforme domínio
3. **Mix inteligente novas/revisões**: ~25% novas, ~75% revisões
4. **Gating prefixal**: Só avança para rank N+1 se dominou 1..N

#### Algoritmo de Variedade de Frases

`get_sentence_for_word(user_id, word_id)`:
1. Busca todas as frases candidatas para a palavra (via `WordSentence` ou `Sentence.word_id`)
2. Consulta últimas K=10 frases usadas em `ReviewEvent` para este usuário+palavra
3. Prioriza:
   - **Frases nunca vistas**: Escolha aleatória entre não usadas recentemente
   - **Menos recente**: Se todas foram vistas, pega a mais antiga
4. Fallback: Cria frase básica se nenhuma existir (offline, sem internet)

#### Algoritmo de Progressão de Vocabulário

`getNextCardForUser(user_id)`:
1. Calcula `new_share = new_cards_shown / cards_shown` (hoje)
2. Se `new_share < 0.25` E existe próxima palavra elegível:
   - Retorna próxima palavra NOVA (rank = `max_contiguous_mastered_rank + 1`)
3. Senão:
   - Retorna palavra de REVISÃO (mais urgente por SM-2)
4. Após acerto:
   - Atualiza `max_contiguous_mastered_rank` (apenas se contíguo)
   - Se `max_contiguous_mastered_rank >= current_window_end_rank`: expande janela (+100)

#### Coexistência com Spec2 (Bandas)

**Importante**: Spec4 **NÃO** remove o sistema de bandas do Spec2.
- **Spec2 (Bandas)**: Continua existindo para insights/seed (WordFrequency.band)
- **Spec4 (Janela)**: Usa janela dinâmica para progressão de "novas" palavras
- **Compatibilidade**: Ambos os algoritmos podem coexistir:
  - `/api/v1/cards/next`: Usa algoritmo Spec2 (bandas + priority score)
  - `/api/v1/cards/next-spec4`: Usa algoritmo Spec4 (janela + variedade)

#### Diferenças Principais

| Aspecto | Spec2 (Bandas) | Spec4 (Janela) |
|---------|---------------|----------------|
| Desbloqueio | Por bandas (1k, 3k, 6k, 10k) | Por janela (100→200→300...) |
| Controle de novas | Por limite diário | Por mix (25% novas / 75% revisões) |
| Variedade de frases | 1 frase por palavra | Múltiplas frases (3-5 por palavra) |
| Gating | Por % de mastery da banda | Por prefixo contíguo (sem buracos) |
| Endpoint | `/api/v1/cards/next` | `/api/v1/cards/next-spec4` |

#### Contratos Críticos

1. **card_id**: Sempre `Card.id` real (UUID existente no banco)
2. **sentence_id**: Sempre preenchido em `ReviewEvent` para variedade
3. **exclude_card_id**: Exclui por `card_id` (não `word_id`)
4. **memory_stage**: Uppercase SM-2 (NEW/LEARNING/REVIEW/MATURE/RELEARN)

## Multi-User Profiles and Persistence

### User Management
FillTheWord supports multiple local users with Netflix-style profile selection:

- **First launch**: Shows profile creation screen
- **Subsequent launches**: Shows profile selection screen with existing users + "Add new user" option
- **Profile switching**: Users can select different profiles without losing progress

### User Entity
```markdown
### User Model Fields
- id: UUID primary key
- username: string (display name)
- language_preference: string (ex: "en")
- native_language_id: FK(Language)
- target_language_id: FK(Language)
- daily_new_limit: int (default: 10)
- easiness_factor: float (default: 2.5)
- created_at: datetime
```

### Persistent Storage
All user data is stored in PostgreSQL with Docker volume persistence:

- User profiles and settings
- Card progress and SRS state
- Word statistics and mastery scores
- Review history and performance data

The database volume is mounted to the host, ensuring that container restarts do not delete user progress.

### UI Profile Selection
Profile selection screen features:
- Grid of existing user profiles
- "Add new user" button for profile creation
- Persistent user selection across sessions
- Local storage of user preferences

### User Onboarding Process
When a new user is created:
1. **Immediate card initialization**: 50 cards from Band 1 (ranks 1-1000) are automatically assigned to the user
2. **No dependency on demo user**: Each user has completely isolated progress
3. **Fallback mechanism**: If initialization fails during creation, cards are created on-demand during first card request
4. **Progressive unlocking**: New users start with only Band 1 unlocked, following mastery-based progression

### Multi-User Isolation
- Each user maintains separate UserCardState and UserWordStats records
- Progress, settings, and mastery scores are completely isolated
- Daily new card limits are enforced per user
- Band unlocking thresholds are calculated individually per user

## Architecture

### Backend (FastAPI + PostgreSQL)
- **Base URL**: `http://localhost:8000/api/v1`
- **Authentication**: Demo user (no auth required in MVP)
- **Database**: PostgreSQL with UUID primary keys
- **Algorithm**: SM-2 implementation with SQLAlchemy

### Frontend (React + TypeScript)
- **URL**: `http://localhost:5173`
- **Theme**: Dark mode with gray-900/800 scheme
- **Components**: User selection, card display, stats dashboard, settings UI
- **Audio**: Integration with TTS microservice with auto-play sentence feature
- **Profile Management**: Netflix-style user selection screen

### TTS Microservice (Python)
- **URL**: `http://localhost:8001`
- **Engines**: Glow TTS, Piper TTS
- **Languages**: EN, PT, ES, FR with voice models
- **Endpoints**: `/api/tts/word/{id}` and `/api/tts/sentence/{id}`

## Database Schema

### Core Models
- **User**: Learner profiles with settings and language preferences
- **Language**: Supported languages with voice models
- **Word**: Vocabulary items with metadata and frequency data
- **WordFrequency**: Frequency rankings for 10,000 most common English words
- **Sentence**: Context sentences with gaps and translations
- **Card**: Gap exercises linking words to sentences
- **UserCardState**: SM-2 progress per user per card
- **UserWordStats**: Performance statistics per user per word
- **ReviewEvent**: Historical review attempts

### Analytics Models
- **WordTheme**: Thematic categories for words (Daily actions, Travel, Emotions, etc.)
- **WordThemeMapping**: Many-to-many relationship between words and themes with optional weights
- **UserThemeStats**: Aggregated performance statistics per user per theme
- **UserDailyStats**: Daily aggregated learning metrics per user

### Key Relationships
- Users → target_language → Language
- Word → WordFrequency (rank and band data)
- Cards → sentence → Sentence → word → Word
- UserCardState → user, card with SM-2 state
- UserWordStats → user, word with mastery scores
- ReviewEvent → user, card with performance data

### Frequency Band System
- **Band 1**: ranks 1-1000 (1000 words, 10% of vocabulary)
- **Band 2**: ranks 1001-3000 (2000 words, 20% of vocabulary)
- **Band 3**: ranks 3001-6000 (3000 words, 30% of vocabulary)
- **Band 4**: ranks 6001-10000 (4000 words, 40% of vocabulary)

Bands unlock progressively based on user mastery thresholds (30%/60%/80%).

## API Endpoints

### Cards
- `GET /api/v1/cards/next` - Get next study card
- `POST /api/v1/cards/{id}/answer` - Submit answer

### Users
- `GET /api/v1/users` - List all user profiles
- `POST /api/v1/users` - Create new user profile
- `GET /api/v1/users/{user_id}` - Get user by ID
- `PATCH /api/v1/users/{user_id}` - Update user profile
- `DELETE /api/v1/users/{user_id}` - Delete user profile

### Statistics
- `GET /api/v1/stats/basic` - User learning statistics

### Insights
- `GET /api/v1/insights/word/{word_id}` - Word frequency and grammar information
- `GET /api/v1/insights/user/{user_id}/themes` - User performance by thematic clusters
- `GET /api/v1/insights/user/{user_id}/daily` - User daily progress and trends
- `GET /api/v1/insights/user/{user_id}/recent` - Recent performance metrics

### Settings
- `GET /api/v1/settings/` - Get user configuration
- `PATCH /api/v1/settings/` - Update user configuration

### Health
- `GET /api/v1/cards/health` - Cards service health
- `GET /api/v1/stats/health` - Stats service health

## UI/UX Requirements

### Dark Mode Theme
- **Background**: `bg-gray-900`, `bg-gray-800`
- **Text**: `text-gray-100`, `text-gray-400`, `text-gray-500`
- **Borders**: `border-gray-700`, `border-gray-600`
- **Colors**: `text-primary-400`, `text-warning-400`, `text-success-400`, `text-info-400`

### Profile Selection Interface
- **Netflix-style design**: User cards in a grid layout
- **Profile creation**: Simple form with username and language preference
- **Visual hierarchy**: Clear distinction between existing and new user options
- **Demo mode indicator**: Subtle notification about local persistence

### Card Display Interface
- **Gap sentence**: Clear visual indication of missing word
- **Grammar hints**: English-only hints, no Portuguese instruction text
- **Translation display**: Context translation without spoilers
- **Auto-play**: Sentence audio plays automatically on new cards
- **Input field**: Clean input with placeholder "Type the missing word..."

### Responsive Design
- **Mobile**: Stacked layout, single column
- **Desktop**: Multi-column grids, optimal spacing
- **Accessibility**: Keyboard navigation, screen reader support

### Performance Targets
- **API response**: <100ms for card operations
- **TTS generation**: <1500ms for cache miss
- **TTS cache hit**: <20ms for cached audio
- **Page load**: <2s initial load

## Development Workflow

### Code Organization
- `api/` - FastAPI backend service
- `frontend/` - React SPA with TypeScript
- `tts/` - Text-to-speech microservice
- `openspec/` - Specifications and change documentation

### Change Management
- Use OpenSpec change documents for features
- Proposal → Apply → Archive workflow
- Atomic commits with clear messages
- No direct production deployments

### Quality Assurance
- Database migrations via Alembic
- Frontend builds with TypeScript
- Integration tests for core workflows
- Manual validation of TTS functionality

## Multi-language Support

### Target Languages (Learning Focus)
- **English (en)**: Target language, American English voice (lessac-glow_tts model, 63MB)
- **French (fr)**: Target language, French native voice (fr_FR-siwis-medium model, 63MB)

### Native Language (Interface)
- **Portuguese (pt)**: Brazilian Portuguese, interface language for grammar hints
- **Spanish (es)**: Spanish interface support
- **French (fr)**: French interface support
- **English (en)**: English interface support

### Language Configuration
- User profiles support `target_language` (en/fr) and `language_preference` (native interface)
- Cards and TTS generated in target language
- Grammar hints and interface in user's native language
- Translation context: PT translations provided for both EN and FR targets

### TTS Voice Models
- **English**: lessac-glow_tts (female, American English)
- **French**: fr_FR-siwis-medium (female, French native voice)
- **Download URLs**: Models sourced from huggingface.co/rhasspy/piper-voices
- **Storage**: `/models/{lang}/model.onnx` and `model.onnx.json` in TTS container

### User Management
- **Multi-user support**: Local profiles with Netflix-style selection
- **CRUD operations**: Create, Read, Update, Delete users via API and UI
- **Language switching**: Change target_language resets progress and generates new cards
- **Data persistence**: PostgreSQL with Docker volume mounts
- **Profile isolation**: Each user maintains separate progress, settings, and statistics

### Localization
- UI labels in user's native language preference
- Audio generation in target language (EN or FR)
- Sentence translations for context (PT translation for both EN and FR targets)
- Grammar hints in user's native language
- Language codes: `en`, `fr` (target), `pt`, `es`, `fr` (native)

## Success Metrics

### Learning Effectiveness
- **Accuracy rate**: >70% correct answers
- **Retention**: 80% cards mature after 30 days
- **Engagement**: Daily active users >60%

### Technical Performance
- **API latency**: 95th percentile <200ms
- **Audio availability**: >95% cache hit rate
- **Database queries**: <50ms average response
- **Frontend load**: <3s initial page load

### User Experience
- **Session completion**: >80% finish daily cards
- **Settings usage**: >20% configure preferences
- **Audio usage**: >90% play word/sentence audio
- **Error rate**: <1% failed requests

## Training Modes

FillTheWord supports multiple training modes to accommodate different learning preferences. Users can switch between modes freely.

### Spec4 Mode (Default)

**Route**: `/study`

**Description**: Traditional flashcard-style training with explicit "Check" button submission.

**Key Features**:
- Display sentence with gap `___`
- Separate input field for answer
- Manual submission via "Check" button
- Immediate feedback (correct/incorrect)
- Memory stage visualization (0-4 dots)
- Audio plays on card load

**Selection Algorithm**:
- Implements Spec4 getNextCardForUser logic
- Mix: 25% new / 75% review
- Gating by max_contiguous_mastered_rank
- Anti-repetition: K=10 sentence variety
- Priority: due cards → new cards (if under daily limit) → learning cards

**Best For**: Users who prefer traditional flashcard review, explicit control over submission timing.

### Lingvist Mode (Cloze Inline + Hints + Audio pós-acerto)

**Route**: `/train/lingvist`

**Status**: 📋 Proposed (see [change proposal](openspec/changes/2025-12-lingvist-mode-v1.md))

**Description**: Cloze deletion training with inline input, real-time validation, progressive hints, and audio reinforcement only after correct answers.

**Key Features**:
- **Inline input**: Gap `___` becomes editable chip `[_______]`
- **No "Check" button**: Auto-submit on correct answer (normalized match)
- **Enter fallback**: For accessibility/ambiguous cases
- **Real-time validation**: Prefix match feedback without server calls
- **Progressive hints**: Appear after mistakes/time stuck
  - Hint 1: Grammar tag PT-BR (ex: "substantivo, plural")
  - Hint 2: Length mask (ex: "_ _ _ _ _")
  - Hint 3: First letter
  - Hint 4: Reveal letters progressively
  - Hint 5: PT-BR word translation
  - Hint 6: Semantic hint
- **Audio after correct**: Play sentence audio only when `correct=true`
- **Advance after audio**: Next card loads only after audio ends (or 3s timeout)
- **Micro-progress**: "3/10" counter in top bar
- **Bottom sheet**: PT-BR translations (word + sentence)
- **Menu**: Skip card, report problem, exit mode

**Selection Algorithm**:
- Reuses Spec4 CardSelectionService (same gating, janela, anti-repetição)
- Mix: 20% new / 80% review (more conservative than Spec4)
- Same SM-2 intervals, memory stages

**Best For**: Users who prefer typing practice, muscle memory building, gamified progression.

**Differences from Spec4**:
| Feature | Spec4 Mode | Lingvist Mode |
|---------|------------|---------------|
| Input | Separate field | Inline in gap |
| Submission | Manual "Check" | Auto-submit + Enter fallback |
| Feedback | After submission | Real-time prefix match |
| Hints | None | Progressive (6 levels) |
| Audio | On card load | After correct only |
| Translations | None (MVP) | PT-BR word + sentence |
| Progress | Per session | Micro (X/Y) |

**Technical Implementation**:
- **Endpoint**: `GET /api/v1/cards/next-lingvist`
- **Response**: Enriched payload with `correct_answer`, `grammar_tag_pt`, `word_translation_pt`, `sentence_translation_pt`, `micro_progress`
- **Frontend**: New components (`InlineGapInput`, `HintPanel`, `BottomSheet`, `MicroProgress`, `OptionsMenu`)
- **Audio**: Hook `usePostCorrectAudio` with timeout (3s)
- **Hints**: Hook `useProgressiveHints` with triggers (mistakes, time stuck)

**Validation**:
- Auto-submit on exact normalized match
- Enter as fallback
- Client-side prefix match (green "bo____", red "box")
- Hints respect 60% max reveal rule
- Audio fallback if blocked/timeout

**Risks & Mitigations**:
- **Autoplay policy**: User just typed (valid gesture), fallback button if blocked
- **Spec4 regression**: New endpoint, `/next-spec4` unchanged
- **Translation debt**: MVP accepts empty, shows "Tradução indisponível"
- **Performance**: Hints calculated server-side, cached client-side

See [openspec/changes/2025-12-lingvist-mode-v1.md](openspec/changes/2025-12-lingvist-mode-v1.md) for complete specification.

## Future Considerations

### Post-MVP Features
- User authentication and profiles
- Advanced SM-2 customizations
- Spaced repetition analytics dashboard
- Export/import learning progress
- Collaborative learning features

### Technical Improvements
- Real-time WebSocket updates
- Advanced TTS voices and models
- Mobile application development
- Cloud deployment and scaling
- Machine learning optimizations
