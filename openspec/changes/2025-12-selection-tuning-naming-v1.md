# Change: Selection Tuning & Mode Renaming v1

**Date**: 2025-12-25
**Status**: 📝 Proposal
**Version**: v1.0
**Spec Reference**: RF-01 (Card Learning System), RF-02 (Vocabulary Progression)

## Overview

Melhorar a mecânica de seleção (palavras + frases) para Spec4 e Lingvist para torná-la progressivamente desafiadora (nem fácil demais, nem difícil demais), corrigir bugs críticos de persistência de modo, e renomear os modos no frontend para nomes mais intuitivos.

## Business Problem

### Problemas Identificados (AUDIT)

#### 1. **CRITICAL BUG**: UI não persiste `User.mode` no backend
- **Symptoms**: Usuário seleciona "Lingvist" na UI, mas backend sempre usa Spec4
- **Root Cause**: `UserSelection.tsx` só salva modo em `localStorage`, nunca chama `PATCH /users/{id}` com `mode`
- **Impacto**: Feature Adaptive Scheduler (relearn queue) nunca é ativada para usuários via UI
- **Evidência**: `frontend/src/components/UserSelection.tsx:102` não inclui `mode` em `CreateUserRequest`

#### 2. Repetição de frases não evita últimas K da MESMA palavra
- **Symptoms**: Mesma frase aparece repetidamente para a mesma palavra dentro de uma sessão
- **Root Cause**: `get_sentence_for_word()` conta K=10 por usuário+frase, não por usuário+palavra+frase
- **Impacto**: K=10 não é efetivo, usuário vê repetição excessiva
- **Evidência**: `api/app/services/vocabulary_progression.py:99-110` não filtra por `word_id`

#### 3. Performance issue: `.all()` carrega todas palavras em memória
- **Symptoms**: Seleção de palavras novas lenta com DB grande (>10K palavras)
- **Root Cause**: `_get_random_new_card()` usa `query.all()` + `random.choice()` em Python
- **Impacto**: Latência alta, uso de memória desnecessário
- **Evidência**: `api/app/services/card_selection.py:220-243`

#### 4. Hardcode de idioma impede multi-idioma
- **Symptoms**: Sistema sempre assume "en" como target language
- **Root Cause**: `WordFrequency.language_code == "en"` hardcoded
- **Impacto**: Não funciona para francês, espanhol, etc.
- **Evidência**: `api/app/services/vocabulary_progression.py:198`

#### 5. Dificuldade não escala com performance do usuário
- **Symptoms**: Usuário com accuracy 95% recebe palavras da mesma dificuldade que usuário com 60%
- **Root Cause**: Seleção é uniforme dentro da janela, sem bias por performance
- **Impacto**: Usuários avançados ficam entediados, iniciantes se frustram

#### 6. Nomes confusos dos modos (UX)
- **Symptoms**: Usuários não entendem diferença entre "Spec4" e "Lingvist"
- **Root Cause**: Nomes técnicos sem significado para usuário final
- **Impacto**: Escolha de modo não é informada

## Goals

### (G1) Frases: evitar repetição recente REAL por palavra
**Objetivo**: Com pool suficiente (>= 12 frases para uma palavra), a mesma frase não aparece dentro das últimas 10 ocorrências **dessa palavra específica**.

**Implementação**:
- Modificar `get_sentence_for_word()` para filtrar últimas K sentenças **por usuário+palavra**
- Query: `ReviewEvent.sentence_id` JOIN `Card` JOIN `Sentence` WHERE `word_id = <word_id>`
- Se houver alternativas fora desse set, escolher entre elas
- Se não houver alternativa (pool pequeno), permitir repetir (não retornar None)

### (G2) Palavras "novas": realmente novas (não vistas) + performance
**Objetivo**: Seleção de palavras novas deve:
1. Preferir palavras sem histórico do usuário (sem UserCardState para aquela Word)
2. Usar randomização DB-side (não `.all()` em memória)
3. Respeitar threshold de pool pequeno (não bloquear quando < 10 alternativas)

**Implementação**:
- Em `_get_random_new_card()`:
  - Substituir `query.all()` por `order_by(func.random()).limit(1)` (PostgreSQL)
  - Adicionar filtro: `NOT EXISTS (SELECT 1 FROM usercardstate WHERE usercardstate.word_id = word.id)`
  - Manter lógica de fallback quando pool pequeno

### (G3) Dificuldade adaptativa baseada em accuracy
**Objetivo**: Quando usuário melhora, puxar palavras/sentenças mais difíceis; quando piora, facilitar.

**Implementação**:
- Criar função `_get_difficulty_bias(user_accuracy: float) -> float`
  - Accuracy < 0.7: bias = 0.2 (favorecer ranks baixos/fácil)
  - Accuracy 0.7-0.9: bias = 0.5 (uniforme)
  - Accuracy > 0.9: bias = 0.8 (favorecer ranks altos/difícil)
- Aplicar em seleção de **NOVAS** palavras:
  - Em vez de `rank <= max_rank`, usar `rank BETWEEN min_rank AND max_rank`
  - `min_rank = max(1, max_rank * (1 - bias))`
- Aplicar em seleção de **FRASES** (se `Sentence.difficulty` existir):
  - Ordenar por proximidade ao difficulty alvo

### (G4) Erros voltam mais cedo (consistência Spec4 vs Lingvist)
**Objetivo**: Palavras erradas devem reaparecer mais frequentemente que as acertadas, de forma previsível.

**Decisão de arquitetura** (Parte D):
- **Opção escolhida**: **Opção 1** - Relearn por endpoint/mode da sessão
  - `/next-lingvist` usa relearn queue
  - `/next-spec4` NÃO usa relearn (mantém comportamento original)
  - Adicionar `mode?: 'spec4'|'lingvist'` no `AnswerRequest` (default = spec4)
  - Backend usa `AnswerRequest.mode` para decidir se aplica relearn
- **Justificativa**: Mais seguro, não quebra Spec4, permite misturar modos na mesma sessão

**Implementação**:
1. Adicionar `mode` em `AnswerRequest` schema (default='spec4')
2. Modificar `submit_answer()` para usar `answer_data.mode` em vez de `user.mode`
3. Garantir que "sair do relearn" siga especificação (quality >= 4)

### (G5) Nomes melhores dos modos (UI-only)
**Objetivo**: Renomear modos para nomes intuitivos, sem alterar IDs/rotas.

**Mapeamento**:
- `spec4` → **"Treino Clássico"** (multiple choice, spaced repetition puro)
- `lingvist` → **"Treino Lacunas"** (preenchimento ativo, hints, áudio)

**Implementação**:
- Frontend: trocar textos em UserSelection, StudySession, LingvistSession
- Manter: `mode=spec4|lingvist` em localStorage, API, DB
- Atualizar descrições: remover "Multiple choice" (errado), usar descrições reais

### (G6) Multi-idioma: remover hardcode "en"
**Objetivo**: Sistema funcionar para qualquer target language do usuário.

**Implementação**:
- Remover `WordFrequency.language_code == "en"` hardcoded em:
  - `get_next_new_word_rank()`
  - `update_contiguous_mastered_rank()`
- Usar `user.target_language.code` dinamicamente

## Non-Goals

- Trocar SM-2/FSRS agora (mantém algoritmo atual)
- Mudar contratos de API existentes (adiciona apenas `mode` em AnswerRequest com default)
- Mexer em Spec4/Lingvist a ponto de quebrar comportamentos estabelecidos
- Implementar dificuldade por IA/ML (usa métricas existentes)

## Success Criteria (Mensurável)

### Performance & Estabilidade
- [ ] 200 chamadas consecutivas a `/api/v1/cards/next-spec4` não retornam 404
- [ ] 200 chamadas consecutivas a `/api/v1/cards/next-lingvist` não retornam 404
- [ ] Tempo p95 do `/next-*` < 200ms em DB seedado (10K+ palavras)

### Seleção de Frases (G1)
- [ ] Com pool de 12+ frases para uma palavra, mesma frase NÃO aparece nas últimas 10 ocorrências
- [ ] Teste pytest: `test_get_sentence_avoids_last_k_when_pool_sufficient`

### Seleção de Palavras Novas (G2)
- [ ] Teste pytest: `_get_random_new_card` retorna palavra "nova" (sem UserCardState)
- [ ] Teste pytest: `_get_random_new_card` não carrega todas palavras em memória (sem `.all()`)

### Dificuldade Adaptativa (G3)
- [ ] Prova: Com accuracy 95%, ranks médios das novas palavras > 70% do max_rank
- [ ] Prova: Com accuracy 60%, ranks médios das novas palavras < 40% do max_rank
- [ ] Teste pytest: `test_difficulty_bias_accuracy_high_returns_higher_ranks`

### Persistência de Modo (Fix Critical Bug)
- [ ] UI chama `PATCH /users/{id}` com `mode` ao criar/editar usuário
- [ ] Teste Playwright: Selecionar "Treino Lacunas" ativa relearn queue

### Nomes na UI (G5)
- [ ] Teste Playwright: Texto "Spec4" não aparece mais na UI
- [ ] Teste Playwright: Texto "Lingvist" não aparece mais na UI
- [ ] Teste Playwright: "Treino Clássico" e "Treino Lacunas" aparecem corretamente

### Multi-idioma (G6)
- [ ] Teste pytest: Usuário com target_language="fr" recebe palavras francesas

## Plano de Implementação (Fases)

### FASE 1 - AUDIT (Concluído)
- [x] Confirmar que UI não persiste `User.mode`
- [x] Documentar funções de seleção de palavras/frases
- [x] Identificar bugs de performance e hardcodes

### FASE 2 - OPENSPEC (Esta fase)
- [x] Criar proposal document
- [ ] Aguardar aprovação

### FASE 3 - APPLY (Implementação incremental)

#### Parte A - Fix Critical Bug: Persistir mode
**Arquivos**: `frontend/src/components/UserSelection.tsx`, `frontend/src/App.tsx`

**Mudanças**:
```typescript
// UserSelection.tsx linha 98-103
const userData: CreateUserRequest = {
  username: newUsername.trim(),
  language_preference: nativeLanguage,
  target_language: targetLanguage,
  word_goal_rank: wordGoalRank,
  mode: selectedMode  // ADICIONAR
};

// UserSelection.tsx linha 124-129
const handleStartLearning = async (userId: string, mode: TrainingMode) => {
  localStorage.setItem('preferredTrainingMode', mode);

  // ADICIONAR: Persistir mode no backend
  await usersApi.updateUser(userId, { mode });

  onModeSelect(mode);
  onUserSelected(userId);
};

// UserSelection.tsx linha 160-165
const updateData: UpdateUserRequest = {
  username: editUsername.trim(),
  language_preference: editNativeLanguage,
  target_language: editTargetLanguage,
  word_goal_rank: editWordGoalRank,
  mode: selectedMode  // ADICIONAR
};
```

**Validação**:
```bash
# Criar usuário com mode=lingvist
USER_ID=$(curl -X POST http://localhost:8000/api/v1/users/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test","mode":"lingvist"}' | jq -r '.id')

# Verificar que mode foi persistido
curl http://localhost:8000/api/v1/users/$USER_ID | jq '.mode'
# Esperado: "lingvist"
```

#### Parte B - Seleção de Frases (K=10 REAL por palavra)
**Arquivo**: `api/app/services/vocabulary_progression.py`

**Mudança em `get_sentence_for_word()` linha 99-110**:
```python
# ANTES (K global):
usage_stats = self.db.query(
    ReviewEvent.sentence_id,
    func.count(ReviewEvent.id).label('usage_count'),
    func.max(ReviewEvent.created_at).label('last_used_at')
).filter(
    and_(
        ReviewEvent.user_id == user_id,
        ReviewEvent.sentence_id.in_(candidate_sentence_ids)
    )
).group_by(ReviewEvent.sentence_id).all()

# DEPOIS (K por palavra):
usage_stats = self.db.query(
    ReviewEvent.sentence_id,
    func.count(ReviewEvent.id).label('usage_count'),
    func.max(ReviewEvent.created_at).label('last_used_at')
).filter(
    and_(
        ReviewEvent.user_id == user_id,
        ReviewEvent.sentence_id.in_(candidate_sentence_ids),
        ReviewEvent.card_id.in_(  # ADICIONAR: filtrar por word_id
            self.db.query(Card.id).join(Sentence).filter(Sentence.word_id == word_id)
        )
    )
).group_by(ReviewEvent.sentence_id).all()
```

**Validação**:
```python
# tests/integration/test_sentence_selection.py
def test_get_sentence_avoids_last_k_for_same_word():
    """Mesma frase não aparece nas últimas 10 ocorrências DA MESMA palavra"""
    # Setup: word com 15 sentenças
    # Executar: chamar get_sentence_for_word 12x
    # Assert: nenhuma frase se repete dentro das últimas 10
```

#### Parte C - Seleção de Palavras Novas (performance)
**Arquivo**: `api/app/services/card_selection.py`

**Mudança em `_get_random_new_card()` linha 220-243**:
```python
# ANTES:
words_without_recent = query.filter(
    ~Word.id.in_(exclusions | recent_word_ids)
).all()  # Carrega TUDO
word = random.choice(words_without_recent)

# DEPOIS:
# Adicionar filtro para palavras realmente novas
new_words_query = query.filter(
    ~Word.id.in_(exclusions | recent_word_ids),
    ~Word.id.in_(
        self.db.query(UserCardState.word_id)
        .filter(UserCardState.user_id == user_id)
    )
)

# DB-side random com limit (PostgreSQL)
word = new_words_query.order_by(func.random()).limit(1).first()
```

**Validação**:
```python
# tests/integration/test_card_selection.py
def test_get_random_new_card_returns_truly_new_word():
    """Palavra nova não tem UserCardState"""
    # Setup: usuário com progress, DB com palavras
    # Executar: chamar _get_random_new_card
    # Assert: palavra retornada não tem UserCardState para o usuário

def test_get_random_new_card_no_all():
    """Não usa query.all()"""
    # Spy/Mock na query para garantir que .all() não é chamado
```

#### Parte D - Dificuldade Adaptativa
**Arquivo**: `api/app/services/card_selection.py`

**Adicionar função** (após linha 672):
```python
def _get_difficulty_bias(self, user: User) -> float:
    """
    Calculate difficulty bias based on user's recent accuracy.

    Returns:
        float between 0.0 (easiest) and 1.0 (hardest)
    """
    if user.accuracy_last_20 is None:
        return 0.5  # Neutral without data

    if user.accuracy_last_20 < 0.7:
        return 0.2  # Favor easier ranks
    elif user.accuracy_last_20 > 0.9:
        return 0.8  # Favor harder ranks
    else:
        return 0.5  # Uniform
```

**Modificar `_get_random_new_card()` linha 193-202**:
```python
# ANTES:
max_rank = min(progress.current_window_end_rank, progress.word_goal_rank)
query = self.db.query(Word).join(WordFrequency, ...).filter(
    WordFrequency.rank <= max_rank
)

# DEPOIS:
user = self.db.query(User).filter(User.id == user_id).first()
difficulty_bias = self._get_difficulty_bias(user)

max_rank = min(progress.current_window_end_rank, progress.word_goal_rank)
min_rank = max(1, int(max_rank * (1 - difficulty_bias)))

query = self.db.query(Word).join(WordFrequency, ...).filter(
    WordFrequency.rank.between(min_rank, max_rank)  # BETWEEN em vez de <=
)
```

**Validação**:
```python
def test_difficulty_bias_accuracy_high_returns_higher_ranks():
    """Accuracy 95% -> ranks medianos > 70% do max_rank"""
    # Setup: user com accuracy_last_20 = 0.95
    # Executar: chamar _get_random_new_card 100x
    # Assert: rank_mediano > 0.7 * max_rank
```

#### Parte E - Consistência Relearn (mode por request)
**Arquivo**: `api/app/schemas/card.py`

**Adicionar em `AnswerRequest`**:
```python
class AnswerRequest(BaseModel):
    answer: str
    response_time_ms: int
    attempts: int = 1
    hints_used: int = 0
    mode: str = "spec4"  # ADICIONAR: default mantém compatibilidade
```

**Arquivo**: `api/app/api/api_v1/endpoints/cards.py`

**Modificar `submit_answer()`**:
```python
# ANTES:
user_mode = user.mode if user else 'spec4'
if user_mode == 'lingvist' and quality < 3:
    # enter relearn queue

# DEPOIS:
answer_mode = answer_data.mode  # Usar mode do request
if answer_mode == 'lingvist' and quality < 3:
    # enter relearn queue
```

**Validação**:
```bash
# Testar Spec4: relearn NÃO deve ser ativado
curl -X POST "http://localhost:8000/api/v1/cards/$CARD_ID/answer?user_id=$USER_ID" \
  -H "Content-Type: application/json" \
  -d '{"answer":"wrong","response_time_ms":3000,"mode":"spec4"}'

# Verificar no banco: is_relearn = FALSE

# Testar Lingvist: relearn DEVE ser ativado
curl -X POST "http://localhost:8000/api/v1/cards/$CARD_ID/answer?user_id=$USER_ID" \
  -H "Content-Type: application/json" \
  -d '{"answer":"wrong","response_time_ms":3000,"mode":"lingvist"}'

# Verificar no banco: is_relearn = TRUE
```

#### Parte F - Multi-idioma
**Arquivo**: `api/app/services/vocabulary_progression.py`

**Modificar `get_next_new_word_rank()` linha 198**:
```python
# ANTES:
WordFrequency.language_code == "en"  # TODO

# DEPOIS:
# Adicionar no início da função (linha ~184):
user = self.db.query(User).filter(User.id == user_id).first()
target_language = self.db.query(Language).filter(Language.id == user.target_language_id).first()

# Depois usar:
WordFrequency.language_code == target_language.code
```

**Mesma mudança em `update_contiguous_mastered_rank()`**.

**Validação**:
```python
def test_get_next_new_word_respects_user_target_language():
    """Usuário com target_language='fr' recebe palavras francesas"""
    # Setup: user com target_language = 'fr'
    # Executar: get_next_new_word_rank
    # Assert: word retornada tem language_code = 'fr'
```

#### Parte G - Renomear Modos na UI
**Arquivos**: `frontend/src/components/UserSelection.tsx`, `frontend/src/components/ProfileCard.tsx`

**Mudanças**:
```typescript
// UserSelection.tsx
const MODE_LABELS: Record<TrainingMode, {name: string, description: string}> = {
  spec4: {
    name: "Treino Clássico",
    description: "Múltipla escolha com spaced repetition"
  },
  lingvist: {
    name: "Treino Lacunas",
    description: "Preenchimento ativo com hints e áudio"
  }
};

// No render, usar MODE_LABELS[selectedMode].name
// Remover "Multiple choice" (está errado)
```

**Validação**:
```typescript
// tests/e2e/mode-naming.spec.ts
test('mostra nomes corretos dos modos', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByText('Spec4')).not.toBeVisible();
  await expect(page.getByText('Lingvist')).not.toBeVisible();
  await expect(page.getByText('Treino Clássico')).toBeVisible();
  await expect(page.getByText('Treino Lacunas')).toBeVisible();
});
```

### FASE 4 - TESTES & VALIDAÇÃO

#### Pytest Tests
```python
# tests/integration/test_selection_tuning.py

def test_get_sentence_avoids_last_k_when_pool_sufficient():
    """G1: Com pool>=12, frase não se repete nas últimas 10 da mesma palavra"""

def test_get_random_new_card_returns_truly_new_word():
    """G2: Palavra nova não tem UserCardState"""

def test_get_random_new_card_no_all():
    """G2: Não usa query.all()"""

def test_difficulty_bias_accuracy_high():
    """G3: Accuracy alta -> ranks altos"""

def test_difficulty_bias_accuracy_low():
    """G3: Accuracy baixa -> ranks baixos"""

def test_relearn_spec4_mode_disabled():
    """G4: mode='spec4' não ativa relearn"""

def test_relearn_lingvist_mode_enabled():
    """G4: mode='lingvist' ativa relearn no erro"""

def test_multi_language_target_respected():
    """G6: Respeita target_language do usuário"""
```

#### Playwright Tests
```typescript
// tests/e2e/selection-tuning.spec.ts

test('modo persiste no backend', async ({ page }) => {
  // Criar usuário em modo Lingvist
  // Verificar que User.mode == 'lingvist' no backend
});

test('nomes dos modos aparecem corretamente', async ({ page }) => {
  // Verificar "Treino Clássico" e "Treino Lacunas"
  // Verificar que "Spec4" e "Lingvist" não aparecem
});

test('stability test: 200 cards sem 404', async ({ page }) => {
  // Carregar 200 cards consecutivos
  // Verificar que nenhum retorna 404
});
```

#### Smoke Manual
```bash
# 1. Criar usuário Spec4
USER_SPEC4=$(curl -X POST http://localhost:8000/api/v1/users/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test_spec4","mode":"spec4"}' | jq -r '.id')

# 2. Criar usuário Lingvist
USER_LINGVIST=$(curl -X POST http://localhost:8000/api/v1/users/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test_lingvist","mode":"lingvist"}' | jq -r '.id')

# 3. Carregar 10 cards Spec4 (sem relearn)
for i in {1..10}; do
  CARD=$(curl -s "http://localhost:8000/api/v1/cards/next-spec4?user_id=$USER_SPEC4")
  # ... enviar answer com mode='spec4'
done

# 4. Carregar 10 cards Lingvist (com relearn no erro)
for i in {1..10}; do
  CARD=$(curl -s "http://localhost:8000/api/v1/cards/next-lingvist?user_id=$USER_LINGVIST")
  # ... enviar answer errado com mode='lingvist'
  # Verificar relearn_due foi setado
done

# 5. Verificar UI
# Abrir frontend, verificar que "Treino Clássico" e "Treino Lacunas" aparecem
```

## Migration

### Database Changes
Nenhuma migration necessária (campos já existem do Adaptive Scheduler v1).

### API Changes
- **Adiciona**: `AnswerRequest.mode` (default='spec4') - backward compatible
- **Mantém**: Todos os endpoints existentes
- **Não quebra**: Clients antigos (usam default)

## Rollback Plan

Se algo der errado:
1. Revert code: `git revert <commit-hash>`
2. Frontend volta a usar apenas localStorage (modo atual)
3. Backend continua com mode='spec4' default seguro
4. Nenhuma migration para reverter

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Relearn queue agressiva demais | Usuário vê mesma palavra muitas vezes | Ajustar intervalos (já configurados em Adaptive Scheduler) |
| Dificuldade adaptativa bug | Seleção retorna vazio | Fallback para min_rank=1 quando bias falhar |
| Multi-idioma sem dados | Usuário FR não tem palavras | Verificar no seeding, mostrar erro claro |
| Performance de ORDER BY RANDOM() | Lentidão em DB grande | Usar `TABLESAMPLE` ou amostragem por rank se necessário |

## Timeline Estimate

- Parte A (Fix mode persist): 30 min
- Parte B (K=10 real): 1 hora
- Parte C (performance): 1 hora
- Parte D (dificuldade adaptativa): 1.5 horas
- Parte E (relearn por request): 1 hora
- Parte F (multi-idioma): 30 min
- Parte G (nomes UI): 30 min
- Testes + Validação: 2 horas
- **Total**: 8 horas

## References

- Adaptive Scheduler v1: `openspec/changes/2025-12-adaptive-scheduler-v1.md`
- Card Selection: `api/app/services/card_selection.py`
- Vocabulary Progression: `api/app/services/vocabulary_progression.py`
- Frontend UI: `frontend/src/components/UserSelection.tsx`
