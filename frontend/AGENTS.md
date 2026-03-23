# Frontend AGENTS.md

Instruções específicas do frontend React.

## Escopo

Aplica-se a tudo dentro de `frontend/`.

## Objetivo

- preservar comportamento visual e fluxo principal antes de reorganizar componentes
- reduzir coordenação local repetida em sessões grandes
- centralizar mudança de modo e navegação no shell do app quando possível

## Áreas sensíveis

- `src/App.tsx`
- `src/components/StudySession.tsx`
- `src/components/LingvistSession.tsx`
- `src/components/ChatCoachSession.tsx`
- `src/components/UserSelection.tsx`
- `src/services/api.ts`
- `src/services/chatWs.ts`

## Regras de mudança

- prefira helpers locais antes de criar abstrações globais
- preserve contratos de props e comportamento observável
- se mudar fluxo de sessão, valide `lint` e `build`
- se mudar setup ou arquitetura, sincronize `docs/PROJECT_STATUS.md`, `docs/ROADMAP.md` e `docs/DECISIONS.md`

## Validação padrão

```bash
cd frontend
npm run lint
npm run build
```
