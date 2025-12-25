# Change: Replay Previous Card (Voltar 1 Frase)

**Date**: 2025-12-25
**Status**: 📝 Proposal
**Version**: v1.0
**Spec Reference**: RF-01 (User Experience)

## Overview

Adicionar funcionalidade de "voltar 1 frase" que permite ao usuário revisualizar e ouvir o card anterior durante as sessões de treino (Spec4 e Lingvist). É um **replay apenas** - não permite responder novamente nem altera o progresso/SRS.

## Business Problem

### Problema Atual
Durante as sessões de treino, usuários às vezes:
- **Esquecem o áudio da frase anterior** assim que avançam
- **Querem revisitar uma citação interessante** que acabaram de ver
- **Precisam ouvir novamente** a pronúncia de uma palavra específica do card anterior

Hoje, para ver/ouvir o card anterior, o usuário teria que:
- Terminar a sessão e procurar no histórico (UX ruim)
- Ou avançar vários cards e perder o contexto

**Solução**: Botão "← Frase anterior" que abre um modal/drawer com os dados do card imediatamente anterior, permitindo ouvir áudio sem impactar o fluxo.

## Goals

### (A) Botão de Replay Visível
**Objetivo**: Adicionar botão "← Frase anterior" que fica desabilitado até existir histórico.

**Implementação**:
- Botão no header ou próximo aos botões de áudio (decisão de UX no componente)
- Inicialmente desabilitado (`disabled`)
- Habilita após o usuário avançar para o 2º card da sessão

### (B) Modal/Drawer de Replay
**Objetivo**: Mostrar conteúdo do card anterior sem permitir responder.

**Conteúdo do modal**:
1. **Frase com lacuna** (ex: "The ___ was here.") - `sentenceWithGap`
2. **Resposta** em linha separada (ex: "Resposta: word") - `answer`
3. **Source** (se existir) - `source`
4. **Tradução** (se existir) - `translation`
5. **Botões de áudio**:
   - "Play Word" - toca áudio da palavra
   - "Play Sentence" - toca áudio da frase completa
6. **Botão de fechar**: "Voltar para o card atual"

**Opcional recomendado**: Auto-play da frase completa ao abrir o modal (é gesto explícito do usuário, não bloqueia nada).

### (C) Não Alterar Fluxo Principal
**Regra de Ouro**: Replay é **somente visualização**.

**O que NÃO acontece**:
- ❌ Nenhuma chamada `POST /answer` ao usar replay
- ❌ Nenhuma alteração no scheduler
- ❌ Nenhum `ReviewEvent` criado
- ❌ Nenhuma mudança em stats/progress

**O que acontece**:
- ✅ Modal abre com dados do card anterior
- ✅ Usuário pode tocar áudio (via `audioService.playFromUrl()`)
- ✅ Fechar modal volta ao card atual (sem refetch)

### (D) Escopo dos Modos
**Objetivo**: Funciona em ambos os modos de treino.

**Modos suportados**:
1. **Treino Clássico (Spec4)** - `StudySession.tsx`
2. **Treino Lacunas (Lingvist)** - `LingvistSession.tsx`

**Diferenças por modo**:
- Spec4: `answer = card.word` (resposta correta)
- Lingvist: `answer = card.correct_answer`

## Non-Goals

- ❌ Histórico longo (navegar 10, 20 cards atrás)
- ❌ Persistir histórico no backend
- ❌ Permitir responder novamente ao card anterior
- ❌ Editar ou modificar o card anterior
- ❌ Implementar navegação completa "próximo/anterior"
- ❌ Modificar backend/SRS/scheduler

## Success Criteria

### Funcional
- [ ] Botão "← Frase anterior" aparece desabilitado no 1º card
- [ ] Após avançar para o 2º card, botão fica habilitado
- [ ] Ao clicar, modal abre com dados do card anterior:
  - [ ] Mostra frase com lacuna (ex: "The ___ was here.")
  - [ ] Mostra linha "Resposta: <word>"
  - [ ] Mostra source (se existir)
  - [ ] Mostra tradução (se existir)
  - [ ] Botões "Play Word" e "Play Sentence" funcionam
- [ ] Fechar modal volta exatamente para o card atual (sem refetch)

### Técnico
- [ ] Nenhuma chamada `POST /answer` é feita ao usar replay
- [ ] Scheduler não é alterado
- [ ] Nenhum `ReviewEvent` é criado
- [ ] Modal usa `audioService.playFromUrl()` para áudio
- [ ] State do card anterior é mantido no frontend apenas (sem backend)

### Testes
- [ ] Teste E2E Playwright:
  1. Entra no modo (Spec4 ou Lingvist)
  2. Responde 1 card corretamente para avançar
  3. Verifica que botão "Frase anterior" está habilitado
  4. Clica no botão e verifica que modal abriu
  5. Verifica que modal mostra texto da frase ou "Source:"
  6. Fecha modal e verifica que está no card atual
  7. Network tab confirma: nenhum POST /answer durante replay

## Plano de Implementação

### FASE 1: Proposal (Esta fase)
- [x] Criar documento OpenSpec
- [ ] Aprovar proposta

### FASE 2: Apply (Frontend Only)

#### 2.1 Criar Componente Modal Reutilizável
**Arquivo**: `frontend/src/components/PreviousCardReplayModal.tsx`

**Props**:
```typescript
interface PreviousCardReplayModalProps {
  open: boolean;
  onClose: () => void;
  title: string | null;          // sentenceWithGap
  answer: string | null;         // word ou correct_answer
  translation: string | null;
  source: string | null;
  audioWordUrl: string | null;
  audioSentenceUrl: string | null;
  autoPlay?: boolean;            // Opcional: auto-play ao abrir
}
```

**Funcionalidades**:
- Renderizar frase com lacuna
- Mostrar linha "Resposta: <answer>"
- Mostrar source/translation se existirem
- Botões "Play Word" e "Play Sentence" usando `audioService.playFromUrl()`
- Opcionalmente tocar automaticamente `audioSentenceUrl` ao abrir

#### 2.2 Modificar StudySession.tsx (Spec4)
**Arquivo**: `frontend/src/components/StudySession.tsx`

**Mudanças**:
1. Adicionar state:
   ```typescript
   const [previousCard, setPreviousCard] = useState<CardResponse | null>(null);
   const previousCardRef = useRef<CardResponse | null>(null);
   ```

2. Quando novo card carrega com sucesso:
   ```typescript
   // Antes de atualizar currentCard
   if (currentCard) {
     previousCardRef.current = currentCard;
     setPreviousCard(currentCard);
   }
   ```

3. Adicionar botão "← Frase anterior" no JSX (desabilitado se `!previousCard`)

4. Integrar modal:
   ```tsx
   <PreviousCardReplayModal
     open={showPreviousCardModal}
     onClose={() => setShowPreviousCardModal(false)}
     title={previousCard?.text || null}
     answer={previousCard?.word || null}
     translation={previousCard?.translation || null}
     source={previousCard?.source || null}
     audioWordUrl={previousCard?.audio_word_url || null}
     audioSentenceUrl={previousCard?.audio_sentence_url || null}
     autoPlay={true}
   />
   ```

**Type check**: Verificar se `CardResponse` tem campo `word`. Se não, adicionar em `frontend/src/services/api.ts`:
```typescript
export interface CardResponse {
  id: string;
  text: string;
  word: string;  // <-- Adicionar
  translation?: string;
  source?: string;
  audio_word_url?: string;
  audio_sentence_url?: string;
  // ... outros campos
}
```

#### 2.3 Modificar LingvistSession.tsx
**Arquivo**: `frontend/src/components/LingvistSession.tsx`

**Mudanças** análogas ao Spec4:
1. Adicionar `previousCard: LingvistCardResponse | null`
2. Atualizar quando novo card carrega
3. Botão "← Frase anterior"
4. Modal com `answer={previousCard?.correct_answer}`

**Type check**: Verificar se `LingvistCardResponse` tem `correct_answer`.

#### 2.4 Testes E2E
**Arquivo**: `tests/e2e/tests/replay-previous-card.spec.ts` (novo)

**Cenário de teste**:
```typescript
test('replay previous card - Spec4', async ({ page }) => {
  // 1. Login e navegar até Spec4
  // 2. Responder 1 card corretamente
  // 3. Verificar botão "Frase anterior" habilitado
  // 4. Clicar e verificar modal aberto
  // 5. Verificar conteúdo do modal
  // 6. Fechar e voltar ao card atual
  // 7. Network: verificar nenhum POST /answer
});
```

### FASE 3: Validate

#### 3.1 Build + Sanity
```bash
cd frontend
npm run build
npm run test:e2e  # Apenas smoke tests
```

#### 3.2 Validação Manual
- [ ] Abrir DevTools Network
- [ ] Iniciar sessão Spec4
- [ ] Avançar para 2º card
- [ ] Clicar "Frase anterior"
- [ ] Verificar modal abriu
- [ ] Verificar NENHUM request POST /answer aparece
- [ ] Tocar áudio - funciona
- [ ] Fechar modal - volta ao card atual

### FASE 4: PR

#### 4.1 Conteúdo do PR
- OpenSpec proposal document
- `frontend/src/components/PreviousCardReplayModal.tsx` (novo)
- `frontend/src/components/StudySession.tsx` (modificado)
- `frontend/src/components/LingvistSession.tsx` (modificado)
- `frontend/src/services/api.ts` (se necessário adicionar `word`)
- `tests/e2e/tests/replay-previous-card.spec.ts` (novo)

#### 4.2 Descrição do PR
- Sumário: "feat: add replay previous card modal (Spec4 + Lingvist)"
- Implementação: componente modal reutilizável
- Validação: teste E2E + validação manual de Network
- Screenshots: do modal aberto em ambos os modos

## Technical Details

### Estado Frontend-Only
**Histórico de cards**: mantido apenas no componente (state + ref)
- `useState` para trigger re-render quando botão habilita
- `useRef` para evitar "stale state" em closures

**Nenhuma mudança no backend**:
- Sem novos endpoints
- Sem modificações em SRS/scheduler
- Sem persistência de histórico

### Audio Service
Usar `audioService.playFromUrl()` já existente:
```typescript
import { audioService } from '../services/audio';

// Play word
audioService.playFromUrl(audioWordUrl);

// Play sentence
audioService.playFromUrl(audioSentenceUrl);
```

### Opcional: Auto-play
Se implementar `autoPlay={true}`:
```typescript
useEffect(() => {
  if (open && autoPlay && audioSentenceUrl) {
    audioService.playFromUrl(audioSentenceUrl);
  }
}, [open, autoPlay, audioSentenceUrl]);
```

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Modal confunde usuário ("posso responder de novo?") | Usuário tenta responder card anterior | Título claro: "Frase Anterior (Apenas Visualização)" + sem input/botão de submit |
| Audio service falha no modal | Áudio não toca | Tratamento de erro existente no service |
| State fica desincronizado | Mostra card errado | Usar `useRef` + `useState` juntos; atualizar apenas quando card novo carrega com sucesso |
| Type errors em CardResponse | Build quebra | Verificar/types no início; adicionar `word?: string` se necessário |

## Timeline Estimate

- FASE 1 (Proposal): 30 min
- FASE 2 (Apply): 2-3 horas
  - Componente modal: 1h
  - StudySession: 45min
  - LingvistSession: 45min
  - Teste E2E: 30min
- FASE 3 (Validate): 30 min
- FASE 4 (PR): 30 min
- **Total**: 3.5 - 4.5 horas

## References

- StudySession component: `frontend/src/components/StudySession.tsx`
- LingvistSession component: `frontend/src/components/LingvistSession.tsx`
- Audio service: `frontend/src/services/audio.ts`
- API types: `frontend/src/services/api.ts`
- Testes E2E existentes: `tests/e2e/tests/`
