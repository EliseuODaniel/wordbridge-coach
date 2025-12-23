# FillTheWord - Arquitetura Local MVP

## Visão Geral do Sistema
Arquitetura de 4 containers Docker focada em deployment local, offline-first. App self-contained sem dependências cloud externas durante uso.

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Host (Local)                     │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐     │
│  │ Frontend    │  │ API Service │  │ TTS Service     │     │
│  │ React       │  │ FastAPI     │  │ Python + Coqui  │     │
│  │ Port 3000   │  │ Port 8000   │  │ Port 8001       │     │
│  └─────────────┘  └─────────────┘  └─────────────────┘     │
│                      │                 │                  │
│                      ▼                 ▼                  │
│                ┌─────────────┐  ┌─────────────┐           │
│                │ PostgreSQL  │  │ Audio Cache │           │
│                │ Port 5432   │  │ /audio/     │           │
│                └─────────────┘  └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

## Serviços

### 1. Frontend Service (React)
**Porta**: 3000  
**Responsabilidade**: Interface do usuário, client-side routing, TTS playback

**Tech Stack**:
- React 18 + TypeScript
- Vite (build tool + dev server)
- TailwindCSS (styling)
- React Router (navigation)
- axios (HTTP client)
- HTML5 Audio API (TTS playback)

**Dockerfile**:
```dockerfile
FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy source code
COPY . .

# Build for production
RUN npm run build

# Serve with nginx for production
FROM nginx:alpine
COPY --from=0 /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
```

**nginx.conf**:
```nginx
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    
    server {
        listen 3000;
        server_name localhost;
        root /usr/share/nginx/html;
        index index.html;
        
        # React Router support
        location / {
            try_files $uri $uri/ /index.html;
        }
        
        # API proxy (development)
        location /api/ {
            proxy_pass http://api:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
        
        # Static file caching
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

**Performance Features**:
- Static asset optimization (gzip)
- Lazy loading de componentes
- Service Worker para cache offline
- Bundle splitting por rota
- Audio preloading estratégico

### 2. API Service (FastAPI)
**Porta**: 8000  
**Responsabilidade**: Core business logic, SM-2 algorithm, audio cache management

**Tech Stack**:
- FastAPI + Python 3.11
- SQLAlchemy ORM + Alembic migrations
- Pydantic models (validation/serialization)
- PostgreSQL driver (psycopg2)
- HTTP client (for TTS service)

**Service Structure**:
```python
app/
├── api/
│   ├── deps.py          # Dependencies (DB, TTS client)
│   ├── cards.py         # Card selection & answer validation
│   ├── tts.py           # TTS endpoints & cache management
│   ├── decks.py         # Content discovery
│   └── system.py        # Health check & stats
├── core/
│   ├── config.py        # Environment variables
│   ├── database.py      # DB connection
│   └── cache.py         # Audio cache management
├── models/
│   ├── card.py          # Card entity
│   ├── word.py          # Word entity  
│   ├── deck.py          # Deck entity
│   └── progress.py      # SM-2 progress
├── services/
│   ├── sm2.py           # Spaced repetition algorithm
│   ├── validation.py    # Answer validation
│   └── tts_client.py    # TTS service client
└── main.py
```

**Dependencies**:
- PostgreSQL: Cards, words, progress, cache metadata
- TTS Service: External service for audio generation
- File System: Audio cache files

**Key Features**:
- SM-2 algorithm implementation
- Answer validation with tolerance
- Audio cache management
- Database connection pooling
- Static file serving for cached audio

### 3. TTS Service (Python + Coqui/Piper)
**Porta**: 8001  
**Responsabilidade**: Text-to-speech generation, voice management

**Tech Stack**:
- Python 3.11 + FastAPI
- Coqui TTS XTTS-v2 (high quality multilingual)
- Piper TTS (fast, lightweight alternative)
- Asyncio for concurrent generation
- FFmpeg (audio processing optimization)

**Service Features**:
- Multi-voice support per language
- Adjustable speech rate (0.5x - 2.0x)
- Audio format optimization (WAV 22kHz mono)
- Batch generation support
- Voice model management

**Voice Configuration**:
```python
VOICES = {
    "en": {
        "primary": "lessac-glow_tts",
        "fallback": "vctk-glow_tts",
        "speed": 1.0
    },
    "pt": {
        "primary": "pt_br_female-glow_tts", 
        "fallback": "pt_br_male-glow_tts",
        "speed": 1.0
    },
    "es": {
        "primary": "es_male-glow_tts",
        "fallback": "es_female-glow_tts", 
        "speed": 1.0
    }
}
```

**TTS Endpoints**:
```python
@app.post("/generate")
async def generate_audio(request: TTSRequest):
    voice = VOICES.get(request.language, {}).get("primary")
    
    # Generate audio with Coqui TTS
    audio_data = await generate_tts(
        text=request.text,
        voice=voice,
        speed=request.speed
    )
    
    return {
        "audio_data": base64.b64encode(audio_data).decode(),
        "duration_ms": len(audio_data) / 44.1,  # Rough estimate
        "voice_used": voice
    }

@app.get("/voices/{language}")
async def get_voices(language: str):
    return VOICES.get(language, {})
```

### 4. Database Service (PostgreSQL)
**Porta**: 5432  
**Responsabilidade**: Persistent data storage com ACID guarantees

**Configuration**:
- Version: PostgreSQL 15
- Extensions: uuid-ossp (UUID generation)
- Character encoding: UTF-8
- Connection pooling: pgBouncer integration
- Backup strategy: pg_dump daily

**Database Schema**:
```sql
-- Core tables (simplified from DOMAINS.md)
languages          -- Supported languages (en, pt, es)
decks              -- Content categories
words              -- Vocabulary entries  
synonyms           -- Answer synonyms
cards              -- Sentence + word combinations
card_progress      -- SM-2 progress tracking
audio_cache        -- TTS cache metadata
```

**Optimizations**:
- **Indexes on foreign keys** + query patterns
- **Composite indexes** for SM-2 card selection
- **Partial indexes** for active cards only
- **Connection pooling**: max 20 connections
- **Query optimization** with EXPLAIN ANALYZE

**Index Strategy**:
```sql
-- SM-2 card selection optimization
CREATE INDEX idx_card_progress_next_review ON card_progress(next_review) 
WHERE sm2_level IN ('learning', 'review', 'mature');

-- Card discovery optimization  
CREATE INDEX idx_cards_language_difficulty ON cards(language_id, difficulty)
WHERE is_active = true;

-- TTS cache optimization
CREATE INDEX idx_audio_cache_hash ON audio_cache(text_hash, language_id);
```

## Infrastructure Local

### Docker Compose Configuration
```yaml
version: '3.8'

services:
  # Frontend Service
  frontend:
    build: 
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000
    depends_on:
      - api
    restart: unless-stopped

  # API Service  
  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/filltheword
      - TTS_SERVICE_URL=http://tts:8001
      - AUDIO_CACHE_PATH=/app/audio
    volumes:
      - audio_cache:/app/audio
    depends_on:
      - db
      - tts
    restart: unless-stopped

  # TTS Service
  tts:
    build:
      context: ./tts-service  
      dockerfile: Dockerfile
    ports:
      - "8001:8001"
    environment:
      - VOICE_MODELS_PATH=/app/models
      - CACHE_PATH=/app/audio
    volumes:
      - audio_cache:/app/audio
      - voice_models:/app/models
    restart: unless-stopped

  # Database Service
  db:
    image: postgres:15
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=filltheword
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
    restart: unless-stopped

volumes:
  postgres_data:
    driver: local
  audio_cache:
    driver: local  
  voice_models:
    driver: local
```

### Audio Cache System

**Directory Structure**:
```
audio_cache/
├── en/
│   ├── sentence/
│   │   ├── abc123def456.wav    # "The book is on the table"
│   │   ├── def456ghi789.wav    # "A cat sleeps on the sofa"
│   │   └── ...
│   └── word/
│       ├── word123abc.wav      # "book"
│       ├── word456def.wav      # "cat"  
│       └── ...
├── pt/
│   ├── sentence/
│   └── word/
└── es/
    ├── sentence/
    └── word/
```

**Cache Management**:
```python
class AudioCacheManager:
    def __init__(self, cache_root: str = "/app/audio"):
        self.cache_root = Path(cache_root)
    
    def get_cache_path(self, text: str, language: str, 
                      audio_type: str, voice: str) -> Path:
        # Create hash from text + voice for consistent naming
        hash_input = f"{text}_{voice}"
        text_hash = hashlib.md5(hash_input.encode()).hexdigest()
        
        return (
            self.cache_root / language / audio_type / f"{text_hash}.wav"
        )
    
    def cache_exists(self, cache_path: Path) -> bool:
        return cache_path.exists() and cache_path.stat().st_size > 0
    
    def save_to_cache(self, audio_data: bytes, cache_path: Path):
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, 'wb') as f:
            f.write(audio_data)
        
        # Save metadata to database
        self.save_cache_metadata(cache_path, audio_data)
```

**Cache Statistics**:
- **File size**: ~50KB per word, ~200KB per sentence
- **Growth rate**: ~5MB per 100 cards reviewed
- **Cleanup strategy**: Manual cleanup based on usage statistics
- **Backup strategy**: Include in daily file system backup

## Data Flow Examples

### 1. Get Next Card Flow
```
Frontend → API: GET /api/cards/next
API → DB: Query card_progress with SM-2 algorithm
API ← DB: Selected card data
API → API: Load progress information
API ← API: Complete card with SM-2 state
Frontend ← API: Card ready for display
```

### 2. Submit Answer Flow  
```
Frontend → API: POST /api/cards/{id}/answer
API → API: Validate answer (case, synonyms, tolerance)
API → DB: Update SM-2 progress
API ← DB: Updated progress state
API → TTS: Generate pronunciation audio (if needed)
API ← TTS: Audio URLs or cache hit
Frontend ← API: Results + audio URLs
```

### 3. TTS Generation Flow
```
API → TTS: POST /generate (text, language, voice)
TTS → Cache: Check if audio already exists
If cache miss:
  TTS → Coqui: Generate audio from text
  TTS → Cache: Save audio to shared volume
  TTS → DB: Update audio_cache metadata
API ← TTS: Audio data or cache hit info
API → Cache: Save to API cache directory
API ← Cache: File path for serving
```

## Performance Targets

### Response Times (Local Deployment)
- **Card selection**: < 100ms (database query with indexes)
- **Answer validation**: < 50ms (in-memory + DB update)  
- **TTS cache hit**: < 20ms (static file serving)
- **TTS generation**: 500-1500ms (first time only)
- **Static file serving**: < 10ms

### Resource Requirements
- **Minimum RAM**: 4GB total
  - Frontend: 256MB
  - API: 512MB  
  - TTS: 1GB (models loaded)
  - Database: 512MB
  - System/Cache: 1.5GB
- **Storage**: 2GB minimum
  - Database: 100MB
  - Voice models: 500MB
  - Audio cache: 1GB+ (grows with usage)
- **CPU**: 2+ cores recommended (parallel TTS generation)

### Throughput (Single User)
- **Cards per minute**: 10-15 cards (including audio)
- **Audio generation**: 2-3 concurrent requests
- **Database connections**: 5-10 active connections
- **File I/O**: < 1MB/s during normal usage

## Deployment Guide

### Development Setup
```bash
# Clone repository
git clone <repo_url>
cd filltheword

# Start all services
docker-compose up -d

# Initialize database
docker-compose exec api alembic upgrade head
docker-compose exec api python scripts/seed_data.py

# Download TTS models
docker-compose exec tts python scripts/download_models.py

# Access application
open http://localhost:3000
```

### Production Deployment
```bash
# Production configuration
cp docker-compose.yml docker-compose.prod.yml
# Edit production settings:
# - Environment variables
# - Resource limits  
# - Backup schedules
# - Log configuration

# Deploy
docker-compose -f docker-compose.prod.yml up -d

# Setup daily backup
crontab -e
# Add: 0 2 * * * /path/to/backup_script.sh
```

### Monitoring (Local)
```bash
# Service health
curl http://localhost:8000/api/health

# Database status  
docker-compose exec db pg_isready

# TTS service status
curl http://localhost:8001/health

# Disk usage
df -h
du -sh audio_cache/
```

## Security Considerations

### Local Deployment Security
- **Network isolation**: Containers em bridge network interna
- **No external exposure**: Apenas portas 3000, 8000 expostas para localhost
- **Database security**: Strong password, limited connections
- **File permissions**: Proper ownership for audio cache
- **Input validation**: Sanitize all text inputs para TTS

### Data Protection
- **Local storage only**: Nenhum dado enviado para serviços externos
- **Backup encryption**: Encrypt backups se conterem dados sensíveis
- **Access control**: Local filesystem permissions adequadas
- **Input sanitization**: Prevenir injection attacks em TTS generation

## Troubleshooting Guide

### Common Issues

**TTS Generation Slow**:
```bash
# Check voice model download
docker-compose exec tts ls -la /app/models/
# Check TTS service logs
docker-compose logs tts
# Monitor resource usage
docker stats
```

**Database Slow Queries**:
```bash
# Check database connections
docker-compose exec db psql -U postgres -d filltheword -c "SELECT count(*) FROM pg_stat_activity;"
# Analyze slow queries
docker-compose exec db psql -U postgres -d filltheword -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

**Audio Cache Issues**:
```bash
# Check cache directory
docker-compose exec api ls -la /app/audio/
# Check permissions
docker-compose exec api ls -ld /app/audio/
# Clear cache if needed
docker-compose exec api rm -rf /app/audio/*
```

### Performance Tuning

**Database Optimization**:
```sql
-- Analyze table statistics
ANALYZE cards;
ANALYZE card_progress;

-- Rebuild indexes if needed
REINDEX DATABASE filltheword;

-- Check query plan
EXPLAIN ANALYZE SELECT * FROM cards WHERE difficulty <= 3;
```

**Memory Optimization**:
```yaml
# docker-compose.yml
services:
  tts:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```
