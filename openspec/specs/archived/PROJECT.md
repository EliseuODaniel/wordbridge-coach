# FillTheWord - Projeto de Aprendizado de Vocabulário

## Contexto
FillTheWord é um aplicativo local de aprendizado de vocabulário que apresenta frases com lacunas para preenchimento. O sistema funciona offline, utiliza TTS (Text-to-Speech) local, valida respostas com tolerância a variações, e implementa spaced repetition algoritmo SM-2 para progressão.

**Stack Tecnológica**: FastAPI + React + Coqui/Piper TTS + PostgreSQL + Docker Compose  
**Foco**: App local, 4 containers, cache de áudio em disco, sem dependências cloud

## Stack Tecnológica

### Backend
- **FastAPI**: Framework web Python para API REST
- **PostgreSQL**: Banco de dados relacional
- **SQLAlchemy**: ORM para acesso ao banco
- **Alembic**: Migrações de banco
- **Coqui TTS / Piper TTS**: Síntese de voz multilíngue local
- **Docker**: Containerização do backend

### Frontend
- **React**: Framework JavaScript UI
- **TypeScript**: Tipagem estática
- **Vite**: Build tool e dev server
- **TailwindCSS**: Framework CSS
- **axios**: Cliente HTTP

### Infraestrutura
- **Docker Compose**: Orquestração de 4 containers
- **PostgreSQL**: Container do banco de dados
- **Sistema de arquivos**: Cache de áudio local

## Princípios de Design

### 1. Simplicidade do Usuário
- Interface limpa e focada no aprendizado
- Feedback imediato de respostas
- Progressão gradual com SRS SM-2

### 2. Performance Local
- TTS cacheado em disco para reprodução instantânea
- API responses otimizados (< 200ms)
- Sem dependências externas durante uso

### 3. Funcionamento Offline
- Cache de áudio em disco: `audio/<lang>/<type>/<slug>.wav`
- Funciona sem conexão internet (após setup inicial)
- Armazenamento local de progresso

### 4. Acessibilidade
- Suporte a múltiplos idiomas (en, pt, es)
- Interface responsiva
- Teclado navigation support
- TTS para conteúdo completo

### 5. Aprendizado Efetivo
- Algoritmo SM-2 de repetição espaçada
- Tolerância a variações (case, plural, artigos)
- Sistema de dicas gramaticais contextuais

## Estrutura do Projeto

```
filltheword/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── cards.py     # Core card API
│   │   │   └── tts.py       # TTS endpoints
│   │   ├── core/
│   │   │   ├── config.py    # Environment
│   │   │   └── database.py  # DB connection
│   │   ├── models/
│   │   │   ├── card.py      # Card entity
│   │   │   ├── word.py      # Word entity
│   │   │   └── deck.py      # Deck entity
│   │   ├── services/
│   │   │   ├── sm2.py       # Spaced repetition SM-2
│   │   │   └── tts.py       # TTS service
│   │   └── main.py
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Card.tsx     # Main card interface
│   │   │   ├── AudioPlayer.tsx # TTS controls
│   │   │   └── ProgressBar.tsx # Progress indicator
│   │   ├── pages/
│   │   │   └── Study.tsx    # Main study page
│   │   ├── services/
│   │   │   └── api.ts       # API client
│   │   └── App.tsx
│   └── package.json
├── docker-compose.yml        # 4 services: api, frontend, tts, db
├── audio/                    # TTS cache directory
└── README.md
```

## Arquitetura de Containers

```yaml
services:
  frontend:    # React + Vite (Port 3000)
  api:         # FastAPI + PostgreSQL (Port 8000)  
  tts:         # Coqui/Piper TTS (Port 8001)
  db:          # PostgreSQL (Port 5432)
```

**Volumes Compartilhados**:
- `postgres_data`: Persistência do banco
- `audio_cache`: Cache TTS compartilhado entre api e tts

## Escopo do MVP

### Funcionalidades Incluídas
- Core learning loop: card → answer → feedback → next
- TTS para frases e palavras (cache local)
- Spaced repetition SM-2 básico
- Tolerância a variações de resposta
- Sistema de dicas gramaticais

### Funcionalidades Excluídas (para MVP)
- Sistema de autenticação/users
- Dashboards de estatísticas
- Gerenciamento de conteúdo/admin
- Sessões de estudo tracking
- Analytics complexos

## Metas do Projeto

1. **MVP v0.1**: Jogo funcional com TTS local e SRS SM-2
2. **v0.2**: Expansão de conteúdo (mais idiomas/decks)
3. **v0.3**: Melhorias no algoritmo SRS e interface
4. **v1.0**: Aplicativo local completo e robusto
