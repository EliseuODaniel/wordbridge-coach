# Change: FillTheWord Base Specification Alignment

**Date**: 2025-02-11
**Type**: Major Restructure
**Scope**: All specification files
**Target**: Align documentation with texto-base original (seções 0-10)

## Problem Statement

Current OpenSpec files are misaligned with the texto-base original:
- Change document removes RF-04/05/06 but texto-base includes them
- Tasks create extra endpoints not in texto-base (/api/decks, /api/languages, /api/stats/overview)
- Missing active files PROJECT/SPEC/DOMAINS/API/ARCH in openspec/
- User/UserCardState/ReviewEvent entities removed but texto-base includes them

## Proposed Changes

### 1. PROJECT.md - Local Project Context

**Create** new file aligned with texto-base seção 0:

**Context**:
- App local/offline funcionando em containers
- Stack: FastAPI + React + Coqui/Piper + PostgreSQL + docker-compose
- 4 serviços: api (FastAPI), frontend (React), tts (Coqui/Piper), db (PostgreSQL)
- Princípios: simplicidade, performance local, cache áudio em disco

**Reference**: Texto-base Seção 0

### 2. SPEC.md - Complete Requirements (RF-01 a RF-06)

**Create** new file with ALL requirements from texto-base seções 1-6:

**Keep All RFs**:
- **RF-01**: Cartão com lacuna, tradução, dica gramatical, nível de memória
- **RF-02**: Validação com tolerância (case/acentos/sinônimos), dicas progressivas
- **RF-03**: Áudio palavra e frase com cache em disco audio/<lang>/<type>/<slug>.wav
- **RF-04**: Sessão de estudo com contador e limite novos/dia
- **RF-05**: Estatísticas básicas de progresso
- **RF-06**: Configuração de revisão (limites, algoritmo)

**Add/Enhance**:
- Complete tolerance system (case, accents, synonyms, articles)
- Progressive hints system
- Memory levels (new, learning, review, mature)
- Session management with daily limits
- Basic progress statistics
- Review configuration parameters

**Reference**: Texto-base Seções 1-6

### 3. DOMAINS.md - Complete Entity Model

**Create** new file with ALL entities from texto-base seção 7:

**Keep All Entities**:
- **Language**: idiomas suportados
- **Word**: pronúncia, audio_path, frequency_rank
- **Sentence**: tradução, tipo (exemplo/uso)
- **Card**: gap_start/gap_end, grammar_hint, deck_id
- **Deck**: categorias, difficulty_level
- **User**: usuário do sistema
- **UserCardState**: repetitions, easiness_factor, interval_days, next_review_at, status
- **ReviewEvent**: quality, response_time, timestamp

**Add Complete SM-2 Algorithm**:
- quality: 0-5 scale
- easiness_factor: minimum 1.3
- interval calculations: 1d → 6d → exponential growth
- Reset logic on failures

**Reference**: Texto-base Seção 7

### 4. API.md - MVP Endpoints Only

**Create** new file with ONLY endpoints from texto-base seções 6, 8, 10:

**Core Endpoints**:
- **GET /api/cards/next**: Seleciona próximo cartão com SRS
- **POST /api/cards/{id}/answer**: Valida resposta e atualiza progresso

**TTS Endpoints** (se necessário para cache local):
- **GET /api/tts/sentence/{id}**: Geração áudio frase com cache
- **GET /api/tts/word/{id}**: Geração áudio palavra com cache
- **GET /api/audio/{lang}/{type}/{slug}.wav**: Arquivo áudio estático
- **POST /tts**: Geração áudio flexível com parâmetros

**Remove**:
- /api/decks (não existe no texto-base)
- /api/languages (não existe no texto-base)
- /api/stats/overview (não existe no texto-base)

**Reference**: Texto-base Seções 6, 8, 10

### 5. ARCH.md - 4-Service Architecture

**Create** new file with 4-service architecture from texto-base seções 8-10:

**Services**:
- **API Service**: FastAPI + PostgreSQL, port 8000
- **Frontend Service**: React + Vite, port 3000
- **TTS Service**: Coqui/Piper TTS, port 8001
- **DB Service**: PostgreSQL, port 5432

**Key Features**:
- Audio cache: disk-based audio/<lang>/<type>/<slug>.wav
- Docker Compose: complete local setup
- Port mapping: 3000 (frontend), 8000 (api), 8001 (tts), 5432 (db)
- Volumes: postgres_data, audio_cache

**Reference**: Texto-base Seções 8-10

### 6. Corpora Pipeline

**Add** section about offline corpora pipeline:
- **Sources**: Tatoeba, ParaCrawl, OpenSubtitles
- **Processing**: sentence alignment, quality filtering
- **Integration**: seed data for MVP

### 7. tasks/ - Corrected Timeline

**Update** existing task file:
- **Remove** extra endpoints (/api/decks, /api/languages, /api/stats/overview)
- **Add** RF-04/05/06 implementation tasks
- **Add** User/UserCardState/ReviewEvent tasks
- **Keep** 2-week timeline but aligned with texto-base scope
- **Include** corpora pipeline setup

## Implementation Plan

1. **Rewrite change document** (este arquivo) - alinhar ao texto-base
2. **Create PROJECT.md** - contexto local, 4 serviços, stack completa
3. **Create SPEC.md** - RF-01 a RF-06 completos
4. **Create DOMAINS.md** - entidades completas com SM-2
5. **Create API.md** - apenas endpoints do texto-base
6. **Create ARCH.md** - arquitetura 4 serviços
7. **Update tasks/** - remover endpoints extras, adicionar RF-04/05/06
8. **Apply change** - mover arquivos para openspec/
9. **Archive** old files to openspec/specs/archived/

## Success Criteria

- All files aligned with texto-base sections 0-10
- RF-04/05/06 included as specified
- User/UserCardState/ReviewEvent entities included
- No extra endpoints beyond texto-base
- 4-service architecture clearly defined
- Corpora pipeline documented
- Local/offline focus maintained

## Migration Strategy

1. Archive current files to openspec/specs/archived/
2. Apply new files to openspec/ root
3. Update cross-references between files
4. Validate consistency across all specifications

## Validation Checklist

- [x] RF-04 (Study Sessions) included
- [x] RF-05 (Statistics) included  
- [x] RF-06 (Configuration) included
- [x] User/UserCardState/ReviewEvent entities present
- [x] SM-2 algorithm complete
- [x] Only texto-base endpoints present
- [x] Corpora pipeline documented
- [x] 4-service architecture defined
- [x] Docker compose specified
- [x] Audio cache structure correct

## API Payloads Validation Checklist (CORRIGIDOS)

### GET /api/cards/next ✅ RESOLVIDO
- [x] ✅ **CAMPO "sentence" ADICIONADO**: Frase completa em L2 agora incluída
- [x] ✅ **card_id**: UUID format mantido
- [x] ✅ **gap**: {start, end} mantido
- [x] ✅ **sentence_translation**: Mantido
- [x] ✅ **grammar_hint**: Mantido
- [x] ✅ **memory_stage**: Mantido
- [x] ✅ **audio_word_url**: Mantido
- [x] ✅ **audio_sentence_url**: Mantido

### POST /api/cards/{id}/answer ✅ RESOLVIDO
- [x] ✅ **REQUEST BODY CORRIGIDO**: `{answer, response_time_ms}` (campo "answer" adicionado, "response_time" → "response_time_ms")
- [x] ✅ **RESPONSE FORMAT CORRIGIDO**: `{correct, correct_answer, sentence_full, quality, next_review_at}` (exato formato texto-base)
- [x] ✅ **SM-2 Quality Scale**: 0-5 mantida
- [x] ✅ **Validation Rules**: Case insensitive, accent removal, article tolerance, etc.

### POST /tts ✅ RESOLVIDO
- [x] ✅ **ENDPOINT ADICIONADO**: POST /tts conforme texto-base
- [x] ✅ **PARÂMETROS**: `{text, lang, voice_type, kind: "word"|"sentence"}`
- [x] ✅ **VOICE MODELS**: EN/ES/FR/PT com vozes específicas documentadas

## Issues Resolvidos

### ISSUE 1: Campo "sentence" Faltante ✅ RESOLVIDO
**Problema**: GET /api/cards/next não incluía campo "sentence" (frase completa em L2)
**Solução**: Adicionado campo "sentence" ao payload de resposta
**Impacto**: Front-end agora tem acesso ao texto completo para renderização

### ISSUE 2: Request Body Incorreto ✅ RESOLVIDO
**Problema**: POST /api/cards/{id}/answer usava apenas "response_time"
**Solução**: Alterado para "{answer, response_time_ms}" conforme texto-base
**Impacto**: Backend receberá campo correto para medição de performance

### ISSUE 3: Response Format Incorreto ✅ RESOLVIDO
**Problema**: POST resposta não seguia formato texto-base
**Solução**: Formatado como "{correct, correct_answer, sentence_full, quality, next_review_at}"
**Impacto**: Front-end receberá dados exatos esperados pelo texto-base

### ISSUE 4: TTS POST Endpoint Faltando ✅ RESOLVIDO
**Problema**: Faltava documentação do POST /tts
**Solução**: Adicionado endpoint POST /tts com parâmetros completos
**Impacto**: API flexível para geração de áudio conforme especificado

## Status Final

🎉 **ESPECIFICAÇÃO 100% ALINHADA AO TEXTO-BASE**  
🎉 **PAYLOADS DA API CORRIGIDOS E VALIDADOS**  
🎉 **TODOS OS ITENS DO CHECKLIST CONCLUÍDOS**  

A documentação está pronta para implementação com total compatibilidade com o texto-base original.
