# Change: Lingvist Mode - Inline Cloze with Progressive Hints

**Date**: 2025-12-24
**Status**: 📋 Proposed
**Version**: v1.0
**Type**: New Feature (New Training Mode)
**Scope**: Backend (API, models), Frontend (new route/components), OpenSpec (SPEC.md, API.md, DOMAINS.md)

---

## Overview

Introduz um novo modo de treino inspirado no [Lingvist.com](https://lingvist.com): **preenchimento de lacunas (cloze) com input inline**, validação em tempo real, hints progressivos e reprodução de áudio da frase completa apenas após o acerto. Este modo **coexiste com o modo Spec4 atual**, não o substitui. Usuários podem escolher entre os modos.

**Motivação**: O modo Spec4 atual (flashcard com botão "Check") é eficaz para revisão espaciada, mas não oferece a experiência de digitação inline que ajuda na fixação ortográfica e na memória muscular. Lingvist.com prova que input direto + hints progressivos + áudio pós-acerto cria um loop de aprendizado mais envolvente.

## Problem Statement

### Estado Atual (Spec4 Mode)

1. **Flashcard tradicional**: Usuário vê frase com lacuna `___`, digita resposta em campo separado, clica botão "Check"
2. **Fluxo interrompido**: Botão "Check" quebra o ritmo de digitação
3. **Feedback tardío**: Usuário só sabe se errou após submissão completa
4. **Sem hints progressivos**: Quando erra, precisa adivinhar ou desistir
5. **Áudio imediato**: Toca ao carregar card (pode ser distração)
6. **Sem tradução PT-BR**: Usuários brasileiros não têm apoio nativo

### Necessidade do Novo Modo

- **Input inline** aumenta engajamento (estado de fluxo)
- **Validação em tempo real** reduz frustração
- **Hints progressivos** mantêm desafio sem travar
- **Áudio pós-acerto** reforça positivo após sucesso
- **Traduções PT-BR** ajudam usuários BR
- **Tag gramatical PT-BR** apoia compreensão gramatical

## Goals / Non-Goals

### Goals (MVP v1.0)

1. **Input inline na lacuna**: Chip cinza `___` vira input `_____`
2. **Sem botão "Check"**: Submissão automática ao digitar resposta correta
3. **Validação em tempo real**: Prefix match visual sem chamar servidor
4. **Hints progressivos**: Aparecem automaticamente após erros/tempo
   - Hint 1: Tag gramatical PT-BR (ex: "substantivo, plural")
   - Hint 2: Máscara de tamanho (ex: "_ _ _ _ _")
   - Hint 3: Primeira letra
   - Hint 4: Revelar letras progressivamente
   - Hint 5: Tradução PT-BR da palavra
   - Hint 6: Dica semântica opcional
5. **Áudio após acerto**: Tocar frase completa apenas quando `correct=true`
6. **Avanço pós-áudio**: Próximo card só carrega após áudio terminar (ou timeout 3s)
7. **Traduções PT-BR**:
   - `word_translation_pt`: tradução da palavra-alvo
   - `sentence_translation_pt`: tradução da frase completa
8. **Tag gramatical PT-BR**: exibir em PT-BR (ex: "verbo, infinitivo")
9. **Reutilizar Spec4**: Gating, janela, anti-repetição, seleção de cards
10. **Mix**: 80% revisão / 20% novas (configurável)

### Non-Goals (explícitos fora do escopo)

1. **Tradução perfeita**: Sentenças sem tradução PT-BR mostram "Tradução indisponível" (MVP aceitável)
2. **FSRS completo**: Usar SM-2 existente, sem migrar para FSRS neste modo
3. **Report/Skip persistente**: Não salvar skip/reports por card neste modo (v1.0)
4. **Keyboard customizado**: Não implementar teclado especial (usar nativo)
5. **Áudio voz diferente**: Não implementar seletor de voz (usar padrão Piper)
6. **Gamificação**: Sem pontos, streaks, conquistas neste modo (v1.0)
7. **Offline mode**: Requer conexão para TTS (áudio online)
8. **Multiplayer**: Sem leaderboards ou competição (v1.0)

## UX Specification

### Layout

```
┌─────────────────────────────────────────────┐
│  ←            [⋮] Menu 3 pontos      1/5   │  ← Top bar
├─────────────────────────────────────────────┤
│                                             │
│  (opcional: "Nova palavra" badge if is_new) │
│                                             │
│        The ___ is on the table.             │  ← Frase
│              [__________]                   │  ← Input inline
│                                             │
│        📚 Dracula                          │  ← Fonte (se sentence bank)
│                                             │
│        "substantivo, feminino, singular"    │  ← Tag gramatical PT-BR
│                                             │
├─────────────────────────────────────────────┤
│  ▼ Traduções (toque para expandir)          │  ← Bottom sheet (collapsed)
└─────────────────────────────────────────────┘

ESTADO CORRETO (após digitar "book"):
┌─────────────────────────────────────────────┐
│        The book is on the table.             │  ← Input some (verde)
│              [__________] ✓                 │
│                                             │
│  🎵 [toca áudio da frase completa...]      │  ← Áudio toca
└─────────────────────────────────────────────┘
↓ (após áudio terminar)
[avança para próximo card automaticamente]

ESTADO ERRADO (3+ erros):
┌─────────────────────────────────────────────┐
│        The ___ is on the table.             │
│              [__________]                   │
│                                             │
│  💡 Dica: começa com "b"                    │  ← Hint 3
│  📖 Tradução: livro                         │  ← Hint 5
│                                             │
│  ▼ Traduções (expandido)                    │
│  ┌───────────────────────────────────────┐  │
│  │ Palavra: book                          │  │
│  │ Tradução: livro                        │  │
│  │                                        │  │
│  │ Frase: The book is on the table.      │  │
│  │ Tradução: O livro está na mesa.       │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

### Componentes Principais

#### 1. **InlineGapInput** (novo)
- **Estado**: `focused`, `correct`, `wrong`, `hinting`
- **Comportamento**:
  - Auto-foco ao carregar card
  - Largura dinâmica baseada em tamanho da resposta
  - Submissão automática ao digitar resposta exata (normalizada)
  - Enter como fallback
  - Validação client-side (prefix match) sem chamar API

#### 2. **HintPanel** (novo)
- **Exibição**: Slide-down ou toast persistente
- **Animação**: Fade-in + slide-up
- **Hints**:
  ```
  Hint 1: "verbo, infinitivo"           → (grammar_tag_pt)
  Hint 2: "_ _ _ _ _"                   → (length_mask)
  Hint 3: "Começa com: b"               → (first_letter)
  Hint 4: "b _ _ k"                     → (reveal_letters)
  Hint 5: "Tradução: livro"             → (word_translation_pt)
  Hint 6: "Objeto que você lê"          → (semantic_hint)
  ```

#### 3. **BottomSheet** (novo)
- **Estado inicial**: Collapsed ("▼ Traduções")
- **Ao expandir**: Mostra `word_translation_pt` e `sentence_translation_pt`
- **Auto-expand**: Após 3 erros ou 30s preso (configurável)

#### 4. **MicroProgress** (novo)
- **Formato**: "3/10" ou "3/10 (novas: 2)"
- **Posição**: Top bar, alinhado à direita ou centro

#### 5. **OptionsMenu** (novo)
- **Ações** (menu 3 pontos):
  - "Pular este card" (skip → não conta como tentativa)
  - "Reportar problema" (abre modal)
  - "Sair do modo Lingvist" (volta para Spec4)

### Acessibilidade

- **Teclado**: Tab não usado (só 1 input), Enter submete
- **Foco**: Auto-foco na lacuna ao carregar card
- **Leitores de tela**: Aria-label na frase completa (ex: "The book is on the table. Input: 4 letters")
- **Contraste**: Input corretos (verde #059669), errados (vermelho #DC2626)

## Input Engine

### Regras de Submissão

#### 1. Auto-Submit (Padrão)
```typescript
function shouldAutoSubmit(userInput: string, correctAnswer: string): boolean {
  const normalizedInput = normalize(userInput);
  const normalizedAnswer = normalize(correctAnswer);

  // Regra 1: Match exato → auto-submeter
  if (normalizedInput === normalizedAnswer) {
    return true;
  }

  // Regra 2: Prefix match → visual feedback sem submeter
  if (normalizedAnswer.startsWith(normalizedInput)) {
    return false; // Mostra "até agora correto"
  }

  // Regra 3: Erro claro → mostrar feedback sem submeter
  return false;
}
```

#### 2. Normalização
```typescript
function normalize(text: string): string {
  return text
    .trim()                    // Remove espaços laterais
    .toLowerCase()             // Case insensitive
    .replace(/[.,!?;:()]/g, '') // Remove pontuação periférica
    .replace(/\s+/g, ' ');     // Normaliza espaços internos
}
```

#### 3. Validação Client-Side (Prefix Match)
```typescript
// Exibe "____" em cinza enquanto usuário digita
function getPrefixDisplay(userInput: string, correctAnswer: string): string {
  const normalizedInput = normalize(userInput);
  const normalizedAnswer = normalize(correctAnswer);

  if (normalizedAnswer.startsWith(normalizedInput)) {
    // Prefixo correto → mostra em verde
    return userInput + "____".repeat(normalizedAnswer.length - normalizedInput.length);
  } else {
    // Erro → mostra vermelho
    return userInput; // CSS adiciona classe .wrong
  }
}
```

#### 4. Enter como Fallback
```typescript
// Se usuário quiser submeter mesmo com prefixo parcial (ex: ambiguidade)
function onKeyDown(e: KeyboardEvent) {
  if (e.key === 'Enter') {
    submitAnswer();
  }
}
```

### Feedback Visual

- **Input vazio**: `_______` (cinza, placeholder)
- **Digitando correto** (prefix match): `bo____` (verde, underscores futuros)
- **Errado**: `box` (vermelho, shake animation)
- **Correto (auto-submetido)**: `book` (verde, checkmark ✓)
- **Hint ativo**: `_ _ _ k` (amarelo/laranja, letras reveladas)

## Hint Engine

### Gatilhos (Triggers)

Hints aparecem automaticamente quando:

```typescript
interface HintTrigger {
  mistakes_on_this_card: number;    // Erros neste card
  time_stuck_seconds: number;        // Segundos preso sem progresso
  consecutive_mistakes: number;      // Erros consecutivos
  total_attempts: number;            // Tentativas totais
}
```

#### Tabela de Hints

| Hint | Gatilho | Formato | Exemplo |
|------|---------|---------|---------|
| 1. Tag gramatical | `mistakes_on_this_card >= 1` | `"part_of_speech, form"` | `"substantivo, plural"` |
| 2. Máscara tamanho | `mistakes_on_this_card >= 2` | `"_ _ _ _ _"` | `"_ _ _ _"` |
| 3. Primeira letra | `mistakes_on_this_card >= 3` | `"Começa com: X"` | `"Começa com: b"` |
| 4. Revelar letras | `mistakes_on_this_card >= 4` | `"X _ X X"` | `"b _ _ k"` |
| 5. Tradução PT | `mistakes_on_this_card >= 5` | `"Tradução: XXX"` | `"Tradução: livro"` |
| 6. Dica semântica | `time_stuck_seconds >= 30` | `"XXX que você YYY"` | `"Objeto que você lê"` |

### Regras de Exibição

1. **Não revelar > 60%** antes de nova tentativa
   - Se resposta tem 4 letras, máx revelar 2 antes de usuário tentar de novo
   - Hint 4 (revelar letras) respeita isso

2. **Mesmo com tradução, usuário deve digitar**
   - Hint 5 mostra tradução, mas não preenche input
   - Usuário precisa digitar mesmo sabendo a resposta

3. **Hints persistem** até acerto ou avanço
   - Não "desaparecem" após serem mostrados
   - Cumulativos: Hint 1 + Hint 2 + ... + Hint 5

4. **Auto-expand BottomSheet** no Hint 5
   - Quando tradução aparece, bottom sheet expande automaticamente

### Implementação (Frontend)

```typescript
interface HintState {
  level: number;              // 0-6 (0 = sem hints)
  revealedLetters: string;    // "b _ _ k"
  showTranslation: boolean;   // true após hint 5
}

function shouldShowHint(hintState: HintState, trigger: HintTrigger): HintState | null {
  const newLevel = calculateHintLevel(trigger);

  if (newLevel > hintState.level) {
    return {
      level: newLevel,
      revealedLetters: revealLetters(correctAnswer, newLevel),
      showTranslation: newLevel >= 5
    };
  }

  return null; // Sem hint novo
}
```

## Áudio (Requisito Crítico)

### Comportamento

**NUNCA** tocar áudio automaticamente ao carregar card neste modo (diferente de Spec4).

**APENAS** após `POST /answer` retornar `correct=true`:

1. **Travar input** (desabilitar, prevenir mais edições)
2. **Mostrar estado correto** (verde, checkmark)
3. **Tocar `audio_sentence_url`** (frase completa com palavra preenchida)
4. **Aguardar áudio terminar** (evento `ended`)
5. **Avançar para próximo card**

### Fallback

Se áudio falhar/timeout (3s):

```typescript
audioElement.onended = () => advanceToNextCard();
audioElement.onerror = () => {
  console.warn('Áudio falhou, avançando anyway');
  setTimeout(() => advanceToNextCard(), 1000); // 1s de delay visual
};

setTimeout(() => {
  if (!advanced) {
    console.warn('Áudio timeout (3s), avançando anyway');
    advanceToNextCard();
  }
}, 3000);
```

### Geração da URL de Áudio

Backend deve retornar `audio_sentence_url` com a **palavra preenchida**:

```json
{
  "correct": true,
  "audio_sentence_url": "/api/tts/sentence/abc123?text=The%20book%20is%20on%20the%20table&lang=en"
}
```

Frontend usa essa URL para tocar áudio pós-acerto.

## Scheduler & Conteúdo

### Reutilizar Spec4

**Não** criar novo scheduler. Reutilizar `CardSelectionService` existente:

- ✅ Gating por `max_contiguous_mastered_rank`
- ✅ Janela de acesso (prefix + range)
- ✅ Mix novo/revisão (Target: 80/20)
- ✅ Anti-repetição (K=10 variedade de sentenças)
- ✅ SM-2 para intervalos

### Mix Recomendado

```python
# Em CardSelectionService.get_next_card_for_user()
if user.preferred_mode == "lingvist":
    target_new_share = 0.2  # 20% novas, 80% revisão
else:  # spec4
    target_new_share = 0.25  # 25% novas (atual)
```

**Decisão ABERTA**: Mix por usuário? Setting global?

- **Opção A**: Campo em `User` table: `preferred_mode: "spec4" | "lingvist"`
  - + Usuário escolhe
  - - Complexidade extra na UI

- **Opção B**: Switch global no app (mesmo mix para todos)
  - + Simples de implementar
  - - Menos flexível

**Recomendação**: Opção A (modo por usuário), mas MVP pode usar Opção B.

## Dados & Modelos (Postgres)

### Registrar Tentativas & Hints

**Decisão ABERTA**: Estender `ReviewEvent` vs nova tabela `Attempt`?

#### Opção A: Estender `ReviewEvent` (Recomendada)

```sql
ALTER TABLE review_event ADD COLUMN typed_answer VARCHAR(200);
ALTER TABLE review_event ADD COLUMN hints_used JSONB;
ALTER TABLE review_event ADD COLUMN attempt_index INTEGER DEFAULT 1;
```

**Exemplo `hints_used`**:
```json
{
  "grammar_tag": true,
  "length_mask": true,
  "first_letter": true,
  "revealed_letters": "b _ _ k",
  "translation": true,
  "semantic": false
}
```

**Vantagens**:
- ✅ Tudo em um lugar (review + tentativas)
- ✅ Backward compatible (colunas nullable)
- ✅ Fácil de query (JOIN com Card já existe)

**Desvantagens**:
- ❌ `ReviewEvent` pode ficar "pesado"
- ❌ Mistura conceitos (review vs attempt)

#### Opção B: Nova Tabela `Attempt`

```sql
CREATE TABLE attempt (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  card_id UUID NOT NULL REFERENCES card(id),
  user_id UUID NOT NULL REFERENCES "user"(id),
  typed_answer VARCHAR(200),
  is_correct BOOLEAN NOT NULL,
  attempt_index INTEGER NOT NULL,
  hints_used JSONB,
  time_to_correct_ms INTEGER,
  created_at TIMESTAMP DEFAULT NOW()
);
```

**Vantagens**:
- ✅ Separação clara de conceitos
- ✅ Pode ter múltiplas tentativas por card
- ✅ Melhor para analytics futuro

**Desvantagens**:
- ❌ Mais complexo (nova tabela, migrations, relacionamentos)
- ❌ Precisa de JOIN para queries

**RECOMENDAÇÃO**: Opção A (estender `ReviewEvent`) para MVP v1.0.

### Campos Novos em `Word`

```sql
ALTER TABLE word ADD COLUMN pt_translation VARCHAR(200);
```

Para armazenar tradução PT-BR da palavra (ex: "book" → "livro").

### Campos Existentes em `Sentence`

Já existe `translation` (VARCHAR(1000)). Vamos assumir:

- `translation` = tradução PT-BR da frase completa
- Se vazio → UI mostra "Tradução indisponível"

## API Contracts

### Decisão ABERTA: Novo Endpoint vs Campos Opcionais

#### Opção A: Novo Endpoint `GET /api/v1/cards/next-lingvist` (Recomendada)

```json
{
  "card_id": "abc123",
  "word_id": "def456",
  "sentence": "The ___ is on the table.",
  "gap": {"start": 4, "end": 8},
  "correct_answer": "book",
  "grammar_tag_pt": "substantivo, masculino, singular",
  "word_translation_pt": "livro",
  "sentence_translation_pt": "O livro está na mesa.",
  "sentence_source": "Dracula",
  "audio_word_url": "/api/tts/word/...",
  "audio_sentence_url": "/api/tts/sentence/...",
  "is_new": true,
  "micro_progress": "3/10"
}
```

**Vantagens**:
- ✅ Separado de Spec4 (backward compatibility garantida)
- ✅ Payload enriquecido sem poluir `/next-spec4`
- ✅ Fácil de versionar (v2, v3)

**Desvantagens**:
- ❌ Mais código (endpoint novo)

#### Opção B: Estender `/next-spec4` com Campos Opcionais

```json
{
  "card_id": "abc123",
  "word": "book",
  "sentence": "The ___ is on the table.",
  "sentence_translation": "...",
  "grammar_hint": "",
  // ... campos existentes ...

  // Campos novos (opcionais)
  "grammar_tag_pt": "substantivo, ...",
  "word_translation_pt": "livro",
  "sentence_translation_pt": "O livro ..."
}
```

**Vantagens**:
- ✅ Um endpoint só
- ✅ Frontend Spec4 pode ignorar campos novos

**Desvantagens**:
- ❌ Mistura conceitos (Spec4 vs Lingvist)
- ❌ Mais difícil de versionar
- ❌ Payload inchado para Spec4

**RECOMENDAÇÃO**: Opção A (novo endpoint `/next-lingvist`).

### Request/Response - Endpoint Lingvist

#### `GET /api/v1/cards/next-lingvist`

**Query Params**:
```
user_id: UUID (opcional, default=demo)
exclude_card_id: UUID (opcional, anti-repetição)
```

**Response 200**:
```json
{
  "card_id": "550e8400-e29b-41d4-a716-446655440000",
  "word_id": "660e8400-e29b-41d4-a716-446655440000",
  "sentence_id": "770e8400-e29b-41d4-a716-446655440000",
  "word": "book",
  "sentence": "The ___ is on the table.",
  "gap": {"start": 4, "end": 8},
  "correct_answer": "book",  // ⚠️ Novo campo (não em Spec4)
  "grammar_tag_pt": "substantivo, masculino, singular",
  "word_translation_pt": "livro",
  "sentence_translation_pt": "O livro está na mesa.",
  "sentence_source": "Dracula",
  "is_new": true,
  "micro_progress": {
    "current": 3,
    "total": 10,
    "new_words": 2
  },
  "audio_word_url": "/api/tts/word/...",
  "audio_sentence_url": "/api/tts/sentence/..."
}
```

**Response 404**:
```json
{
  "error": "No cards available",
  "message": "No cards available for study at this time"
}
```

#### `POST /api/v1/cards/{card_id}/answer` (Reutilizar)

**Request** (mesmo de Spec4):
```json
{
  "answer": "book",
  "response_time_ms": 3500
}
```

**Response 200**:
```json
{
  "correct": true,
  "correct_answer": "book",
  "sentence_full": "The book is on the table.",
  "quality": 5,
  "next_review_at": "2024-01-21T10:00:00Z",
  "audio_sentence_url": "/api/tts/sentence/...?text=The%20book%20is%20on%20the%20table&lang=en"
}
```

**Diferença de Spec4**: `audio_sentence_url` inclui texto completo da frase (com palavra preenchida) para tocar pós-acerto.

## Traduções PT-BR

### Dados Existentes

1. **`Word.pt_translation`** (nova coluna)
   - Seed v1.0: **VAZIO** (MVP aceita isso)
   - Futuro: Preencher via script de tradução ou API

2. **`Sentence.translation`** (coluna existente)
   - Sentence Bank: **PRENCHIDO** (traduzido via script?)
   - Templates antigos: **VAZIO** → "Tradução indisponível"

### Implementação Incremental

#### Fase 1 (MVP v1.0): Aceitar Vazio

```typescript
// Frontend
if (!word_translation_pt) {
  // Não mostrar nada (ou ícone de tradução desabilitado)
}

if (!sentence_translation_pt) {
  // Mostrar "Tradução indisponível" (cinza, italic)
}
```

#### Fase 2 (Futura): Preencher Dados

- Script para traduzir `Word.lemma` via API (ex: LibreTranslate, Google Translate)
- Script para traduzir `Sentence.text` do sentence bank
- Migration para popular colunas

## Plano de Implementação

### Backend

1. **Migração**: Adicionar colunas
   - `Word.pt_translation`
   - `ReviewEvent.typed_answer`, `.hints_used`, `.attempt_index`

2. **Novo endpoint**: `GET /api/v1/cards/next-lingvist`
   - Reutilizar `CardSelectionService` (spec4)
   - Adicionar `correct_answer` ao response
   - Adicionar campos PT-BR
   - Calcular `micro_progress`

3. **Modificar resposta do `/answer`**:
   - Incluir `audio_sentence_url` com texto completo

4. **Grammar Tags**:
   - Mapear `part_of_speech` para PT-BR
   - Adicionar contexto (ex: "verb, past tense")

### Frontend

1. **Nova rota**: `/train/lingvist`
   - Página separada de `/study`

2. **Novos componentes**:
   - `InlineGapInput.tsx`
   - `HintPanel.tsx`
   - `BottomSheet.tsx`
   - `MicroProgress.tsx`
   - `OptionsMenu.tsx`

3. **Áudio pós-acerto**:
   - Hook `usePostCorrectAudio`
   - Lógica de timeout (3s)
   - Avanço automático após `ended`

4. **Hints**:
   - Hook `useProgressiveHints`
   - Lógica de triggers
   - Animações

5. **Navegação**:
   - Adicionar link em home/study para "Modo Lingvist"

### Testes

#### Playwright (E2E)

```typescript
test('Lingvist mode: auto-submit on correct answer', async ({ page }) => {
  await page.goto('/train/lingvist');

  // Card carrega com input focado
  const input = await page.locator('input[aria-label="Lacuna"]');
  await expect(input).toBeFocused();

  // Digitar resposta correta
  await input.type('book');

  // Auto-submete (sem clicar em Check)
  await expect(page.locator('[data-testid="feedback-correct"]')).toBeVisible();

  // Áudio toca
  await expect(page.locator('audio')).toHaveAttribute('src', /sentence/);

  // Avança para próximo após áudio
  await page.waitForSelector('[data-testid="feedback-correct"]', { state: 'hidden' });
  await expect(page.locator('text=/\\d+\\/\\d+/')).toHaveText(/2\\/10/);
});

test('Lingvist mode: hints appear on mistakes', async ({ page }) => {
  await page.goto('/train/lingvist');
  const input = await page.locator('input[aria-label="Lacuna"]');

  // Errar 3 vezes
  await input.type('wrong');
  await page.keyboard.press('Enter');
  await expect(page.locator('[data-testid="feedback-wrong"]')).toBeVisible();

  await input.clear();
  await input.type('bad');
  await page.keyboard.press('Enter');
  await expect(page.locator('[data-testid="feedback-wrong"]')).toBeVisible();

  // Hint 3 aparece (primeira letra)
  await expect(page.locator('text=/Começa com:/')).toBeVisible();
});
```

#### Pytest (Backend)

```python
def test_next_lingvist_returns_correct_answer(client, db_session):
    response = client.get("/api/v1/cards/next-lingvist?user_id=demo")

    assert response.status_code == 200
    data = response.json()

    assert "correct_answer" in data
    assert data["word"] != data["correct_answer"]  # Lacuna
    assert "grammar_tag_pt" in data
    assert "word_translation_pt" in data
    assert "micro_progress" in data

def test_next_lingvist_reuses_spec4_gating(client, db_session):
    """Testa que Spec4 gating funciona no modo Lingvist"""
    # Criar user com max_contiguous_mastered_rank = 100
    user = create_user(max_contiguous_mastered_rank=100)

    response = client.get(f"/api/v1/cards/next-lingvist?user_id={user.id}")
    data = response.json()

    # Verificar que word rank <= 100 + range
    assert data["word"]["rank"] <= 200  # max_contiguous_mastered_rank + 100
```

### Compatibilidade

- **Modo Spec4 permanece disponível** em `/study`
- **Nenhuma mudança em Spec4**:
  - Botão "Check" mantido
  - Áudio ao carregar card mantido
  - Fluxo inalterado

- **Modo Lingvist como alternativa** em `/train/lingvist`
  - Usuário escolhe modo
  - Settings salvam preferência

## Validation Plan

### Backend

```bash
# 1. Testar novo endpoint
curl "http://localhost:8000/api/v1/cards/next-lingvist?user_id=demo" | jq '.correct_answer'
# Esperado: retorna palavra correta

# 2. Verificar Spec4 ainda funciona
curl "http://localhost:8000/api/v1/cards/next-spec4?user_id=demo" | jq '.word'
# Esperado: retorna card sem 'correct_answer'

# 3. Testar mix (80/20)
# Criar 10 cards (9 revisão, 1 nova)
# Chamar /next-lingvist 10x
# Esperado: ~8 revisão, ~2 novas (margem)

# 4. Verificar migrations
alembic upgrade head
# Esperado: columns added sem erros
```

### Frontend

```bash
# 1. Build
npm run build
# Esperado: sem erros TypeScript

# 2. Test E2E
npx playwright test lingvist-mode.spec.ts
# Esperado: todos passam

# 3. Sanity Spec4
npx playwright test spec4-mode.spec.ts
# Esperado: todos passam (sem regressão)
```

### Evidências de Aceite

1. ✅ Usuário consegue acessar `/train/lingvist`
2. ✅ Input auto-foca ao carregar
3. ✅ Digitar resposta correta auto-submete (sem Enter)
4. ✅ Áudio toca após acerto
5. ✅ Próximo card carrega após áudio terminar
6. ✅ Hints aparecem após erros
7. ✅ Bottom sheet expande ao tocar
8. ✅ Traduções PT-BR aparecem (ou "indisponível")
9. ✅ Spec4 ainda funciona em `/study`
10. ✅ Não há erros no console

## Risks & Mitigations

### 1. Autoplay Policy Bloqueia Áudio Pós-Acerto

**Risco**: Browsers bloqueiam `audio.play()` se não houver gesto do usuário.

**Mitigação**:
- Usuário acabou de digitar (gesture válido)
- `audio.play()` em handler de clique/keydown
- Fallback: se bloqueado, mostrar botão "▶ Ouvir frase"

**Validação**: Testar em Chrome/Firefox/Safari com autoplay desabilitado.

### 2. Regressão de Spec4

**Risco**: Mudanças no backend quebram Spec4.

**Mitigação**:
- Endpoint novo (`/next-lingvist`), não alterar `/next-spec4`
- Testes E2E Spec4 continuam passando
- Code review focado em backward compatibility

**Rollback**: Se Spec4 quebrar, reverter commit e analisar logs.

### 3. Seeds sem Tradução PT-BR

**Risco**: 10k palavras sem `pt_translation` → UI parece "quebrada".

**Mitigação**:
- MVP: Aceitar vazio, mostrar "Tradução indisponível"
- Fase 2: Script de tradução (API externa)

**Decisão**: Documentar como "dívida técnica" em SPEC.md.

### 4. Performance de Hints

**Risco**: Calcular hints a cada keystroke trava UI.

**Mitigação**:
- Hints calculados no backend (novo endpoint)
- Frontend só exibe, não calcula
- Cache de hints por card

**Validação**: Profiler frontend com 100 cards.

### 5. Áudio Timeout Congela User

**Risco**: Áudio demora 10s+ para carregar, user preso no card.

**Mitigação**:
- Timeout 3s (não aumentar)
- Fallback imediato para próximo card
- Loading indicator visível

**Validação**: Simular delay de áudio no TTS service.

## Status & Timeline

### Status

📋 **Proposed** → Aguardando aprovação

### Timeline Estimada

- **Planejamento (FASE 1)**: 1 dia (este doc)
- **Implementação Backend**: 3-5 dias
  - Migrações
  - Endpoint `/next-lingvist`
  - Grammar tags PT-BR
- **Implementação Frontend**: 5-7 dias
  - Novos componentes
  - Áudio pós-acerto
  - Hints progressivos
- **Testes**: 2-3 dias
  - E2E Playwright
  - Pytest
  - Manual QA
- **Total**: 11-16 dias

### Rollback Plan

Se bugs críticos forem encontrados pós-release:

1. **Opção A**: Remover link para `/train/lingvist` da UI
2. **Opção B**: Reverter commit (git revert)
3. **Opção C**: Hotfix (branch de emergência)

**Decisão**: Baseada em severidade e quantidade de usuários afetados.

---

## Decisões ABERTAS (Aprovar com Escolha)

Por favor, aprove as decisões abaixo:

1. **Mix de cards (80/20)**:
   - [ ] Opção A: Campo `User.preferred_mode` (modo por usuário)
   - [ ] Opção B: Setting global (mesmo mix para todos)

2. **Registrar tentativas**:
   - [ ] Opção A: Estender `ReviewEvent` (recomendado)
   - [ ] Opção B: Nova tabela `Attempt`

3. **API contract**:
   - [ ] Opção A: Novo endpoint `/next-lingvist` (recomendado)
   - [ ] Opção B: Estender `/next-spec4` com campos opcionais

---

## Aprovação

- [ ] Approve proposal
- [ ] Approve decisions above (se aplique)
- [ ] Ready to move to FASE 2 (Apply)

---

**Generated**: 2025-12-24
**Author**: Claude (via user request)
**OpenSpec Version**: 1.0
