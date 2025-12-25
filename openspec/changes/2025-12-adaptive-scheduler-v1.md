# Change: Adaptive Scheduler v1 (Lingvist)

**Date**: 2025-12-25
**Status**: 🚧 Applied (Frontend Pending)
**Version**: v1.0
**Spec Reference**: RF-01 (Card Learning System), Lingvist Mode

## Overview

Implementar um scheduler adaptativo para o modo Lingvist que:
1. Prioriza palavras erradas para reaparecerem mais cedo (relearn queue)
2. Ajusta dinamicamente a quantidade de novas palavras baseado em accuracy
3. Usa tentativas e hints do frontend para calcular qualidade SM-2
4. Mantém compatibilidade total com Spec4 (modo clássico sem mudanças)

## Spec4 Invariável

**Princípio fundamental**: Spec4 mode deve permanecer 100% inalterado.

**Implementação**:
- Campo `User.mode` com default `"spec4"` garante que usuários existentes não são afetados
- Toda lógica adaptativa é condicionada a `user.mode == "lingvist"`
- `CardSelectionService.get_next_card_for_user()` verifica modo e chama:
  - `_get_next_card_spec4()` → Comportamento original (25% new fixo, sem relearn)
  - `_get_next_card_lingvist()` → Comportamento adaptativo (relearn queue + new_share variável)
- `submit_answer()` só aplica relearn queue se `user.mode == "lingvist"`

**Validação**:
- Testes específicos garantem que Spec4 não usa relearn ou adaptive new_share
- Usuários criados sem especificar mode → mode="spec4"
- API backward compatible (attempts/hints têm defaults)

## Business Problem

No scheduler atual (SM-2 puro), palavras erradas podem demorar dias para reaparecer, o que prejudica a aprendizagem. Usuários que erram muito continuam recebendo muitas palavras novas, sobrecarregando o sistema.

## Changes

### Phase 1: Backend (No Major Migration)

#### 1.1 Relearn Queue (Lingvist Mode)

**Objective**: Palavras erradas reaparecem em minutos, não dias

**Implementation**:
- Novo campo em `UserCard`: `relearn_due: datetime | null`
- Novo campo em `UserCard`: `is_relearn: bool default False`
- Endpoint `/api/v1/cards/next` ajustado para priorizar cards `is_relearn=True`
- Lógica de marking:
  - Se `quality < 3` (errou ou acertou com dificuldade):
    - `is_relearn = True`
    - `relearn_due = now() + timedelta(minutes=10)` (primeira revisão)
    - Intervalos subsequentes: 10min → 30min → 2h → 6h → 24h
  - Se `quality >= 4` (acertou bem) em relearn:
    - `is_relearn = False`
    - `relearn_due = null`
    - Retornar ao scheduler SM-2 normal

#### 1.2 Adaptive New Share

**Objective**: Reduzir novas palavras quando usuário está errando muito

**Implementation**:
- Novo campo em `User`: `accuracy_last_20: float | null` (média das últimas 20 respostas)
- Calculado no endpoint `/answer` após cada resposta:
  ```python
  recent_attempts = get_last_20_attempts(user_id)
  accuracy = sum(1 for a in recent_attempts if a.was_correct) / len(recent_attempts)
  user.accuracy_last_20 = accuracy
  ```

- Lógica adaptativa em `/cards/next`:
  ```python
  reviews_due_count = count_reviews_due(user_id)

  if reviews_due_count > 50:
      new_share = 0.0  # Priorizar reviews
  elif user.accuracy_last_20 is not None:
      if user.accuracy_last_20 < 0.7:
          new_share = 0.10  # Apenas 10% de novas
      elif user.accuracy_last_20 > 0.9:
          new_share = 0.25  # Aumentar para 25%
      else:
          new_share = 0.15  # Padrão
  else:
      new_share = 0.15  # Padrão sem dados
  ```

#### 1.3 Anti-Repetition Fix

**Objective**: Não excluir palavras erradas da fila de estudo

**Current Code** (`cards/next`):
```python
recent_word_ids = [card.word_id for card in recent_cards]
query = query.filter(~UserCard.word_id.in_(recent_word_ids))
```

**Issue**: Exui TODAS as palavras recentes, mesmo as erradas

**Fix**:
```python
recent_word_ids_correct = [
    card.word_id for card in recent_cards
    if card.was_correct is True
]
query = query.filter(~UserCard.word_id.in_(recent_word_ids_correct))
```

#### 1.4 Attempts and Hints Tracking

**Objective**: Calcular qualidade SM-2 mais precisa

**Database Changes**:
- Adicionar campos em `StudySession`:
  - `attempts: int default 1`
  - `hints_used: int default 0`

**API Changes**:
- Endpoint `POST /api/v1/cards/{card_id}/answer`:
  - Aceitar novos campos: `attempts`, `hints_used`
  - Usar `SM2Algorithm.calculate_quality_from_response()`:
    ```python
    quality = calculate_quality_from_response(
        was_correct=answer_data.was_correct,
        attempts=answer_data.attempts,
        hints_used=answer_data.hints_used
    )
    ```

#### 1.5 Mode Selection (Spec4 vs Lingvist)

**Objective**: Spec4 continua sem mudanças comportamentais

**Implementation**:
- Novo campo em `User`: `mode: varchar(20) default 'spec4'`
- Valores: `'spec4'` | `'lingvist'`
- `/cards/next`:
  - Se `mode == 'spec4'`: Usa scheduler atual (sem relearn, new_share fixo)
  - Se `mode == 'lingvist'`: Usa scheduler adaptativo (relearn + adaptive new_share)

### Phase 2: Frontend

#### 2.1 Track Attempts and Hints

**Implementation**:
- Componente `LingvistCard`: Contar tentativas de submit
- Contar cliques em "Show Hint"
- Enviar no payload do `/answer`:
  ```typescript
  {
    answer: string,
    was_correct: boolean,
    response_time_ms: number,
    attempts: number,      // NOVO
    hints_used: number     // NOVO
  }
  ```

#### 2.2 Mode Selection UI

**Implementation**:
- Adicionar seletor em `/settings`: "Learning Mode"
  - Spec4 (Classic): Scheduler SM-2 padrão
  - Lingvist (Adaptive): Scheduler com revisão curta + adaptação

### Phase 3: Testing

#### 3.1 Backend Tests (pytest)

**New Test File**: `tests/integration/test_adaptive_scheduler.py`

```python
def test_wrong_answer_enters_relearn_queue():
    """Erro → palavra marcada como relearn com due em minutos"""

def test_relearn_card_appears_before_normal_reviews():
    """Relearn cards têm prioridade alta"""

def test_correct_answer_exits_relearn():
    """Acertou bem → sai do relearn e volta ao SM-2 normal"""

def test_accuracy_below_70_reduces_new_cards():
    """Accuracy < 0.7 → new_share reduz para 10%"""

def test_accuracy_above_90_increases_new_cards():
    """Accuracy > 0.9 → new_share aumenta para 25%"""

def test_high_review_backlog_zero_new_cards():
    """Reviews due > 50 → new_share = 0"""

def test_wrong_word_not_excluded_by_anti_repetition():
    """Palavra errada NÃO é excluída por recent_word_ids"""

def test_spec4_mode_unchanged():
    """Spec4 mode não usa relearn ou adaptive new_share"""
```

#### 3.2 E2E Tests (Playwright)

**New Test File**: `tests/e2e/adaptive-scheduler.spec.ts`

```typescript
test('errei 2x → aparece hint e qualidade menor → volta antes', async ({ page }) => {
  // User entra em modo Lingvist
  // Erra palavra 2x seguidas
  // Verifica que aparece novamente em menos de 5 cards
});

test('accuracy baixa → recebo menos novas palavras', async ({ page }) => {
  // User erra muito (accuracy < 0.7)
  // Verifica que próxima sessão tem mais reviews que novas
});

test('spec4 mode sem mudanças', async ({ page }) => {
  // User em modo Spec4
  // Erra palavra
  // Verifica que NÃO entra em relearn queue
});
```

## Validation

### Manual Testing Plan

1. **Testar Relearn Queue**:
   ```bash
   # Criar user em modo lingvist
   curl -X POST http://localhost:8000/api/v1/users/ \
     -H "Content-Type: application/json" \
     -d '{"username": "testlingvist", "mode": "lingvist"}'

   # Errar uma palavra (quality < 3)
   # Verificar que is_relearn=true e relearn_due em ~10min

   # Pegar próximo card - deve ser o relearn
   # Acertar bem (quality >= 4)
   # Verificar que is_relearn=false
   ```

2. **Testar Adaptive New Share**:
   ```bash
   # Errar 15 de 20 últimas (accuracy = 0.25)
   # Verificar que new_share = 0.10

   # Acertar 19 de 20 últimas (accuracy = 0.95)
   # Verificar que new_share = 0.25
   ```

3. **Testar Spec4 Compatibility**:
   ```bash
   # User em modo spec4
   # Errar palavra
   # Verificar que is_relearn=false (sem mudança)
   ```

### Automated Testing

```bash
# Backend tests
pytest tests/integration/test_adaptive_scheduler.py -v

# E2E tests
cd tests/e2e && npm test adaptive-scheduler.spec.ts
```

## Success Criteria

- [ ] Palavra errada (quality < 3) é marcada `is_relearn=True` com `relearn_due` em minutos
- [ ] Cards relearn aparecem com prioridade alta no `/cards/next`
- [ ] Acertar bem (quality >= 4) remove card do relearn
- [ ] `accuracy_last_20 < 0.7` → `new_share = 0.10`
- [ ] `accuracy_last_20 > 0.9` → `new_share = 0.25`
- [ ] Reviews due > 50 → `new_share = 0`
- [ ] Palavras erradas NÃO são excluídas por `recent_word_ids`
- [ ] Endpoint `/answer` aceita e usa `attempts` e `hints_used`
- [ ] Spec4 mode mantém comportamento original (sem relearn, new_share fixo)
- [ ] Testes pytest passam (cobertura > 80% do novo código)
- [ ] Testes Playwright passam
- [ ] Frontend envia `attempts` e `hints_used` no `/answer`

## Migration

### Database Migration

```sql
-- Adicionar campos em User
ALTER TABLE "user" ADD COLUMN mode VARCHAR(20) DEFAULT 'spec4';
ALTER TABLE "user" ADD COLUMN accuracy_last_20 FLOAT;

-- Adicionar campos em UserCard
ALTER TABLE user_card ADD COLUMN relearn_due TIMESTAMP;
ALTER TABLE user_card ADD COLUMN is_relearn BOOLEAN DEFAULT FALSE;

-- Adicionar campos em StudySession
ALTER TABLE study_session ADD COLUMN attempts INTEGER DEFAULT 1;
ALTER TABLE study_session ADD COLUMN hints_used INTEGER DEFAULT 0;

-- Criar índices
CREATE INDEX idx_user_card_relearn ON user_card(user_id, is_relearn, relearn_due) WHERE is_relearn = TRUE;
CREATE INDEX idx_user_accuracy ON "user"(id, accuracy_last_20);
```

### Rollback Plan

Se algo der errado:
1. Reverter migration: `alembic downgrade -1`
2. Remover flags de modo Lingvist da UI
3. Sistema volta ao comportamento Spec4 original

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Relearn queue muito agressiva | Usuário ver mesma palavra muitas vezes | Ajustar intervalos (10min→30min→2h) baseado em feedback |
| Accuracy calculation bug | New share errado | Adicionar validações (clamp 0-1, null check) |
| Spec4 regression | Quebra workflow existente | Testes explícitos de Spec4, mode flag com default safe |
| Performance hit (queries extras) | Lentidão no /cards/next | Adicionar índices, otimizar queries, cachear accuracy |

## Open Questions

1. **Intervalos de relearn**: 10min → 30min → 2h está ok? Ou deve ser configurável?
2. **Backlog threshold**: 50 reviews é bom threshold? Depende de daily_limit?
3. **Frontend mode selection**: Onde colocar seletor? Settings ou onboarding?
4. **Migration strategy**: Criar novos users em qual mode? Perguntar no onboarding?

## Timeline Estimate

- Phase 1 (Backend): 4-6 horas
- Phase 2 (Frontend): 2-3 horas
- Phase 3 (Testing): 2-3 horas
- **Total**: 8-12 horas

## References

- SM-2 Algorithm: `api/app/services/sm2.py`
- Current Scheduler: `api/app/api/v1/cards.py`
- Spec4 Logic: `api/app/services/card_service.py:get_next_card()`
- Lingvist Integration: branch atual (fix/lingvist-translations-hints)

---

## Implementation Progress (Updated: 2025-12-25)

### ✅ Completed (Backend)

**Database & Models (100%)**
- ✅ Migration `20251225014903_add_adaptive_scheduler_fields.py` created and applied
- ✅ User model: `mode`, `accuracy_last_20`
- ✅ UserCardState model: `is_relearn`, `relearn_due`
- ✅ ReviewEvent model: `attempts`

**SM2 Service (100%)**
- ✅ `calculate_relearn_interval()` - Progressive intervals (10min→30min→2h→6h→24h)
- ✅ `should_enter_relearn()` - Check if quality < 3

**CardSelectionService (100%)**
- ✅ `_get_user_mode()` - Detect user mode
- ✅ `_get_next_card_spec4()` - Original behavior preserved
- ✅ `_get_next_card_lingvist()` - Adaptive scheduler
- ✅ `_get_due_relearn_card()` - Relearn queue priority
- ✅ `_calculate_adaptive_new_share()` - Accuracy-based (10%/15%/25%)
- ✅ `_count_reviews_due()` - Review backlog counter
- ✅ `_get_recent_correct_word_ids()` - Anti-repetition fix

**API & Schemas (100%)**
- ✅ `AnswerRequest` schema: added `attempts`, `hints_used`
- ✅ `submit_answer()` endpoint:
  - Uses attempts and hints for quality calculation
  - Updates `accuracy_last_20` after each answer
  - Manages relearn queue (enter/exit) based on quality and mode

### 🔄 In Progress / Pending

**Frontend (0%)**
- ⏳ Update `LingvistSession.tsx` to track attempts and hints
- ⏳ Update `HintPanel.tsx` to emit hints_used callback
- ⏳ Update `api.ts` to send attempts/hints in AnswerRequest
- ⏳ Add mode selection UI (optional for v1)

**Testing (0%)**
- ⏳ Backend integration tests: `test_adaptive_scheduler.py`
- ⏳ E2E tests: `adaptive-scheduler.spec.ts`
- ⏳ Manual testing checklist

### 📝 Notes

- **Spec4 Compatibility**: All existing users default to 'spec4' mode, preserving original behavior
- **Backward Compatibility**: API accepts attempts/hints with defaults (1, 0), so existing clients work
- **Performance**: Indexes created on relearn fields for query optimization
- **Next Steps**: Frontend implementation required for full testing of adaptive features
