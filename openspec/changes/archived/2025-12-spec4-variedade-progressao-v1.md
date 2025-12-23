# Change: Spec4 Variedade + Progressão + Integração Completa

**Date**: 2025-12-22
**Status**: ✅ Applied & Validated
**Version**: v1.0
**Type**: Major Feature Enhancement + Bug Fixes
**Scope**: Backend (Spec4 algorithm), Frontend (Study Session), Database (Seed), Documentation (Docker)

---

## Overview

Implementa completamente o algoritmo **Spec4** definido em `spec4.md`, incluindo variedade de frases por palavra, progressão de vocabulário com janela dinâmica, e corrigindo bugs críticos na implementação atual do endpoint `/api/v1/cards/next-spec4`.

## Problem Statement

### Problemas Atuais

1. **Bug Crítico: card_id incorreto** - O endpoint `/api/v1/cards/next-spec4` retorna `word_id` como se fosse `card_id`, causando fallback no POST `/answer` e impedindo persistência correta de `ReviewEvent` e `UserCardState`.

2. **Variedade de frases não funciona** - O método `get_sentence_for_word` tem bugs (acesso incorreto a tuplas) e não existe seed de múltiplas frases por palavra (atualmente 1:1).

3. **ReviewEvent.sentence_id não preenchido** - Campo existe no modelo mas não é gravado no POST `/answer`, quebrando a variedade de frases.

4. **UI de goal incompleta** - Frontend tem slider na criação mas não permite editar `word_goal_rank` posteriormente.

5. **Seed de dados quebrado** - Script `seed_varied_sentences.py` falha (falta `Sentence.type`) e não cria `Card` para cada `Sentence`.

6. **Docs Docker desatualizadas** - WSL2 requer `docker compose` (v2) mas docs mencionam `docker-compose` (legado); porta do frontend inconsistente (3000 vs 3007).

## Proposed Changes

### 1. Correção Crítica do Endpoint `/api/v1/cards/next-spec4`

**Current State:**
```python
# Retorna word_id como card_id (BUG)
return {
    "card_id": str(word.id),  # INCORRETO
    "word_id": str(word.id),
    ...
}
```

**Target State:**
```python
# Retorna card_id REAL de Card existente
return {
    "card_id": str(card.id),  # Card.id UUID REAL
    "word_id": str(word.id),  # Word.id separado
    "sentence_id": str(sentence.id),
    ...
}
```

**Contrato API:**
- `card_id`: Sempre `Card.id` (UUID) de um Card existente no banco
- `word_id`: Sempre `Word.id` (UUID) separado
- `sentence_id`: Incluído para rastreamento de variedade

### 2. Algoritmo de Variedade de Frases

**Implementação de `get_sentence_for_word(user_id, word_id)`:**

#### Contrato:
1. **Busca candidatos**: Todas as `Sentence` vinculadas ao `word_id` via `WordSentence` (ou `Sentence.word_id`)
2. **Consulta histórico**: Últimas K=10 `sentence_id` usados em `ReviewEvent` para esse user+word
3. **Seleção**:
   - **Prioridade 1**: Frases nunca vistas (`count == 0` ou não em recent_ids)
   - **Prioridade 2**: Menos recentemente usada (menor `last_used_at`)
4. **Fallback**: Criar frase básica se nenhuma existir (sem internet, template local)

#### Pseudocódigo:
```python
def get_sentence_for_word(user_id, word_id):
    # 1. Obter sentence_ids candidatos
    candidate_ids = get_word_sentence_ids(word_id)

    # 2. Buscar últimos K=10 usados
    K = 10
    recent = db.query(ReviewEvent.sentence_id)\
        .filter(ReviewEvent.user_id == user_id)\
        .filter(ReviewEvent.sentence_id.in_(candidate_ids))\
        .order_by(desc(ReviewEvent.created_at))\
        .limit(K).all()
    recent_ids = [r.sentence_id for r in recent]

    # 3. Separar unseen vs seen
    unseen = [sid for sid in candidate_ids if sid not in recent_ids]

    if unseen:
        # Escolher aleatório entre unseen
        return random.choice(unseen)
    else:
        # Menos recente
        last_used = db.query(
            ReviewEvent.sentence_id,
            func.max(ReviewEvent.created_at).label('last_used')
        ).filter(
            ReviewEvent.sentence_id.in_(candidate_ids)
        ).group_by(ReviewEvent.sentence_id)\
         .order_by('last_used ASC')\
         .first()

        return last_used.sentence_id if last_used else None
```

### 3. Persistência Obrigatória no POST `/answer`

**Current State:**
```python
# sentence_id não é preenchido
review_event = ReviewEvent(
    user_id=...,
    card_id=...,
    sentence_id=None,  # BUG
    ...
)
```

**Target State:**
```python
# Sempre preencher sentence_id
review_event = ReviewEvent(
    user_id=user_id,
    card_id=card.id,
    sentence_id=card.sentence_id,  # OBRIGATÓRIO
    quality=quality,
    response_time_ms=answer_data.response_time_ms,
    was_correct=is_correct,
    ...
)
```

### 4. Seed de Múltiplas Frases por Palavra

**Mínimo Viável:**
- 3-5 frases por palavra para top 200-500 ranks (offline)
- Cada Sentence deve ter Card correspondente
- Templates locais (sem internet):
  - Frases declarativas: "{word} is/are {context}."
  - Perguntas: "Is/Are {word} {context}?"
  - Negativas: "{word} is/are not {context}."

**Script: `api/seed_varied_sentences.py`**
```python
def create_sentences_for_word(word, count=5):
    templates = [
        ("The {word} is {context}.", "{context} é {translation}."),
        ("Is {word} {context}?", "{context} é {translation}?"),
        ...
    ]

    for i in range(count):
        sentence = Sentence(
            text=template.format(word=word.text, context=random_context()),
            translation=trans_template.format(...),
            word_id=word.id,
            language_id=word.language_id,
            type="example",
            source_type=SourceType.GENERATED,
            difficulty=word.difficulty,
            gap_start=calculate_gap_start(...),
            gap_end=calculate_gap_end(...)
        )
        db.add(sentence)
        db.flush()

        # OBRIGATÓRIO: Criar Card
        card = Card(
            sentence_id=sentence.id,
            deck_id=default_deck.id,
            grammar_hint=generate_grammar_hint(word),
            difficulty=word.difficulty,
            gap_start=sentence.gap_start,
            gap_end=sentence.gap_end,
            is_active=True
        )
        db.add(card)
```

### 5. UI de Objetivo de Vocabulário (Goal)

**Backend:**
- Adicionar `word_goal_rank` ao `UserUpdateRequest`
- Validar contra `{100, 500, 1500, 3000, 5000, 10000}`
- Atualizar `User.word_goal_rank`
- Ajustar `UserFrequencyProgress.current_window_end_rank = min(current, new_goal)`

**Frontend:**
- Adicionar seletor no modal de editar perfil
- Já existe slider na criação (manter)
- Suportar edição via PATCH `/api/v1/users/{user_id}`

### 6. Ajustes de memory_stage

**Contrato:**
- Valores SM-2: `NEW`, `LEARNING`, `REVIEW`, `MATURE`, `RELEARN`
- Frontend deve suportar uppercase (além de lowercase legado)
- Derivado de `UserCardState.status` para cards com estado
- Para cards novos sem estado: usar `NEW`

### 7. Documentação Docker/WSL2

**Atualizar:**
- `README.md` e `openspec/PROJECT.md`
- Instruções com `docker compose` (v2) como primary
- Alternativa `docker-compose` (legado) em nota
- WSL2: habilitar Docker Desktop integration
- Corrigir porta frontend (3007 no compose, docs dizem 3000)

## Non-Scope (O que NÃO vai ser mudado)

- ❌ Endpoint legado `/api/v1/cards/next` (mantém compatibilidade)
- ❌ Algoritmo SM-2 (já implementado corretamente)
- ❌ Bandas de frequência (Spec2) - continuam existindo para insights
- ❌ Multi-idioma (EN/FR já suportado)

## Decisões de Contrato

### card_id vs word_id
- **Decisão**: `card_id` é SEMPRE `Card.id` real (UUID existente no banco)
- **Racional**: Permite persistência correta de `ReviewEvent` e `UserCardState`
- **Breaking**: Nenhum (frontend já trata card_id como string opaca)

### sentence_id em ReviewEvent
- **Decisão**: `sentence_id` é OBRIGATÓRIO e sempre preenchido
- **Racional**: Necessário para variedade de frases (evitar repetição)
- **Validação**: POST `/answer` retorna 400 se `sentence_id` for None

### memory_stage values
- **Decisão**: Uppercase SM-2 values (`NEW`, `LEARNING`, etc.)
- **Racional**: Consistência com `MemoryStage` enum em `user_card_state.py`
- **Frontend**: Suporta ambos uppercase e lowercase (backwards compat)

### K=10 para frases recentes
- **Decisão**: Constante `K=10` para "últimas frases usadas"
- **Racional**: Balance entre variedade e performance (query simples)
- **Future**: Pode se tornar configurável por usuário

### word_goal_rank values
- **Decisão**: Apenas `{100, 500, 1500, 3000, 5000, 10000}`
- **Racional**: UI simplificada com opções pré-definidas
- **Validação**: Backend rejeita valores fora do conjunto

## Plano de Migração (Database)

### Alembic Migration
**Arquivo**: `api/alembic/versions/YYYYMMDD_spec4_sentence_review_fix.py`

**Changes:**
1. Garantir `ReviewEvent.sentence_id` tem índice para performance
2. Adicionar constraint `NOT NULL` após validação (ou manter nullable para backwards compat)

```python
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add index for sentence_id in ReviewEvent (performance)
    op.create_index(
        'ix_reviewevent_sentence_id',
        'reviewevent',
        ['sentence_id']
    )

    # Add index for user_id + sentence_id composite queries
    op.create_index(
        'ix_reviewevent_user_sentence',
        'reviewevent',
        ['user_id', 'sentence_id']
    )

def downgrade():
    op.drop_index('ix_reviewevent_user_sentence', table_name='reviewevent')
    op.drop_index('ix_reviewevent_sentence_id', table_name='reviewevent')
```

**Nota**: Não é necessário mudar schema (campos já existem).

## Requisitos Funcionais

### RF-09: Variedade de Frases por Palavra
- **User Story**: Como estudante, quero ver frases diferentes ao estudar a mesma palavra
- **Critérios**:
  - [ ] Sistema prefere frases nunca vistas pelo usuário
  - [ ] Sistema evita repetir últimas K=10 frases usadas
  - [ ] Se todas foram vistas, escolhe a menos recente
  - [ ] Fallback cria frase básica se nenhuma existir

### RF-10: Progressão de Vocabulário com Janela Dinâmica
- **User Story**: Como estudante, quero progredir em ordem de frequência
- **Critérios**:
  - [ ] Mix 25% novas / 75% revisões
  - [ ] Janela expande automaticamente (100 → 200 → 300...)
  - [ ] Objetivo configurável (100/500/1500/3000/5000/10000)
  - [ ] Gating por prefixo contíguo (não pula buracos)

### RF-11: Edição de Objetivo de Vocabulário
- **User Story**: Como estudante, quero ajustar minha meta de vocabulário
- **Critérios**:
  - [ ] Frontend tem seletor de goal no modal de edição
  - [ ] Backend aceita `word_goal_rank` no PATCH `/users/{id}`
  - [ ] Progresso é ajustado (clamp) se goal reduzido
  - [ ] Validação contra opções permitidas

### RF-12: Correção de Bugs Críticos
- **User Story**: Como sistema, preciso persistir dados corretamente
- **Critérios**:
  - [ ] `next-spec4` retorna `card_id` real de `Card.id`
  - [ ] `ReviewEvent.sentence_id` sempre preenchido
  - [ ] `exclude_card_id` exclui por card_id (não word_id)
  - [ ] Sem erros de fallback no POST `/answer`

## Critérios de Aceite

### Backend
- [ ] `GET /api/v1/cards/next-spec4` retorna `card_id` válido (existente em `Card`)
- [ ] `POST /api/v1/cards/{card_id}/answer` persiste `ReviewEvent.sentence_id`
- [ ] `get_sentence_for_word` prefere frases unseen
- [ ] K=10 últimas frases são evitadas quando há alternativas
- [ ] `PATCH /api/v1/users/{id}` aceita e atualiza `word_goal_rank`
- [ ] Seed cria 3-5 frases por palavra com Cards correspondentes
- [ ] Testes de integração passam (ver TESTING.md)

### Frontend
- [ ] `StudySession` usa `/api/v1/cards/next-spec4` com `exclude_card_id`
- [ ] `exclude_card_id` envia `card.id` (não `word.id`)
- [ ] `CardDisplay` suporta `memory_stage` em uppercase
- [ ] `UserSelection` tem slider de goal no modal de edição
- [ ] Não há erros de "card not found" no POST `/answer`

### Seed/Dados
- [ ] Script `seed_varied_sentences.py` roda sem erros
- [ ] Cria pelo menos 3 frases para top 200 palavras
- [ ] Cada Sentence tem Card correspondente
- [ ] Gap positions (start/end) estão corretos

### Docs
- [ ] `README.md` menciona `docker compose` (v2)
- [ ] Nota sobre `docker-compose` legado incluída
- [ ] Instruções WSL2 presentes (Docker Desktop integration)
- [ ] Porta do frontend documentada corretamente (3007:3000)

## Plano de Validação

### Backend Tests (pytest)
```bash
# Rodar todos os testes
cd api
PYTHONPATH=. pytest tests/integration/ -v

# Teste específico de Spec4
pytest tests/integration/test_spec4_card_selection.py -v

# Teste de variedade de frases
pytest tests/integration/test_sentence_variety.py -v

# Com coverage
pytest --cov=app --cov-report=html
```

**Testes Críticos:**
1. `test_next_spec4_returns_real_card_id`
   - Assert: `card_id` retornado existe em `Card` table
2. `test_answer_creates_review_event_with_sentence_id`
   - Assert: `ReviewEvent.sentence_id is not None`
3. `test_sentence_variety_prefers_unseen`
   - Assert: 10 calls → 10 different sentences (when possible)
4. `test_sentence_variety_avoids_recent_k`
   - Assert: Last 10 sentences are not repeated
5. `test_user_update_accepts_word_goal_rank`
   - Assert: PATCH com `word_goal_rank` atualiza `User` e `UserFrequencyProgress`

### E2E Tests (Playwright)
```bash
cd tests/e2e
npm test

# Fluxo manual:
# 1. Criar usuário com goal=500
# 2. Estudar 5 cards (verificar variedade de frases)
# 3. Editar perfil para goal=1000
# 4. Continuar estudando (verificar sem erros)
```

**Validação Manual:**
1. Acessar http://localhost:3007
2. Criar usuário (goal=500)
3. Estudar 10 cards, anotar sentence_ids
4. Verificar se há variedade (pouca repetição)
5. Editar perfil para goal=1500
6. Verificar se sistema continua funcionando

### Performance Checks
```bash
# Query performance (sentence variety)
EXPLAIN ANALYZE
SELECT sentence_id, MAX(created_at)
FROM reviewevent
WHERE user_id = '...' AND sentence_id IN (...)
GROUP BY sentence_id
ORDER BY MAX(created_at) ASC;
```

**Target**: <50ms para query de últimas K=10 frases

## Riscos e Mitigações

### Risco 1: Regressão no Endpoint Legado
- **Impacto**: Usuários de `/next` (se houver) podem quebrar
- **Mitigação**: Não tocar em `/next`; testes backwards compat
- **Plano B**: Reverter migration e fix hotfix

### Risco 2: Performance da Query de Variedade
- **Impacto**: Query de ReviewEvent pode ficar lenta com muitos dados
- **Mitigação**: Índices compostos em `(user_id, sentence_id)`
- **Plano B**: Cache de últimas K=10 em Redis (futuro)

### Risco 3: Seed Demorado
- **Impacto**: Script de seed pode levar minutos para top 10k
- **Mitigação**: Limitar a top 500 palavras no MVP
- **Plano B**: Seed assíncrono em background job

### Risco 4: Inconsistência card_id/word_id
- **Impacto**: Frontend pode enviar card_id errado no POST
- **Mitigação**: Validação estrita no backend (404 se não existe)
- **Plano B**: Logs detalhados para debug

## Rollback Plan

Se algo der errado após deploy:

1. **Backend**:
   - Reverter código para commit anterior
   - Desfazer migration Alembic (alembic downgrade -1)
   - Verificar se dados estão consistentes

2. **Frontend**:
   - Revert para versão anterior (npm run build)
   - Limpar cache do browser

3. **Dados**:
   - `ReviewEvent.sentence_id` pode permanecer nullable (sem dano)
   - Cards criados na seed podem ser mantidos (sem problema)

4. **Comunicação**:
   - Avisar time sobre rollback
   - Documentar o que falhou
   - Corrigir e tentar novamente

## Success Metrics

### Técnicos
- [ ] 95%+ dos testes backend passando
- [ ] 100% dos testes E2E passando
- [ ] Zero erros 500 em produção
- [ ] <200ms latência média do `/next-spec4`

### Funcionais
- [ ] 90%+ dos cards estudados têm sentence_id preenchido
- [ ] 80%+ das palavras estudadas repetem com frase diferente (após K=10)
- [ ] 0% de erros "card not found" no POST `/answer`

### UX
- [ ] Usuários conseguem editar goal sem erros
- [ ] Variedade de frases perceptível (feedback qualitativo)
- [ ] Documentação Docker funciona em WSL2

## Timeline Estimada

- **FASE 1 (Proposal)**: 2-3h (este documento)
- **FASE 2 (Apply)**: 8-12h
  - Backend fixes: 3-4h
  - Seed script: 2-3h
  - Frontend adjustments: 1-2h
  - Tests: 2-3h
- **FASE 3 (Validate)**: 2-3h
  - Run tests: 1h
  - Manual validation: 1h
  - Documentation: 1h
- **FASE 4 (Archive)**: 1h
  - Update CHANGE_SUMMARY: 30min
  - Mark change as Applied: 30min

**Total**: 13-19 horas (1.5-2.5 dias de trabalho)

## References

- `spec4.md`: Fonte de verdade para algoritmos Spec4
- `openspec/AGENTS.md`: Workflow de development
- `openspec/SPEC.md`: Requisitos funcionais RF-01 a RF-08
- `openspec/DOMAINS.md`: Modelo de domínio atual
- `openspec/API.md`: Contratos API atuais
- `TESTING.md`: Como rodar testes
- `README.md`: Documentação Docker atual

---

**Status**: 📋 Planned → Pending Implementation

**Next Steps**:
1. Aprovação deste change proposal
2. Atualizar OpenSpec (DOMAINS, API, SPEC, CHANGE_SUMMARY)
3. Implementar mudanças (FASE 2)
4. Validar com testes (FASE 3)
5. Arquivar e documentar (FASE 4)
