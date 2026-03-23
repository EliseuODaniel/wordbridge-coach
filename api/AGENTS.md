# API AGENTS.md

Instruções específicas do backend FastAPI.

## Escopo

Aplica-se a tudo dentro de `api/`.

## Objetivo

- preservar contratos HTTP e comportamento observável antes de simplificar
- preferir extrações pequenas em endpoints e serviços
- manter regras de domínio em serviços e helpers, não espalhadas por handlers

## Áreas sensíveis

- `app/api/api_v1/endpoints/chat.py`
- `app/api/api_v1/endpoints/cards.py`
- `app/services/card_selection.py`
- `app/services/vocabulary_progression.py`
- `app/llm/`

## Regras de mudança

- não paralelize suítes `pytest` que compartilham o mesmo banco de teste
- preserve a trilha já validada de chat utilitário, WebSocket e Spec4
- se mudar setup, testes ou direção arquitetural, atualize `docs/DECISIONS.md`, `docs/ROADMAP.md` ou `docs/TESTING.md`

## Validação padrão

Mudanças localizadas:

```bash
cd api
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest path/to/test_file.py -q
```

Baseline já validado:

```bash
cd api
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_chat_utilities.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/integration/test_chat_websocket_flow.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/integration/test_spec4_card_selection.py -q
```
