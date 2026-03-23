# Testing

## Objetivo

Este arquivo registra o baseline de validação do projeto após a limpeza de governança.

## Backend

Local: `api/`

Comandos úteis:

```bash
cd api
TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test ./test-runner.sh --all
```

Quando a mudança for localizada:

```bash
cd api
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest path/to/test_file.py -q
```

Exemplos já validados:

```bash
cd api
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_vocabulary_progression.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_chat_draft_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_chat_feedback_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_chat_context_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_chat_delivery_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_chat_text_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_chat_rest_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_lingvist_payload_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_card_answer_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_card_progress_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_card_response_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_card_submission_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_card_spec4_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_card_lingvist_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_card_selection_payload_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_chat_runtime_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_chat_turn_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/integration/test_spec4_card_selection.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/integration/test_chat_websocket_flow.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/integration/test_themes_stats.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_chat_utilities.py -q
```

Notas:

- o runner prefere automaticamente `api/.venv` quando ele existir
- para testes locais no host, suba o banco com `docker compose --profile test up -d db_test`
- `api/tests/conftest.py` aceita override por `TEST_DATABASE_URL`
- suites que compartilham o mesmo banco de teste devem rodar em serie; evitar paralelizar `pytest` nesse grupo

## Frontend

Local: `frontend/`

Comandos úteis:

```bash
cd frontend
npm run lint
npm run build
```

## E2E

Local: `tests/e2e/`

Comandos úteis:

```bash
cd tests/e2e
npm test
```

Variações:

```bash
npm run test:headed
npm run test:debug
npm run test:ui
```

## Compose local

Para validar integração local:

```bash
docker compose up -d --build
docker compose ps
```

## CI

Existe um baseline inicial de quality gate em `.github/workflows/quality.yml` cobrindo:

- `frontend`: `npm ci`, `npm run lint`, `npm run build`
- `api`: trilhas críticas já validadas de draft/feedback/contexto/entrega/texto/rest/runtime/orquestração/utilitários de chat, WebSocket, progressão e Spec4

## Regra prática

- mudanças de backend: rode `pytest` no escopo tocado
- mudanças de frontend: rode `npm run lint` e `npm run build`
- mudanças de fluxo crítico: considere Playwright
- mudanças amplas: valide também `docker compose` e healthchecks
