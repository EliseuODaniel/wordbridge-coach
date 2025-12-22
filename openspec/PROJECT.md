# FillTheWord - Project Context

## Overview
FillTheWord é um aplicativo de aprendizado de vocabulário focado em preenchimento de lacunas, utilizando algoritmo SRS SM-2 e TTS local. Funciona como aplicativo local/offline com arquitetura baseada em containers.

## Context
App local, offline-first com seguintes características:
- **Funcionamento**: Totalmente local após setup inicial
- **Stack**: FastAPI + React + Coqui/Piper + PostgreSQL + docker-compose  
- **Arquitetura**: 4 serviços (api, frontend, tts, db)
- **Cache**: Áudio em disco, não Redis/cloud
- **Dados**: Corpora offline (Tatoeba/ParaCrawl/OpenSubtitles)

## Stack Tecnológica

### Backend API
- **Framework**: FastAPI (Python 3.11+)
- **Banco**: PostgreSQL 15+
- **ORM**: SQLAlchemy 2.0 com Alembic
- **SRS**: Algoritmo SM-2 implementado localmente
- **Auth**: Simples (sem JWT complexo)

### Frontend
- **Framework**: React 18 com TypeScript
- **Build**: Vite
- **Estilos**: TailwindCSS
- **Estado**: React Context + useState
- **Comunicação**: Axios

### TTS Service
- **Engine**: Coqui TTS / Piper TTS
- **Vozes**: Modelos locais por idioma
- **Cache**: Sistema de arquivos em disco
- **API**: FastAPI dedicado

### Infraestrutura
- **Containers**: Docker + Docker Compose
- **Banco**: PostgreSQL container persistente
- **Volumes**: postgres_data + audio_cache
- **Rede**: Docker network interna

## Princípios

### 1. Simplicidade
- Mínimo de dependências externas
- Interface direta e intuitiva
- Setup rápido com docker-compose

### 2. Performance Local
- Respostas rápidas (<200ms)
- Cache agressivo de áudio em disco
- Seleção eficiente de cartões SM-2

### 3. Offline-First
- Funcionamento completo sem internet
- Todos os dados armazenados localmente
- Sincronização apenas se necessário no futuro

### 4. Qualidade de Áudio
- TTS de alta qualidade local
- Cache inteligente por idioma/tipo
- Pronúncia precisa para aprendizado

## Estrutura

### Serviços (4 containers)

1. **api** (FastAPI)
   - Porta: 8000
   - Responsabilidades: API REST, SRS SM-2, validação
   - Dependências: PostgreSQL

2. **frontend** (React + Vite)
   - Porta: 3000
   - Responsabilidades: Interface do usuário, navegação
   - Dependências: API service

3. **tts** (Coqui/Piper TTS)
   - Porta: 8001
   - Responsabilidades: Geração de áudio, cache em disco
   - Dependências: Volume compartilhado audio/

4. **db** (PostgreSQL)
   - Porta: 5432
   - Responsabilidades: Persistência de dados
   - Volumes: postgres_data

### Cache de Áudio

Estrutura em disco:
```
audio/
├── en/word/abc123.wav      # palavra em inglês
├── en/sentence/def456.wav  # frase em inglês  
├── pt/word/ghi789.wav      # palavra em português
└── es/sentence/jkl012.wav  # frase em espanhol
```

## MVP Focus

### Escopo Inicial
- Loop principal de aprendizado
- 100+ palavras iniciais
- 3+ decks por dificuldade
- Inglês como idioma principal
- Interface web responsiva

### Limites Claros
- Sem autenticação complexa
- Sem painel administrativo
- Sem recursos cloud
- Sem sincronização remota

## Implementação

### Setup
```bash
git clone <repo>
cd filltheword
docker-compose up -d
docker-compose exec api alembic upgrade head
docker-compose exec api python scripts/seed_data.py
```

### Acesso
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- TTS API: http://localhost:8001/docs

## Expansão Futura

### Fase 2 (pós-MVP)
- Mais idiomas (português, espanhol)
- Expansão de vocabulário (500+ palavras)
- Recursos avançados de estatísticas

### Fase 3 (longo prazo)  
- Aplicativo mobile
- Sincronização entre dispositivos
- Modo colaborativo

## Workflow OpenSpec/SDD

Este projeto segue o padrão OpenSpec para especificações e change management.

### Instalação da CLI
```bash
npm i -g @fission-ai/openspec
```

### Estrutura Padrão OpenSpec
```
openspec/
├── PROJECT.md    # Contexto do projeto, stack, princípios
├── SPEC.md       # Requisitos funcionais (RF-01..RF-06)
├── DOMAINS.md    # Modelo de domínio, entidades, relacionamentos
├── API.md        # Endpoints, requests/responses, exemplos
├── ARCH.md       # Arquitetura, deploy, infraestrutura
├── TASKS.md      # Timeline de implementação, sprints
├── CHANGE_SUMMARY.md # Resumo das mudanças realizadas
├── changes/      # Propostas de mudança (Proposal → Apply → Archive)
└── archived/     # Versões antigas das especificações
```

### Ciclo de Vida das Especificações

#### 1. Proposal
- Criar documento de mudança em `changes/`
- Descrever o que e porque mudar
- Referenciar seções afetadas

#### 2. Apply
- Aplicar mudanças nos arquivos principais
- Manter consistência entre todos os arquivos
- Atualizar CHANGE_SUMMARY.md

#### 3. Archive
- Mover versões antigas para `specs/archived/`
- Manter histórico preservado
- Limpar arquivos principais

### Comandos Úteis
```bash
# Inicializar estrutura OpenSpec
openspec init

# Validar estrutura
openspec validate

# Gerar summary
openspec summary

# Arquivar versão atual
openspec archive --tag "v1.0"
```

### Change Documents
Cada mudança significativa deve ter um documento em `changes/`:
- **ID**: Formato `YYYY-MM-nome-da-mudança.md`
- **Seções**: Context, Changes, Impact, Checklist
- **Aprovação**: Review técnico antes de aplicar

### Versionamento
- **Patch**: Correções pequenas (docs, typos)
- **Minor**: Novas features, mudanças estruturais
- **Major**: Mudanças arquiteturais, quebra de compatibilidade

### Boas Práticas
1. **Spec primeiro, código depois**: Sempre especifique antes de implementar
2. **Mudanças incrementais**: Evite mudanças gigantes de uma vez
3. **Histórico preservado**: Nunca delete, apenas archive
4. **Consistência**: Mantenha todos os arquivos alinhados
5. **Review**: Sempre obtenha aprovação técnica para mudanças maiores
