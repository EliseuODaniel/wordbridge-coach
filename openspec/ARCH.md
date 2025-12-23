# FillTheWord - Arquitetura de Sistema

## Visão Geral
Arquitetura local com 4 serviços containers Docker, comunicação via rede interna, cache de áudio em disco, funcionamento offline após setup inicial.

## Serviços (4 Containers)

### 1. API Service
**Função**: Backend principal com FastAPI, SRS SM-2, validação de respostas

**Stack**:
- FastAPI 0.104+ (Python 3.11+)
- SQLAlchemy 2.0 + Alembic
- PostgreSQL client (psycopg2)
- Pydantic models

**Porta**: 8000
**Dependências**: PostgreSQL (port 5432)

**Responsabilidades**:
- API REST endpoints (/api/cards/*)
- Algoritmo SM-2 completo
- Validação de respostas com tolerâncias
- Controle de sessões de estudo
- Cálculo de estatísticas básicas

### 2. Frontend Service  
**Função**: Interface React SPA para interação do usuário

**Stack**:
- React 18 + TypeScript
- Vite build system
- TailwindCSS styling
- Axios HTTP client

**Porta**: 3000
**Dependências**: API Service (port 8000)

**Responsabilidades**:
- Interface de estudo principal
- Exibição de cartões com gaps
- Formulário de resposta
- Feedback visual e áudio
- Navegação e configurações básicas

### 3. TTS Service
**Função**: Geração de áudio Text-to-Speech com cache em disco

**Stack**:
- FastAPI (Python)
- Coqui TTS + Piper TTS engines
- NumPy + librosa para processamento
- Models de voz por idioma

**Porta**: 8001
**Dependências**: Volume compartilhado de áudio

**Responsabilidades**:
- Geração de áudio para palavras e frases
- Cache persistente em sistema de arquivos
- Vozes configuradas por idioma
- API para gerenciar áudio cacheado

### 4. Database Service
**Função**: Persistência de dados PostgreSQL

**Stack**:
- PostgreSQL 15+ 
- PGAdmin (opcional, porta 5050)

**Porta**: 5432
**Volumes**: postgres_data (persistente)

**Responsabilidades**:
- Armazenamento de todos os dados
- Consistência ACID
- Backups automáticos
- Migrations via Alembic

## Comunicação entre Serviços

### Rede Interna
```yaml
networks:
  filltheword-net:
    driver: bridge
    internal: true  # Acesso apenas entre containers
```

### Port Mapping
```yaml
services:
  frontend:
    ports: ["3000:3000"]    # Acesso externo
  api:
    ports: ["8000:8000"]    # Acesso externo  
  tts:
    ports: ["8001:8001"]    # Acesso externo via API
  db:
    ports: ["5432:5432"]    # Acesso externo (debug apenas)
```

### API Dependencies
```mermaid
graph TD
    A[Frontend 3000] --> B[API 8000]
    B --> C[PostgreSQL 5432]
    A --> B
    B --> D[TTS 8001]
    D --> E[Audio Volume]
```

## Cache de Áudio em Disco

### Estrutura de Diretórios
```bash
audio/
├── en/
│   ├── word/
│   │   ├── abc123.wav      # "book"
│   │   └── def456.wav      # "table"
│   └── sentence/
│       ├── ghi789.wav      # "The book is on the table"
│       └── jkl012.wav      # "A cat sleeps here"
├── pt/
│   ├── word/
│   │   └── mno345.wav      # "livro"
│   └── sentence/
│       └── pqr678.wav      # "O livro está na mesa"
└── es/
    ├── word/
    └── sentence/
```

### Volume Compartilhado
```yaml
volumes:
  audio_cache:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ./audio
```

### Cache Logic
1. **Request**: API solicita áudio ao TTS
2. **Check**: TTS verifica se arquivo existe em disco
3. **Cache Hit**: Retorna arquivo estático via /api/audio/{path}
4. **Cache Miss**: Gera áudio, salva em disco, retorna
5. **Serving**: Frontend acessa via API ou diretamente se exposto

## Docker Compose Setup

### docker-compose.yml
```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    container_name: ftw-db
    environment:
      POSTGRES_DB: filltheword
      POSTGRES_USER: ftw_user
      POSTGRES_PASSWORD: ftw_password
    ports: ["5432:5432"]
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql
    networks: [filltheword-net]

  api:
    build: 
      context: ./api
      dockerfile: Dockerfile
    container_name: ftw-api
    environment:
      DATABASE_URL: postgresql://ftw_user:ftw_password@db:5432/filltheword
      TTS_SERVICE_URL: http://tts:8001
      AUDIO_CACHE_PATH: /audio
    ports: ["8000:8000"]
    volumes:
      - audio_cache:/audio
      - ./api:/app
    depends_on: [db]
    networks: [filltheword-net]
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  tts:
    build:
      context: ./tts  
      dockerfile: Dockerfile
    container_name: ftw-tts
    environment:
      AUDIO_CACHE_PATH: /audio
      MODELS_PATH: /models
    ports: ["8001:8001"]
    volumes:
      - audio_cache:/audio
      - tts_models:/models
    networks: [filltheword-net]
    command: uvicorn main:app --host 0.0.0.0 --port 8001

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: ftw-frontend
    environment:
      VITE_API_URL: http://localhost:8000
    ports: ["3000:3000"]
    volumes:
      - ./frontend:/app
      - /app/node_modules
    depends_on: [api]
    networks: [filltheword-net]
    command: npm run dev

volumes:
  postgres_data:
  audio_cache:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ./audio
  tts_models:

networks:
  filltheword-net:
    driver: bridge
```

## Deploy Local

### Setup Inicial
```bash
# Clonar repositório
git clone <repo>
cd filltheword

# Criar diretórios necessários
mkdir -p audio/{en,pt,es}/{word,sentence}
mkdir -p tts_models

# Iniciar serviços
docker-compose up -d

# Rodar migrations
docker-compose exec api alembic upgrade head

# Seed dados iniciais
docker-compose exec api python scripts/seed_data.py

# Baixar modelos TTS
docker-compose exec tts python scripts/download_models.py
```

### Acesso
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **TTS API**: http://localhost:8001/docs
- **Database**: localhost:5432 (development apenas)

## Performance e Monitoramento

### Métricas Chave
- **Startup time**: <30 segundos total
- **API response**: <200ms (95th percentile)
- **TTS generation**: <1500ms (cache miss)
- **TTS cache hit**: <20ms
- **Memory usage**: <2GB total
- **Disk usage**: <1GB (incluindo cache)

### Logs
```yaml
logging:
  version: 1
  formatters:
    default:
      format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  handlers:
    console:
      class: logging.StreamHandler
      formatter: default
  loggers:
    app:
      level: INFO
      handlers: [console]
```

### Health Checks
```bash
# API health
curl http://localhost:8000/health

# TTS health  
curl http://localhost:8000/health

# Database connection
docker-compose exec api python -c "from database import engine; print(engine.execute('SELECT 1').scalar())"
```

## Segurança

### Rede Interna
- Comunicação entre containers via rede bridge interna
- Apenas frontend/api expostos externamente
- Database acessível apenas internamente

### Variáveis de Ambiente
```bash
# .env file
DATABASE_URL=postgresql://user:password@localhost:5432/filltheword
TTS_SERVICE_URL=http://localhost:8001
SECRET_KEY=your-secret-key-here
```

### CORS (Frontend ↔ API)
```python
# FastAPI CORS setup
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Backup e Recuperação

### Database Backup
```bash
# Automatic daily backup
docker-compose exec db pg_dump -U ftw_user filltheword > backup_$(date +%Y%m%d).sql

# Restore backup
docker-compose exec -T db psql -U ftw_user filltheword < backup_20240115.sql
```

### Audio Cache
- Áudio gerado não versionado (re-gerável)
- Opcional: backup de áudios customizados
- Cleanup automático se disk usage > 500MB

## Escalabilidade (Futura)

### Vertical Scaling
- Mais CPU/RAM para TTS generation
- Storage SSD para cache rápido
- PostgreSQL tuning

### Horizontal Scaling  
- Load balancer para múltiplos API containers
- Redis cache compartilhado (se necessário)
- PostgreSQL read replicas

### Cloud Migration Path
- AWS ECS/EKS para containers
- RDS para PostgreSQL
- S3 para audio cache
- CloudFront para CDN
