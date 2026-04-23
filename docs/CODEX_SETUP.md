# Codex Setup

Data de referência: 2026-03-23

## Objetivo

Este arquivo descreve o setup recomendado para usar Codex neste repositório com governança consistente, skills úteis e documentação alinhada.

## Fonte de verdade

Antes de trabalhar no código, leia:

1. `AGENTS.md`
2. `api/AGENTS.md` ou `frontend/AGENTS.md` quando a mudança estiver nessas áreas
3. `docs/PROJECT_STATUS.md`
4. `docs/ARCHITECTURE.md`
5. `docs/TESTING.md`

## Skills repo-locais

Skills disponíveis no repositório:

- `change-verification`
- `docs-sync`
- `refactor-slice`
- `backend-endpoint-slice`
- `frontend-session-slice`
- `codex-readiness`

Use skills para tarefas repetitivas. Não use skills como substituto de arquitetura ou de documentação oficial.

## MCP recomendado

O repositório não commita configuração local de MCP porque isso pertence ao ambiente do agente.

Setup recomendado para documentação oficial da OpenAI:

```bash
codex mcp add openaiDeveloperDocs --url https://developers.openai.com/mcp
```

Uso recomendado:

- consultar práticas oficiais atuais de Codex, skills, `AGENTS.md` e modelos
- tirar dúvidas sobre APIs e docs oficiais da OpenAI

Se o ambiente usar MCPs adicionais no futuro, documente aqui:

- qual problema resolvem
- como instalar
- em que momento entram no fluxo

## Validação padrão

Frontend:

```bash
./scripts/frontend_tooling.sh check
```

Backend:

```bash
cd api
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest tests/test_vocabulary_progression.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest tests/test_chat_utilities.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest tests/integration/test_chat_websocket_flow.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest tests/integration/test_spec4_card_selection.py -q
```

Compose:

```bash
docker compose config --quiet
```

Compose com áudio local opcional:

```bash
docker compose --profile audio up -d --build
```

Compose com IA local opcional:

```bash
docker compose --profile ai up -d --build
```

## Regras práticas

- prefira mudanças pequenas e verificáveis
- preserve comportamento antes de reorganizar estrutura
- mantenha docs e código alinhados
- use `AGENTS.md` locais quando a mudança entrar em backend, frontend, TTS ou E2E
