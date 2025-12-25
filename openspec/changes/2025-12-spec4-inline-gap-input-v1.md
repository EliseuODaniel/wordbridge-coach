# Change: Spec4 Inline Gap Input (Melhoria de UX)

**Date**: 2025-12-25
**Status**: 📝 Proposal
**Version**: v1.0
**Spec Reference**: RF-02 (User Experience)

## Overview

Transformar a experiência do Spec4 de "campo de resposta separado + botão Check" para "lacuna digitável inline" (igual ao Lingvist), mantendo todas as regras de Spec4 (SM-2, feedback, scheduler) sem alterações no backend.

## Business Problem

### Problema Atual (Spec4)
Hoje o Spec4 tem UX inconsistente:
- **Lacuna estática**: "The ___ is on the table." (não é interativa)
- **Campo separado**: Input abaixo da frase + botão "Check"
- **Dois cliques**: Usuário precisa clicar no input E depois clicar em "Check"
- **Incoerente**: Lingvist já tem lacuna digitável inline, Spec4 não

**Resultado**: Usuário confuso, UX mais lenta, não aproveita o padrão já estabelecido no Lingvist.

### Solução Proposta
- **Lacuna digitável inline**: Input direto no lugar do "___"
- **Auto-submit**: Ao digitar a palavra correta, submete automaticamente
- **Enter fallback**: Se apertar Enter, submete mesmo se estiver errado
- **Sem botão "Check"**: Remove completamente o botão de check
- **Reutiliza código**: Usa `InlineGapInput` existente do Lingvist

## Goals

### (A) Lacuna Digitável Inline
**Objetivo**: Input direto na frase, igual ao Lingvist.

**Antes**:
```
┌─────────────────────────────────┐
│ The ___ is on the table.        │  ← lacuna estática
├─────────────────────────────────┤
│ [Digite a resposta aqui    ]    │  ← input separado
│ [✓ Check]                       │  ← botão
└─────────────────────────────────┘
```

**Depois**:
```
┌─────────────────────────────────┐
│ The [           ] is on the table.│  ← input inline
└─────────────────────────────────┘
```

### (B) Auto-Submit no Match Exato
**Objetivo**: Submeter automaticamente quando usuário digitar a palavra correta.

**Lógica**:
- Usuário digita no input inline
- A cada tecla, compara com `correctAnswer` (normalizada: case-insensitive, trim)
- Se bater exatamente:
  - Desabilita input
  - Submete resposta automaticamente
  - Mostra feedback (✅ correto)
  - Avança após delay (como já acontece hoje)

### (C) Enter Submete (Mesmo Errado)
**Objetivo**: Enter é equivalente ao botão "Check" (que será removido).

**Comportamento**:
- Usuário digita (errado ou certo)
- Aperta Enter
- Submete resposta
- Se errou: mostra feedback ❌, permite tentar de novo (não avança)
- Se acertou: feedback ✅, avança após delay

### (D) Erro Não Avança
**Objetivo**: Usuário pode tentar de novo sem forçar próximo card.

**Fluxo de erro**:
1. Usuário digita "dook" (errado)
2. Aperta Enter
3. Feedback aparece: "❌ Incorreto. A resposta correta é: book"
4. Input fica habilitado para nova tentativa
5. Usuário corrige para "book"
6. Auto-submit ou Enter → ✅ avança

### (E) Preservar "Voltar 1 Frase"
**Objetivo**: Botão "← Frase anterior" continua funcionando.

- Nenhuma alteração no `PreviousCardReplayModal`
- Botão no header permanece
- Funciona igualzinho hoje (PR #6)

## Non-Goals

- ❌ Modificar backend/SMS/scheduler
- ❌ Alterar modo Lingvist (já está certo)
- ❌ Modificar "Voltar 1 Frase" (PR #6)
- ❌ Adicionar botão "Check" (remover completamente)
- ❌ Mudar regras de validação (SM-2, normalize, etc.)
- ❌ Modificar lógica de feedback ou next review

## UX Specifications

### Comportamento do Input Inline

**Estados**:
1. **Inicial**: Vazio, habilitado, focado automaticamente
2. **Digitando**: Usuário digita, nada acontece ainda
3. **Match Exato**: Se `userInput === correctAnswer` (normalizado):
   - Auto-submete
   - Input desabilita
   - Feedback ✅ aparece
4. **Enter**: Submete manualmente:
   - Se correto: ✅ avança
   - Se errado: ❌ mostra feedback, input habilita para correção

**Exemplo Visual**:

```
Estado 1: Inicial
┌──────────────────────────────────────┐
│ The [                   ] is here.   │  ← cursor piscando
└──────────────────────────────────────┘

Estado 2: Digitando "bo"
┌──────────────────────────────────────┐
│ The [bo                 ] is here.   │
└──────────────────────────────────────┘

Estado 3: Match exato "book" → Auto-submit!
┌──────────────────────────────────────┐
│ The [book               ] is here.   │  ← desabilitado
└──────────────────────────────────────┘
     ✅ Correto! Next review: 2025-12-26
     [aguardando delay para próximo card...]
```

### Validação de Resposta

**Normalização** (igual ao backend):
```typescript
const normalize = (text: string) =>
  text.toLowerCase().trim().replace(/\s+/g, ' ');

if (normalize(userInput) === normalize(correctAnswer)) {
  // Auto-submit
}
```

**Feedback**:
- ✅ Correto: Verde, mostra "next review at", avança após delay
- ❌ Incorreto: Vermelho, mostra resposta correta, **não avança**

### Acessibilidade

**data-testid**: `[data-testid="gap-input"]` no `<input>` dentro de `InlineGapInput`

**Instruções atualizadas**:
- Remover: "Press Enter to submit answer"
- Adicionar: "Digite na lacuna e pressione Enter para conferir"

## Acceptance Criteria

### Funcional
- [ ] Spec4 mostra input inline na frase (não mais campo separado)
- [ ] Nenhum botão "Check" existe no Spec4
- [ ] Digitar palavra correta → auto-submit
- [ ] Apertar Enter → submete (mesmo se errado)
- [ ] Errar → feedback aparece, permite tentar de novo
- [ ] Acertar → feedback ✅, avança após delay
- [ ] Botão "← Frase anterior" permanece e funciona

### Técnico
- [ ] Reutiliza `InlineGapInput` do Lingvist
- [ ] `CardDisplay` aceita prop opcional `sentenceNode?`
- [ ] `study-session.spec.ts` atualizado para novo seletor
- [ ] `data-testid="gap-input"` presente no input
- [ ] Nenhuma mudança em backend/API
- [ ] Testes E2E passam

### Não-Regressão
- [ ] Lingvist continua funcionando igual
- [ ] "Voltar 1 Frase" funciona (PR #6)
- [ ] SM-2 scheduler inalterado
- [ ] Áudio funciona
- [ ] Spec4 selection algorithm inalterado

## Implementation Plan

### FASE 1: Proposal (Esta fase)
- [x] Criar documento OpenSpec
- [ ] Aprovar proposta

### FASE 2: Apply (Frontend Only)

#### 2.1 Modificar CardDisplay.tsx
**Arquivo**: `frontend/src/components/CardDisplay.tsx`

**Mudança**: Adicionar prop opcional `sentenceNode?: React.ReactNode`

```typescript
interface CardDisplayProps {
  // ... props existentes
  sentenceNode?: React.ReactNode;  // ← Novo
}
```

**Lógica de renderização**:
```tsx
// Se sentenceNode fornecido, renderiza no lugar da lacuna estática
{sentenceNode ? (
  <div className="text-xl font-medium text-gray-900 dark:text-white leading-relaxed">
    {sentenceNode}
  </div>
) : (
  // Comportamento atual: lacuna estática
  <div className="text-xl font-medium ...">
    {renderSentenceWithGap()}  // função existente
  </div>
)}
```

#### 2.2 Modificar InlineGapInput.tsx
**Arquivo**: `frontend/src/components/InlineGapInput.tsx`

**Mudanças**:
1. Adicionar `data-testid="gap-input"` ao `<input>`
2. Aceitar prop `correctAnswer?: string` (já existe no Lingvist, só garantir)
3. Aceitar prop `isCorrect?: boolean` e `isIncorrect?: boolean` para feedback visual

```tsx
<input
  data-testid="gap-input"  // ← Adicionar
  type="text"
  value={value}
  onChange={handleChange}
  onKeyDown={handleKeyDown}
  disabled={disabled}
  className={`
    // ... classes existentes
    ${isCorrect ? 'bg-green-50 dark:bg-green-900/20' : ''}
    ${isIncorrect ? 'bg-red-50 dark:bg-red-900/20' : ''}
  `}
/>
```

#### 2.3 Modificar StudySession.tsx
**Arquivo**: `frontend/src/components/StudySession.tsx`

**Mudanças**:

**A) Remover AnswerInput**:
```tsx
// REMOVER:
import AnswerInput from './AnswerInput';

// REMOVER do JSX:
<AnswerInput
  onSubmit={handleSubmit}
  isSubmitting={isSubmitting}
  feedback={feedback ? {
    correct: feedback.correct,
    correctAnswer: feedback.correct_answer
  } : null}
  cardId={currentCard?.card_id}
/>
```

**B) Adicionar InlineGapInput**:
```tsx
import InlineGapInput from './InlineGapInput';

// Dentro do JSX, onde está <CardDisplay>:
<CardDisplay
  card={currentCard}
  sentenceNode={  // ← Novo prop
    <InlineGapInput
      correctAnswer={currentCard.word}  // Spec4 tem 'word' no CardResponse
      onSubmit={handleSubmit}
      disabled={isSubmitting || feedback?.correct === true}
      isCorrect={feedback?.correct === true}
      isIncorrect={feedback?.correct === false}
      onUserEdit={() => setFeedback(null)}  // Limpa feedback ao editar
      autoFocus={true}
    />
  }
  onPlayWordAudio={handlePlayWordAudio}
  onPlaySentenceAudio={handlePlaySentenceAudio}
  loadingAudio={loadingAudio}
/>
```

**C) Atualizar texto de ajuda**:
```tsx
// REMOVER (ou alterar):
<p>Press <kbd>Enter</kbd> to submit answer</p>

// ADICIONAR:
<p>Digite na lacuna e pressione <kbd>Enter</kbd> para conferir</p>
```

#### 2.4 Atualizar Testes E2E
**Arquivo**: `tests/e2e/tests/study-session.spec.ts`

**Mudanças**:

**A) Alterar seletores**:
```typescript
// ANTIGO:
await page.locator('[data-testid="answer-input"]').fill('test');
await page.locator('[data-testid="answer-submit"]').click();

// NOVO:
await page.locator('[data-testid="gap-input"]').fill('test');
await page.locator('[data-testid="gap-input"]').press('Enter');
```

**B) Adicionar assert: não existe botão Check**:
```typescript
test('não tem botão Check no Spec4', async ({ page }) => {
  await page.waitForTimeout(2000);

  const hasCards = await page.locator('[data-testid="study-card"]').isVisible().catch(() => false);
  if (!hasCards) {
    test.skip(true, 'No cards available');
    return;
  }

  // Verificar que NÃO existe botão "Check"
  const checkButton = page.getByText('Check');
  await expect(checkButton).not.toBeVisible();
  await expect(checkButton).toHaveCount(0);
});
```

**C) Testar auto-submit**:
```typescript
test('auto-submit ao digitar palavra correta', async ({ page }) => {
  await page.waitForTimeout(2000);

  const hasCards = await page.locator('[data-testid="study-card"]').isVisible().catch(() => false);
  if (!hasCards) {
    test.skip(true, 'No cards available');
    return;
  }

  // Pegar a palavra correta da frase (extrair do contexto)
  const sentenceElement = page.locator('[data-testid="study-card"]');
  const sentenceText = await sentenceElement.textContent();

  // Preencher com palavra correta (simulação)
  await page.locator('[data-testid="gap-input"]').fill('book');

  // Esperar auto-submit (feedback aparece)
  await page.waitForTimeout(1000);

  // Verificar que feedback correto apareceu
  const feedback = page.locator('text=Correto');
  await expect(feedback).toBeVisible();
});
```

### FASE 3: Validate

#### 3.1 Build
```bash
cd frontend
npm run build
```

#### 3.2 E2E Tests
```bash
cd tests/e2e
npm run test
```

Focar em:
- `study-session.spec.ts` → Spec4
- `replay-previous-card.spec.ts` → "Voltar 1 Frase"
- `lingvist-session.spec.ts` → Lingvist (não deve quebrar)

#### 3.3 Smoke Manual
**Cenário 1: Erro + Correção**
1. Abrir Spec4
2. Digitar errado: "dook"
3. Apertar Enter
4. ✅ Feedback ❌ aparece
5. ✅ Input continua habilitado
6. Corrigir: "book"
7. ✅ Auto-submit ou Enter → ✅ avança

**Cenário 2: Acerto Direto**
1. Abrir Spec4
2. Digitar correto: "book"
3. ✅ Auto-submit (sem apertar Enter)
4. ✅ Feedback ✅ aparece
5. ✅ Avança após delay

**Cenário 3: Voltar 1 Frase**
1. Avançar para 2º card
2. Clicar "← Frase anterior"
3. ✅ Modal abre
4. ✅ Nenhum POST /answer no DevTools Network
5. Fechar modal
6. ✅ De volta ao card atual

**Cenário 4: Não Existe Check**
1. Abrir Spec4
2. Procurar botão com texto "Check"
3. ✅ Não encontrado

### FASE 4: PR

#### 4.1 Conteúdo
- OpenSpec proposal
- `frontend/src/components/CardDisplay.tsx` (modificado)
- `frontend/src/components/InlineGapInput.tsx` (modificado)
- `frontend/src/components/StudySession.tsx` (modificado)
- `tests/e2e/tests/study-session.spec.ts` (modificado)

#### 4.2 Checklist no PR
- [ ] Nenhuma mudança no backend
- [ ] Lingvist não foi modificado
- [ ] "Voltar 1 Frase" continua funcionando
- [ ] Testes E2E passam
- [ ] Build sem erros
- [ ] Manual smoke test realizado

## Technical Details

### Diferenças Spec4 vs Lingvist

| Característica | Spec4 | Lingvist |
|----------------|-------|----------|
| `correctAnswer` | `card.word` (string) | `card.correct_answer` (string) |
| Auto-submit | Sim (match exato) | Sim (match exato) |
| Enter fallback | Sim (submete errado) | Sim (submete errado) |
| Erro avança? | Não | Não |
| Hint system | Não (apenas grammar_hint do card) | Sim (progressivo 0-5) |

**Conclusão**: `InlineGapInput` já suporta tudo que precisamos!

### Fluxo de Dados

```
StudySession.tsx
  ↓
CardDisplay(sentenceNode={<InlineGapInput .../>})
  ↓
InlineGapInput(correctAnswer={currentCard.word})
  ↓
onChange → compara com correctAnswer (normalizada)
  ↓
Se match → onSubmit() → handleSubmit() → POST /answer
  ↓
Feedback → isCorrect={true} → Input desabilita (verde)
```

### Estado do Feedback

**Como limpar feedback quando usuário editar após erro**:
```typescript
<InlineGapInput
  onUserEdit={() => setFeedback(null)}  // Limpa feedback ao digitar
  // ...
/>
```

**No InlineGapInput**:
```typescript
const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
  setValue(e.target.value);
  if (onUserEdit) {
    onUserEdit();  // ← Notifica StudySession para limpar feedback
  }

  // Auto-submit logic
  if (isMatch(normalize(e.target.value), normalize(correctAnswer))) {
    onSubmit(e.target.value);
  }
};
```

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Quebrar Lingvist | Alto | Não modificar `LingvistSession.tsx`; apenas reutilizar componente |
| Quebrar "Voltar 1 Frase" | Médio | Não modificar `PreviousCardReplayModal`; testar após implementação |
| Auto-submit indesejado | Médio | Apenas no match **exato** (normalizado); Enter sempre funciona |
| Testes E2E quebram | Baixo | Atualizar seletores; garantir que specs novos passem |
| Usuário confuso sem botão Check | Baixo | Instrução clara: "Digite na lacuna e pressione Enter" |

## Timeline Estimate

- FASE 1 (Proposal): 30 min
- FASE 2 (Apply): 2-3 horas
  - CardDisplay: 30 min
  - InlineGapInput: 30 min
  - StudySession: 1h
  - Testes E2E: 30 min
- FASE 3 (Validate): 30 min
- FASE 4 (PR): 30 min
- **Total**: 3.5 - 4.5 horas

## References

- InlineGapInput: `frontend/src/components/InlineGapInput.tsx`
- StudySession: `frontend/src/components/StudySession.tsx`
- CardDisplay: `frontend/src/components/CardDisplay.tsx`
- LingvistSession: `frontend/src/components/LingvistSession.tsx` (referência de uso)
- Testes E2E: `tests/e2e/tests/study-session.spec.ts`
- SM-2 Algorithm: backend/app/services/sm2_algorithm.py (não modificar)
