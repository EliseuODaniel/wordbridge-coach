# FillTheWord MVP - Vocabulary Learning with SRS

A Complete Fill-in-the-Gap vocabulary learning application with spaced repetition system (SRS) based on the SM-2 algorithm, featuring local Text-to-Speech (TTS) and comprehensive learning analytics.

## 🎯 Features Implemented (RF-01 to RF-06)

### ✅ RF-01: Card with Gap Display
- **Gap visualization**: Clear "___" placeholders in sentences
- **Memory indicator**: 0-4 bolinhas showing SM-2 memory stage
- **Translation display**: Full sentence translations in Portuguese
- **Grammar hints**: Contextual hints for each word
- **Visual feedback**: Color-coded memory stages (gray → yellow → blue → green)

### ✅ RF-02: Smart Answer Validation
- **Case insensitive**: "Book" = "book" = "BOOK"
- **Accent removal**: "café" = "cafe"
- **Article tolerance**: "book" accepts "a book"/"the book" based on context
- **Synonym support**: "color" accepts "colour" (configurable per word)
- **Progressive hints**: 4-level hint system with increasing specificity
- **Visual feedback**: ✅ correct, ❌ incorrect, 💡 hints

### ✅ RF-03: Audio TTS with Cache
- **Word pronunciation**: Audio for target vocabulary
- **Sentence audio**: Full sentence context with proper pronunciation
- **Disk caching**: `audio/<lang>/<type>/<slug>.wav` structure
- **Cache optimization**: <20ms cache hit, <1500ms generation
- **Multi-language support**: English (primary), Portuguese, Spanish
- **Fallback handling**: Graceful degradation when TTS unavailable

### ✅ RF-04: Study Session Management
- **Session counters**: Cards studied, new cards, accuracy percentage
- **Daily limits**: Configurable new cards per day (default: 10)
- **Progress tracking**: Real-time session statistics
- **Study streak**: Daily learning streak counter
- **Session persistence**: State maintained across restarts

### ✅ RF-05: Basic Statistics Dashboard
- **Progress overview**: Total cards, studied cards, mastered cards
- **SM-2 distribution**: New, Learning, Review, Mature card counts
- **Success rate**: Overall accuracy percentage
- **Study metrics**: Session performance and streaks

### ✅ RF-06: Configuration Management
- **SRS parameters**: Adjustable easiness factor (1.3-2.5)
- **Daily limits**: New cards per day (5-20, default: 10)
- **Review settings**: Algorithm customization options
- **User preferences**: Interface and behavior settings

## 🏗️ Architecture

### 4-Service Docker Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Service   │    │   TTS Service   │    │   PostgreSQL    │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (FastAPI)     │◄──►│   Database      │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 8001    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Core Technologies
- **Backend**: FastAPI + SQLAlchemy + PostgreSQL + Alembic
- **Frontend**: React 18 + TypeScript + Vite + TailwindCSS
- **TTS**: Piper TTS + Coqui TTS engines
- **Database**: PostgreSQL 15 with full-text search
- **Containerization**: Docker + Docker Compose

### Algorithm Implementation
- **SM-2 Algorithm**: Complete implementation with quality scores 0-5
- **Memory Stages**: New → Learning → Review → Mature progression
- **Answer Tolerance**: Multiple validation strategies
- **Interval Calculation**: Exponential growth with easiness factor

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
  - **Docker Compose V2** (recommended): `docker compose` command
  - **Legacy V1** (also supported): `docker-compose` command
- Git for cloning the repository
- For **WSL2 users**: Enable Docker Desktop WSL2 integration

### Setup and Run
```bash
# Clone the repository
git clone <repository-url>
cd filltheword

# Run the quick start script
./scripts/quick_start.sh
```

### WSL2 Notes
If you're using WSL2 on Windows:
1. Install Docker Desktop for Windows
2. Enable **WSL2 Integration** in Docker Desktop Settings:
   - Settings → Resources → WSL Integration
   - Enable your WSL2 distro (e.g., Ubuntu)
3. Verify: `docker compose version` (should work in WSL2 terminal)
4. Frontend URL: `http://localhost:3007` (mapped from 3000 in container)

### Manual Setup
```bash
# Create directories
mkdir -p audio/{en,pt,es}/{word,sentence} tts_models

# Start services (Docker Compose V2)
docker compose up -d --build

# OR for legacy Docker Compose V1
docker-compose up -d --build

# Wait for services to be ready
sleep 30

# Seed the database
docker-compose exec api python scripts/seed_data.py

# Access the application
open http://localhost:3007  # Note: mapped from container port 3000
```

### Service URLs
- **Frontend**: http://localhost:3007 (mapped from container port 3000)
- **API Documentation**: http://localhost:8000/docs
- **TTS Service**: http://localhost:8001/health
- **Database**: localhost:5432 (user: ftw_user, password: ftw_password)

## 📚 API Endpoints

### Core Learning API
```bash
# Get next card for study
GET /api/v1/cards/next
# Returns: Card with gap, translation, hints, memory stage

# Submit answer
POST /api/v1/cards/{card_id}/answer
# Body: {"answer": "book", "response_time_ms": 3200}
# Returns: Feedback with SM-2 update
```

### TTS Audio API
```bash
# Generate word audio
GET /api/tts/word/{id}?text=book&lang=en

# Generate sentence audio  
GET /api/tts/sentence/{id}?text=The book is on the table&lang=en

# Access cached audio
GET /api/audio/en/word/abc123.wav
```

## 🎯 Learning Workflow

1. **Card Presentation**: User sees sentence with gap, translation, and hints
2. **Memory Indicator**: Visual progress shown via colored dots (0-4)
3. **Audio Practice**: Optional pronunciation for word and sentence
4. **Answer Input**: Type the missing word
5. **Validation**: Smart tolerance checking with immediate feedback
6. **Progressive Hints**: Up to 4 levels of hints for incorrect answers
7. **SM-2 Update**: Algorithm adjusts review intervals based on performance
8. **Next Card**: Automatic progression based on readiness and daily limits

## 🔧 Development

### Project Structure
```
filltheword/
├── api/                 # FastAPI backend service
│   ├── app/
│   │   ├── models/     # SQLAlchemy models (SM-2 entities)
│   │   ├── api/        # API endpoints
│   │   ├── services/   # Business logic (SM-2 algorithm)
│   │   └── schemas/    # Pydantic models
│   ├── alembic/        # Database migrations
│   └── Dockerfile
├── frontend/           # React TypeScript frontend
│   ├── src/
│   │   ├── components/ # React components (RF-01 to RF-06)
│   │   ├── services/   # API and audio services
│   │   └── types/      # TypeScript definitions
│   ├── Dockerfile
│   └── nginx.conf
├── tts/                # Text-to-Speech service
│   ├── app/
│   │   ├── services/   # TTS engine with caching
│   │   └── api/        # Audio generation endpoints
│   └── Dockerfile
├── audio/              # Persistent audio cache
├── scripts/            # Database seeding and utilities
└── docker-compose.yml  # Multi-service orchestration
```

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5432/filltheword

# API Settings
DEBUG=true
SECRET_KEY=your-secret-key

# TTS Configuration  
AUDIO_CACHE_PATH=./audio
TTS_MODELS_PATH=./tts_models

# SRS Settings
DEFAULT_EASINESS_FACTOR=2.5
DEFAULT_NEW_CARDS_PER_DAY=10
```

## 📊 Database Schema

### Core Entities
- **User**: Individual learning profiles with preferences
- **UserCardState**: SM-2 progress tracking per card
- **Card**: Study content with gap positions
- **Sentence**: Source text with translations
- **Word**: Vocabulary items with metadata
- **ReviewEvent**: Detailed analytics for each interaction
- **Language**: Multi-language support configuration
- **Deck**: Content organization by difficulty

### SM-2 Implementation
```python
# Quality calculation based on response
quality = SM2Algorithm.calculate_quality_from_response(
    was_correct=True,
    response_time_ms=2500,
    hints_used=0,
    attempts=1
)  # Returns 5 (perfect score)

# Next review calculation
next_review = SM2Algorithm.calculate_next_review(
    quality=5,
    current_repetitions=2,
    current_easiness_factor=2.5,
    current_interval_days=1
)  # Returns next interval and review time
```

## 🔍 Testing and Validation

### Test Scenarios
1. **Complete Learning Loop**: Card → Answer → Feedback → Next
2. **Answer Validation**: Case, accents, synonyms, articles tolerance
3. **TTS Integration**: Word/sentence audio generation and caching
4. **SM-2 Progression**: New → Learning → Review → Mature transitions
5. **Session Management**: Daily limits, counters, persistence
6. **Progress Statistics**: Dashboard accuracy and distribution

### Performance Targets
- **API Response**: <100ms (card selection), <50ms (answer validation)
- **TTS Generation**: <1500ms (cache miss), <20ms (cache hit)
- **Frontend Load**: <2s initial load
- **Memory Usage**: <2GB total system usage

## 🛠️ Commands

### Docker Management
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild services
docker-compose up -d --build
```

### Database Operations
```bash
# Run migrations
docker-compose exec api alembic upgrade head

# Seed data
docker-compose exec api python scripts/seed_data.py

# Access database
docker-compose exec db psql -U ftw_user -d filltheword
```

### Development
```bash
# Frontend development
cd frontend && npm run dev

# API development
cd api && source venv/bin/activate && python -m uvicorn app.main:app --reload

# TTS development  
cd tts && python -m uvicorn app.main:app --reload
```

## 🎨 UI Components

### Study Interface (RF-01/02)
- **CardDisplay**: Gap visualization with memory indicator
- **AnswerInput**: Input field with keyboard navigation
- **FeedbackMessage**: Progressive hints and corrections
- **AudioButton**: TTS integration for words/sentences

### Session Management (RF-04/05/06)
- **SessionCounter**: Progress tracking and statistics
- **StatsDashboard**: Learning analytics and distribution
- **SettingsForm**: Configuration management interface

## 🌍 Multi-Language Support

### Currently Supported
- **English**: Primary learning language (American accent)
- **Portuguese**: Interface translations (Brazilian Portuguese)
- **Spanish**: Future expansion ready (neutral accent)

### Adding New Languages
1. Add language configuration in TTS service
2. Add voice models for pronunciation
3. Update translation files
4. Seed vocabulary for new language pair

## 📈 Content and Analytics

### Initial Vocabulary
- **100+ words**: High-frequency English vocabulary
- **300+ sentences**: 3 sentences per word average
- **3 difficulty levels**: Beginner to intermediate content
- **Grammar hints**: Contextual learning support

### Analytics Tracking
- **SM-2 Metrics**: Repetitions, intervals, success rates
- **Session Data**: Time spent, cards studied, accuracy
- **Progress Analytics**: Learning curves and retention rates

## 🔜 Future Enhancements

### Content Expansion
- **500+ words**: Extended vocabulary corpus
- **Multi-directional**: EN→PT, PT→EN learning pairs
- **Corpora Pipeline**: Automated content from Tatoeba/ParaCrawl
- **Adaptive Difficulty**: Personalized content selection

### Feature Enhancements
- **Advanced Statistics**: Detailed learning analytics
- **Social Features**: Leaderboards and sharing
- **Mobile App**: Native iOS/Android applications
- **Cloud Sync**: Cross-device progress synchronization

## 🤝 Contributing

### Development Workflow
1. Create feature branch from `main`
2. Implement changes with tests
3. Update documentation
4. Submit pull request with description
5. Code review and merge

### Code Standards
- **Python**: Black formatting, type hints, docstrings
- **TypeScript**: ESLint + Prettier, strict typing
- **Git**: Conventional commits, descriptive PRs
- **Testing**: Unit tests for core logic, integration tests

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **SM-2 Algorithm**: Original spaced repetition research
- **TTS Engines**: Piper TTS and Coqui TTS communities
- **FastAPI**: Modern Python web framework
- **React**: Component-based UI development
- **Open Source**: The broader open-source community

---

**Happy Learning! 📖✨**

For questions, issues, or contributions, please visit the project repository or contact the development team.
