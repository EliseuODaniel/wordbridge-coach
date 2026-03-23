# AGENTS.md

Este repositório usa uma governança simples e única.

## Fonte de verdade

Os arquivos oficiais do projeto são:

- `AGENTS.md`: regras de trabalho no repositório
- `README.md`: visão geral e onboarding rápido
- `docs/PROJECT_STATUS.md`: estado real do produto em 2026-03-23
- `docs/ARCHITECTURE.md`: arquitetura atual
- `docs/ROADMAP.md`: prioridades e fases da refatoração
- `docs/DECISIONS.md`: decisões arquiteturais registradas
- `docs/TESTING.md`: estratégia e comandos de teste
- `docs/LOCAL_LLM_SETUP.md`: setup local dos modelos
- `docs/CODEX_SETUP.md`: setup recomendado para Codex, skills e MCPs

Não usamos mais OpenSpec neste projeto. Não crie ou mantenha uma árvore paralela de specs.

## Papel do agente

O agente principal deste repositório é o Codex.

Responsabilidades:

- entender o código antes de editar
- implementar mudanças end to end quando possível
- manter documentação e código alinhados
- preferir mudanças pequenas, testáveis e reversíveis
- registrar decisões que alterem arquitetura, workflow ou setup
- respeitar `AGENTS.md` locais em subpastas quando existirem

## Workflow padrão

1. Ler o contexto mínimo necessário no código e nos docs oficiais.
2. Confirmar a área afetada e as restrições reais.
3. Implementar a mudança.
4. Rodar a validação proporcional ao escopo.
5. Atualizar a documentação oficial se o comportamento, setup ou arquitetura mudou.

## Regras de documentação

- `README.md` deve continuar curto e orientado a onboarding.
- `docs/PROJECT_STATUS.md` descreve o que existe de verdade, não o que gostaríamos que existisse.
- `docs/ROADMAP.md` guarda prioridades ativas e próximos passos.
- `docs/DECISIONS.md` registra decisões importantes com data e impacto.
- Documentos antigos que competem com esses arquivos devem ser removidos ou consolidados.

## Regras de implementação

- Prefira `rg` para localizar arquivos e texto.
- Prefira mudanças pequenas por área.
- Não mantenha comentários apontando para documentação removida.
- Não reintroduza instruções específicas de Claude, OpenSpec ou fluxos paralelos.
- Para trabalho repetitivo, use skills repo-locais em `.agents/skills/`.
- Configurações de MCP devem ser tratadas como setup do ambiente do agente, não como segredo commitado no repositório.

## Regras de validação

- Backend: `pytest` no escopo tocado e, quando relevante, lint/tipos.
- Frontend: `npm run lint` e `npm run build` quando a mudança afetar UI ou tipos.
- E2E: Playwright apenas para fluxos alterados ou regressões críticas.
- Se algum check não puder ser executado, isso deve ser informado no fechamento.

## Refatorações

Para refatorações:

- preservar comportamento observável antes de simplificar
- explicitar invariantes e riscos
- atacar acoplamentos por etapas
- atualizar `docs/ROADMAP.md` e `docs/DECISIONS.md` quando a direção mudar

## Skills repo-locais

As skills em `.agents/skills/` existem para workflows repetitivos. Elas complementam este arquivo; não substituem a documentação oficial.

## Setup Codex

Para preparar o ambiente do agente:

- leia `docs/CODEX_SETUP.md`
- use `AGENTS.md` da raiz e, quando aplicável, os `AGENTS.md` de `api/`, `frontend/`, `tts/` e `tests/e2e/`
- mantenha skills, docs e quality gates coerentes entre si
