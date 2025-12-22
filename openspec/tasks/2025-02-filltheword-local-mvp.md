# FillTheWord Local MVP Tasks - February 2025

## Overview
MVP v0.1 focado no loop principal de aprendizado com TTS local e algoritmo SM-2. Timeline de 2 semanas para time de 3 pessoas, alinhado ao texto-base original (RF-01 a RF-06).

**Team Structure**: 
- 1 Backend Developer (API + Database + TTS)
- 1 Frontend Developer (React + Interface)  
- 1 Content Developer (Vocabulary + Sentences)

**Timeline**: 2 semanas (10 dias úteis)
**Goal**: App funcional local com 100+ cartões iniciais
**Scope**: RF-01 a RF-06 completos conforme texto-base

## Phase 1: Foundation Setup (Days 1-3)

### [BACKEND-001] Backend Foundation
**Priority**: Critical
**Assignee**: Backend Developer
**Estimated**: 2 days

**Tasks**:
- [ ] Initialize FastAPI project structure
- [ ] Configure PostgreSQL connection with SQLAlchemy
- [ ] Set up Alembic for database migrations
- [ ] Create core models (Card, Word, Deck, User, UserCardState, ReviewEvent)
- [ ] Add Dockerfile for backend service
- [ ] Set up development environment with hot reload
- [ ] Create basic health check endpoint

**Deliverables**:
- Working API server at http://localhost:8000
- Database migrations for core entities
- Basic API documentation
- Docker container ready

### [DB-001] Database and Content Setup
**Priority**: Critical
**Assignee**: Backend Developer + Content Developer
**Estimated**: 1 day

**Tasks**:
- [ ] Run database migrations
- [ ] Create seed data script
- [ ] Add 50 initial English words (frequency 1-100)
- [ ] Create 100 fill-in-the-gap sentences
- [ ] Set up proper indexes for SM-2 queries
- [ ] Test database performance

**Content Requirements**:
- **Words**: Common vocabulary (book, cat, house, etc.)
- **Sentences**: Simple structures with clear context
- **Difficulty**: Levels 1-3 only for MVP
- **Examples**: 
  - "The ___ is on the table." → book
  - "A ___ sleeps in the garden." → cat

**Deliverables**:
- Populated database with 100 cards
- Basic content validation
- Performance benchmarks

## Phase 2: Core API Implementation (Days 4-6)

### [API-001] Core Card Management API
**Priority**: Critical
**Assignee**: Backend Developer  
**Estimated**: 2 days

**Tasks**:
- [ ] Implement GET /api/cards/next with SM-2 selection
- [ ] Implement POST /api/cards/{id}/answer with validation
- [ ] Add answer tolerance (case, accents, synonyms, articles)
- [ ] Implement complete SM-2 algorithm (quality 0-5, easiness_factor >= 1.3)
- [ ] Add progressive hints system
- [ ] Create API tests for core endpoints

**SM-2 Implementation Details**:
- Quality scale: 0-5 (0=failure, 5=perfect)
- Ease factor: 1.3 to 2.5 range (default 2.5)
- Intervals: 1d → 6d → exponential growth
- Status mapping: new → learning → review → mature
- Reset on failure: repetitions=0, interval=1d

**Answer Validation Logic**:
- Case insensitive: "Book" = "book"
- Accent removal: "café" = "cafe"  
- Article tolerance: "book" accepts "a book"/"the book"
- Synonym support: "color" accepts "colour"
- Plural control based on context

**Deliverables**:
- Working card selection algorithm
- Complete answer validation with tolerance
- Full SM-2 progress tracking
- Unit tests with >80% coverage

### [TTS-001] Local TTS Integration
**Priority**: Critical  
**Assignee**: Backend Developer
**Estimated**: 2 days

**Tasks**:
- [ ] Set up Coqui/Piper TTS service container
- [ ] Download and configure voice models (en/pt/es)
- [ ] Implement disk-based audio cache system
- [ ] Create TTS API endpoints (/api/tts/word, /api/tts/sentence)
- [ ] Add static file serving for cached audio (/api/audio/{lang}/{type}/{slug}.wav)
- [ ] Test TTS performance and quality

**TTS Configuration**:
```yaml
voices:
  en: "lessac-glow_tts"      # Clear American English
  pt: "pt_br_female-glow_tts" # Brazilian Portuguese  
  es: "es_male-glow_tts"     # Neutral Spanish
```

**Audio Cache Structure**:
```
audio/
├── en/word/abc123.wav
├── en/sentence/def456.wav
├── pt/word/ghi789.wav
└── es/sentence/jkl012.wav
```

**Deliverables**:
- TTS service at http://localhost:8001
- Audio generation API with disk cache
- Pre-downloaded models for 3 languages
- Performance benchmarks (<1500ms generation)

## Phase 3: Study Features Implementation (Days 7-8)

### [API-002] Study Session Features (RF-04)
**Priority**: High
**Assignee**: Backend Developer
**Estimated**: 1 day

**Tasks**:
- [ ] Implement session management with counters
- [ ] Add daily new card limits (configurable, default 10)
- [ ] Create session persistence across restarts
- [ ] Add basic session statistics tracking
- [ ] Implement study streak calculation

**Session Management**:
```python
{
  "session_id": "uuid",
  "cards_studied": 15,
  "new_cards_today": 3,
  "new_cards_limit": 10,
  "correct_answers": 12,
  "incorrect_answers": 3,
  "start_time": "2024-01-15T10:00:00Z"
}
```

**Deliverables**:
- Session state persistence
- Daily limits enforcement
- Session counters and statistics
- Study streak tracking

### [API-003] Statistics and Configuration (RF-05/06)
**Priority**: High
**Assignee**: Backend Developer
**Estimated**: 1 day

**Tasks**:
- [ ] Implement basic progress statistics (RF-05)
- [ ] Add review configuration parameters (RF-06)
- [ ] Create statistics summary endpoints
- [ ] Add configuration management
- [ ] Implement user preference storage

**Statistics Features**:
- Total cards, studied cards, mastered cards
- SM-2 level distribution (new/learning/review/mature)
- Success rate calculation
- Study streak tracking

**Configuration Features**:
- Daily new card limit (5-20, default 10)
- SM-2 parameters (easiness_factor 1.3-2.5)
- Audio auto-play toggle
- Hints system toggle

**Deliverables**:
- Basic statistics dashboard data
- User preference management
- Review configuration interface
- Progress tracking analytics

## Phase 4: Frontend Development (Days 7-8)

### [FE-001] React Foundation
**Priority**: Critical
**Assignee**: Frontend Developer
**Estimated**: 1 day

**Tasks**:
- [ ] Initialize React + TypeScript project with Vite
- [ ] Configure TailwindCSS styling system
- [ ] Set up React Router for navigation
- [ ] Configure axios for API communication
- [ ] Create basic project structure
- [ ] Add Dockerfile for frontend container

**Deliverables**:
- Working React app at http://localhost:3000
- Basic styling system with Tailwind
- API integration layer ready

### [FE-002] Study Interface Core (RF-01/02)
**Priority**: Critical
**Assignee**: Frontend Developer
**Estimated**: 1 day

**Tasks**:
- [ ] Create main study page component
- [ ] Implement card display with gap visualization
- [ ] Add answer input field with validation
- [ ] Create submit button with loading states
- [ ] Add feedback system (correct/incorrect/hints)
- [ ] Implement progressive hints display
- [ ] Add keyboard navigation (Enter to submit)

**UI Components**:
```tsx
// Main study interface
<CardDisplay 
  sentence="The ___ is on the table." 
  gapStart={4}
  gapEnd={4}
  grammarHint="É um objeto que você lê"
/>
<AnswerInput onSubmit={handleSubmit} />
<FeedbackMessage 
  isCorrect={true} 
  message="✅ Excelente!"
  hint={null}
/>
<NavigationButtons onNext={handleNext} />
<SessionCounter 
  studied={15} 
  newToday={3} 
  limit={10}
/>
```

**Deliverables**:
- Complete study interface
- Progressive hints system
- Keyboard navigation support
- Session counters display

## Phase 5: Audio Integration & Polish (Days 9-10)

### [FE-003] TTS Audio Integration (RF-03)
**Priority**: High
**Assignee**: Frontend Developer + Backend Developer
**Estimated**: 1 day

**Tasks**:
- [ ] Add audio player components for TTS
- [ ] Implement sentence audio playback
- [ ] Implement word pronunciation playback
- [ ] Add audio caching in frontend
- [ ] Handle audio loading and error states
- [ ] Test audio quality and synchronization

**Audio Features**:
```tsx
<AudioButton 
  type="sentence" 
  text="The book is on the table"
  language="en" 
  cacheKey="en-sentence-def456"
/>
<AudioButton 
  type="word" 
  text="book"
  language="en" 
  cacheKey="en-word-abc123"
/>
```

**Deliverables**:
- Working TTS integration
- Audio playback controls
- Error handling for TTS failures
- Frontend audio caching

### [FE-004] Statistics and Settings UI (RF-05/06)
**Priority**: High
**Assignee**: Frontend Developer
**Estimated**: 1 day

**Tasks**:
- [ ] Create basic statistics dashboard
- [ ] Add session statistics display
- [ ] Implement progress visualization
- [ ] Create settings/configuration interface
- [ ] Add user preference forms
- [ ] Implement responsive design for mobile

**Statistics UI**:
```tsx
<StatsDashboard 
  totalCards={300}
  studiedCards={135}
  masteredCards={23}
  learningCards={67}
  successRate={80}
  studyStreak={5}
/>
<SettingsForm 
  dailyNewLimit={10}
  easinessFactor={2.5}
  autoPlayAudio={true}
  showHints={true}
/>
```

**Deliverables**:
- Statistics dashboard interface
- User settings management
- Mobile-responsive design
- Complete user experience

### [INT-001] Integration & Testing
**Priority**: Critical
**Assignee**: Full Team
**Estimated**: 1 day

**Tasks**:
- [ ] Connect frontend to backend APIs
- [ ] Test complete user flow end-to-end
- [ ] Fix integration issues and bugs
- [ ] Optimize performance and caching
- [ ] Test on different screen sizes
- [ ] Validate SM-2 algorithm with sample data
- [ ] Test session persistence
- [ ] Verify statistics calculations

**Testing Scenarios**:
1. **Complete Learning Loop**: Next card → Answer → Feedback → Next
2. **TTS Audio**: Play sentence → Play word → Cache verification
3. **Answer Validation**: Case, accents, synonyms, articles tolerance
4. **SM-2 Progress**: New → Learning → Review → Mature transitions
5. **Session Management**: Daily limits, counters, persistence
6. **Statistics**: Progress calculation, dashboard display
7. **Settings**: Configuration changes, preferences storage

**Deliverables**:
- Fully integrated application
- End-to-end testing complete
- Performance optimization
- Bug-free MVP

## Content Development (Parallel)

### [CONTENT-001] Initial Vocabulary Corpus
**Priority**: High
**Assignee**: Content Developer
**Estimated**: 3 days (parallel with development)
**Days 1-3**: Core vocabulary creation
**Days 4-6**: Sentence generation and validation
**Days 7-8**: Audio preparation and testing

**Tasks**:
- [ ] Compile 100 core English words (frequency 1-500)
- [ ] Create 300 fill-in-the-gap sentences (3 per word average)
- [ ] Add IPA pronunciations for all words
- [ ] Create 3-5 decks with difficulty levels
- [ ] Add grammar hints for all sentences
- [ ] Configure synonyms for common variations
- [ ] Validate grammar and context of all sentences
- [ ] Test TTS pronunciation for all content

**Vocabulary Scope (100 words)**:
- **Level 1** (40 words): book, cat, house, water, food, etc.
- **Level 2** (35 words): beautiful, important, different, etc.  
- **Level 3** (25 words): necessary, delicious, expensive, etc.

**Sentence Examples**:
```json
{
  "word": "book",
  "sentences": [
    {
      "text": "The ___ is on the table.",
      "translation": "O livro está na mesa.",
      "grammar_hint": "É um objeto que você lê",
      "difficulty": 1
    },
    {
      "text": "I am reading an interesting ___.",
      "translation": "Estou lendo um livro interessante.",
      "grammar_hint": "Pode ser interessante ou boring",
      "difficulty": 2
    },
    {
      "text": "She borrowed a ___ from the library.",
      "translation": "Ela pegou um livro emprestado da biblioteca.",
      "grammar_hint": "Normalmente se empresta de library",
      "difficulty": 2
    }
  ],
  "pronunciation": "/bʊk/",
  "synonyms": ["tome"] // synonym for "book" as verb
}
```

**Deck Structure**:
- **Daily English**: 40 cards, difficulty 1-2
- **Common Objects**: 30 cards, difficulty 1
- **Actions & Verbs**: 30 cards, difficulty 2-3

**Deliverables**:
- 100 words with metadata and pronunciations
- 300 sentences with gaps, translations, and hints
- 3 structured decks with difficulty levels
- Content ready for database seeding
- Audio validation report

### [CONTENT-002] Corpora Pipeline Setup
**Priority**: Medium
**Assignee**: Content Developer + Backend Developer
**Estimated**: 1 day (parallel)

**Tasks**:
- [ ] Set up Tatoeba download scripts
- [ ] Configure ParaCrawl processing
- [ ] Add OpenSubtitles extraction
- [ ] Create sentence alignment tools
- [ ] Implement quality filtering
- [ ] Generate initial seed data

**Corpora Sources**:
- **Tatoeba**: Sentenças paralelas com tradução humana
- **ParaCrawl**: Corpus paralelo de alta qualidade web
- **OpenSubtitles**: Legendas de filmes/series para linguagem natural

**Deliverables**:
- Working corpora processing pipeline
- Quality filters for sentence selection
- Automated seed data generation
- Documentation for content expansion

## Deployment & Documentation (Day 10)

### [DEPLOY-001] Local Deployment Setup
**Priority**: High
**Assignee**: Full Team
**Estimated**: 0.5 days

**Tasks**:
- [ ] Finalize docker-compose.yml with all 4 services
- [ ] Create deployment scripts
- [ ] Set up database backup strategy
- [ ] Create user documentation
- [ ] Test complete deployment process
- [ ] Verify audio cache permissions

**Deployment Checklist**:
```bash
# Quick deployment commands
git clone <repository>
cd filltheword
mkdir -p audio/{en,pt,es}/{word,sentence}
docker-compose up -d
docker-compose exec api alembic upgrade head
docker-compose exec api python scripts/seed_data.py
docker-compose exec tts python scripts/download_models.py
open http://localhost:3000
```

**Deliverables**:
- Production-ready docker-compose
- Deployment documentation
- User guide for setup

### [DOC-001] Documentation Complete
**Priority**: Medium
**Assignee**: Full Team
**Estimated**: 0.5 days

**Tasks**:
- [ ] Finalize README.md with setup instructions
- [ ] Document API endpoints with examples
- [ ] Create user guide for the application
- [ ] Document content creation process
- [ ] Add troubleshooting guide
- [ ] Document SM-2 algorithm implementation

**Deliverables**:
- Complete project documentation
- User setup guide
- API documentation
- Troubleshooting guide

## MVP Acceptance Criteria

### Core Functionality ✅
- [ ] RF-01: Cartão com lacuna, tradução, dica, nível memória
- [ ] RF-02: Validação tolerante (case/acentos/sinônimos), dicas progressivas  
- [ ] RF-03: Áudio palavra e frase com cache disco audio/<lang>/<type>/<slug>.wav
- [ ] RF-04: Sessão estudo com contador e limite novos/dia
- [ ] RF-05: Estatísticas básicas de progresso
- [ ] RF-06: Configuração revisão (limites, algoritmo SM-2)
- [ ] SM-2 algorithm working correctly (quality 0-5, easiness_factor >= 1.3)
- [ ] User/UserCardState/ReviewEvent entities implemented
- [ ] Application works offline after initial setup

### Performance ✅  
- [ ] Page load time < 2 seconds
- [ ] Card selection < 100ms
- [ ] Answer validation < 50ms
- [ ] TTS cache hit < 20ms
- [ ] TTS generation < 1500ms

### Content ✅
- [ ] Minimum 100 words available
- [ ] Minimum 300 sentences with translations and hints
- [ ] 3+ decks with different difficulty levels
- [ ] Audio available for all content
- [ ] IPA pronunciations included
- [ ] Grammar hints for all sentences

### Usability ✅
- [ ] Interface works on mobile/tablet/desktop
- [ ] Keyboard navigation complete
- [ ] Audio controls intuitive
- [ ] Progressive hints clear and helpful
- [ ] Session counters visible
- [ ] Statistics dashboard informative
- [ ] Settings accessible and functional

### Technical Quality ✅
- [ ] All 4 Docker containers working correctly
- [ ] Database migrations run smoothly
- [ ] Core API endpoints documented and working
- [ ] Complete SM-2 algorithm implemented
- [ ] Audio cache system functional
- [ ] Session persistence working
- [ ] Statistics calculations accurate

## Risk Mitigation

### Technical Risks
**TTS Performance**: Coqui TTS may be slow initially
- **Mitigation**: Pre-generate audio for first 50 words
- **Fallback**: Use Piper TTS if Coqui too slow

**SM-2 Complexity**: Algorithm may have edge cases
- **Mitigation**: Implement严格按照 texto-base SM-2 specification
- **Testing**: Extensive testing with quality 0-5 scenarios

**Session Management**: State persistence complexity
- **Mitigation**: Simple session storage in database
- **Fallback**: In-memory session if DB issues

### Content Risks
**Sentence Quality**: Generated sentences may be unnatural
- **Mitigation**: Human review of all 300 sentences
- **Validation**: Grammar checking tools integration

**Limited Vocabulary**: 100 words may be too restrictive
- **Mitigation**: Focus on high-frequency words (rank 1-500)
- **Plan**: Easy expansion to 500+ words post-MVP

### Timeline Risks
**Integration Issues**: Frontend-backend integration may take longer
- **Mitigation**: Start integration testing by Day 6
- **Parallel**: Work on integration during development

**TTS Setup**: Voice model downloads may be slow/large
- **Mitigation**: Start downloads on Day 1
- **Alternative**: Include models in Docker image if needed

## Success Metrics

### Technical Performance
- System startup time: < 30 seconds
- Average response time: < 200ms
- TTS generation time: < 1500ms
- Memory usage: < 2GB total
- Disk usage: < 1GB (including cache)

### User Experience  
- Study session completion rate: > 90%
- Average cards per session: > 10
- Time to first correct answer: < 30 seconds
- Audio playback success rate: > 95%
- Session persistence reliability: > 99%

### Learning Outcomes
- SM-2 algorithm working correctly (quality 0-5, easiness_factor >= 1.3)
- Progress tracking accurate across all levels
- Answer validation tolerance appropriate
- Users can complete full learning cycle including RF-04/05/06
- Statistics reflect real progress

## Daily Schedule

### Day 1 (Monday)
- **Backend**: FastAPI setup + Database models (User/UserCardState/ReviewEvent)
- **Content**: Word list compilation (50 words)
- **Frontend**: Project setup + Basic structure

### Day 2 (Tuesday)  
- **Backend**: Database migrations + Seed data
- **Content**: Word list completion + Sentence creation
- **Frontend**: Styling system + Basic components

### Day 3 (Wednesday)
- **Backend**: Health checks + Basic API endpoints
- **Content**: Sentence validation + Grammar hints
- **Frontend**: Card display component

### Day 4 (Thursday)
- **Backend**: Card selection API (SM-2 completo)
- **Content**: Deck organization + Difficulty levels
- **Frontend**: Answer input component

### Day 5 (Friday)
- **Backend**: Answer validation + SM-2 updates (quality 0-5)
- **Content**: Audio preparation + Synonyms
- **Frontend**: Feedback system + Navigation

### Day 6 (Saturday)
- **Backend**: TTS service integration + Audio cache
- **Content**: Final content validation + Audio testing
- **Frontend**: Basic page layout complete

### Day 7 (Sunday)
- **Backend**: Session management (RF-04) + Statistics (RF-05)
- **Frontend**: Audio integration + Session counters
- **Integration**: Frontend + Backend connection

### Day 8 (Monday)
- **Backend**: Configuration (RF-06) + API documentation
- **Frontend**: Statistics dashboard + Settings UI
- **Integration**: End-to-end testing

### Day 9 (Tuesday)
- **Full Team**: Integration testing + Bug fixes
- **Full Team**: Performance tuning
- **Full Team**: Cross-browser testing + Mobile testing

### Day 10 (Wednesday)
- **Full Team**: Final deployment setup
- **Full Team**: Documentation completion
- **Full Team**: MVP review and handoff

## Post-MVP Roadmap

### Week 3-4: Content Expansion
- Add 400 more words (total 500)
- Create 1500+ sentences
- Add Portuguese and Spanish content
- Improve sentence variety and grammar hints

### Week 5-6: Feature Enhancements  
- Advanced SM-2 features (context awareness)
- Image support for visual learning
- Enhanced statistics dashboard
- Export/import functionality

### Week 7-8: Polish & Optimization
- UI/UX improvements based on feedback
- Performance optimizations
- Mobile app considerations
- User testing and refinement

**Target Launch**: End of February 2025 (after 2 months total development)
