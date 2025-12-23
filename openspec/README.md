# FillTheWord OpenSpec Documentation

## Status: Alinhado com Texto-Base Definitivo (seções 0-10)

## Estrutura Atual
```
openspec/
├── README.md                    # Este arquivo
├── PROJECT.md                   # Contexto completo e stack local
├── SPEC.md                      # Requisitos funcionais RF-01..RF-06
├── DOMAINS.md                   # Modelo de domínio completo
├── API.md                       # Endpoints essenciais alinhados
├── ARCH.md                      # Arquitetura 4 serviços local
├── CHANGE_SUMMARY.md            # Resumo das mudanças realizadas
├── changes/
│   └── 2025-02-filltheword-base.md # Documento de change
├── tasks/
│   └── 2025-02-filltheword-local-mvp.md # Timeline implementação
└── specs/
    └── archived/                # Arquivos antigos preservados
        ├── README.md            # Explicação do arquivamento
        ├── PROJECT.md           # Versões anteriores
        ├── SPEC.md              # Versões anteriores
        ├── DOMAINS.md           # Versões anteriores
        ├── API.md               # Versões anteriores
        ├── ARCH.md              # Versões anteriores
        └── 2025-12-filltheword-mvp.md # Versão anterior
```

## Visão Geral do Projeto

FillTheWord é um aplicativo de aprendizado de vocabulário focado em preenchimento de lacunas com:

- **Funcionamento**: Totalmente local/offline via Docker containers
- **Algoritmo**: SRS SM-2 completo com quality 0-5, easiness_factor >= 1.3
- **TTS**: Coqui/Piper local com cache em disco
- **Idiomas**: EN/ES/FR/PT suportados
- **Stack**: FastAPI + React + PostgreSQL + Docker Compose

## Stack Tecnológica

### Backend API
- FastAPI (Python 3.11+)
- PostgreSQL 15+ com SQLAlchemy 2.0
- Algoritmo SM-2 implementado localmente
- Validação tolerante de respostas

### Frontend  
- React 18 + TypeScript
- Vite + TailwindCSS
- Interface responsiva offline-first

### TTS Service
- Coqui TTS / Piper TTS
- Modelos locais por idioma
- Cache persistente: `audio/<lang>/<type>/<slug>.wav`

### Infraestrutura
- Docker + Docker Compose
- 4 serviços (api, frontend, tts, db)
- Volumes persistentes para dados e áudio

## Requisitos Funcionais (RF-01..RF-06)

✅ **RF-01**: Cartão com lacuna, tradução, dica gramatical, indicador visual memória (0–4 bolinhas)  
✅ **RF-02**: Validação tolerante (case/acentos/sinônimos), dicas progressivas  
✅ **RF-03**: Áudio TTS local com cache em disco  
✅ **RF-04**: Sessão estudo com contador e limite novos/dia  
✅ **RF-05**: Estatísticas básicas de progresso  
✅ **RF-06**: Configuração revisão (limites, algoritmo SM-2)  

## Modelo de Domínio

Entidades principais alinhadas ao texto-base:
- **User**: native_language, target_language
- **Language**: EN/ES/FR/PT com vozes TTS específicas
- **Word**: lemma, part_of_speech, features (JSON)
- **UserCardState**: SM-2 completo (repetitions, easiness_factor, interval_days)
- **ReviewEvent**: quality 0-5, response_time_ms

## API Endpoints

Endpoints essenciais conforme texto-base:
- **GET /api/cards/next**: Seleção SM-2 com resposta exata
- **POST /api/cards/{id}/answer**: Validação + update SM-2
- **GET /api/tts/**: Áudio cacheado
- **POST /tts**: Opção para geração de áudio

## Corpora Pipeline

Fontes de dados offline:
- **Tatoeba**: Sentenças paralelas com tradução
- **ParaCrawl**: Corpus paralelo de alta qualidade  
- **OpenSubtitles**: Legendas de filmes/series

## Workflow OpenSpec

### Instalação CLI
```bash
npm i -g @fission-ai/openspec
```

### Estrutura Padrão
```
openspec/
├── PROJECT.md    # Contexto e stack
├── SPEC.md       # Requisitos funcionais
├── DOMAINS.md    # Modelo de domínio
├── API.md        # Endpoints e exemplos
├── ARCH.md       # Arquitetura e deploy
└── TASKS.md      # Timeline de implementação
```

### Ciclo de Vida
1. **Proposal**: Criar proposta de mudança em `changes/`
2. **Apply**: Aplicar mudanças nos arquivos principais
3. **Archive**: Mover versões antigas para `specs/archived/`

## Setup e Deploy

### Inicialização
```bash
git clone <repo>
cd filltheword
docker-compose up -d
docker-compose exec api alembic upgrade head
docker-compose exec api python scripts/seed_data.py
```

### Acesso
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs  
- **TTS API**: http://localhost:8001/docs

## Validação Final

✅ **Texto-Base Alinhado**: Todas as seções 0-10 implementadas  
✅ **Domínio Completo**: User/UserCardState/ReviewEvent entities  
✅ **SM-2 Completo**: quality 0-5, easiness_factor >= 1.3  
✅ **API Correta**: Payloads exatos do texto-base  
✅ **4 Serviços**: api, frontend, tts, db containers  
✅ **Local/Offline**: Funcionamento sem internet  
✅ **Corpora**: Pipeline Tatoeba/ParaCrawl/OpenSubtitles  

## Próximos Passos

1. **Implementação**: Seguir tasks em `tasks/2025-02-filltheword-local-mvp.md`
2. **Review**: Validar especificações com time técnico
3. **Development**: In implementação seguindo arquiterura definida
4. **Testing**: Validar funcionamento offline e SM-2

## Contato

Para dúvidas sobre as especificações:
- Referenciar change document em `changes/`
- Consultar arquivos arquivados para histórico
- Seguir estrutura OpenSpec padrão
