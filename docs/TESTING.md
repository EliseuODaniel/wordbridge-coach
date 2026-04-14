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
PYTHONPATH=. .venv/bin/pytest tests/test_chat_conversation_service.py -q
PYTHONPATH=. .venv/bin/pytest tests/test_chat_generation_service.py -q
PYTHONPATH=. .venv/bin/pytest tests/test_chat_draft_state_service.py -q
PYTHONPATH=. .venv/bin/pytest tests/test_chat_handler_service.py -q
PYTHONPATH=. .venv/bin/pytest tests/test_chat_endpoint_adapter_service.py -q
PYTHONPATH=. .venv/bin/pytest tests/test_chat_websocket_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_lingvist_payload_service.py -q
PYTHONPATH=. .venv/bin/pytest tests/test_lingvist_autofill_service.py -q
PYTHONPATH=. .venv/bin/pytest tests/test_card_next_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_card_answer_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_card_progress_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_card_response_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_card_submission_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_card_spec4_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_card_lingvist_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_card_selection_payload_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_card_selection_policy_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_card_selection_query_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_card_selection_fallback_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_card_selection_progress_service.py -q
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

Fluxo suportado local:

```bash
./scripts/frontend_tooling.sh check
```

Comandos isolados:

```bash
./scripts/frontend_tooling.sh install
./scripts/frontend_tooling.sh lint
./scripts/frontend_tooling.sh typecheck
./scripts/frontend_tooling.sh build
```

Uso nativo de `npm` continua valido apenas quando install e execucao ficam no mesmo runtime.

Local alternativo: `frontend/`

```bash
cd frontend
npm run typecheck
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
npm run test:ci
npm run test:smoke
npm run test:headed
npm run test:debug
npm run test:ui
```

Para validar no mesmo contrato Linux/Chromium usado na automação, um caminho reproduzível é:

```bash
docker run --rm --network host \
  -v /home/edann/vscode_projects/filltheword/tests/e2e:/app \
  -w /app node:20-bookworm \
  bash -lc "npm ci && npx playwright install --with-deps chromium && BASE_URL=http://127.0.0.1:3007 npm run test:ci"
```

## Compose local

Para validar integração local:

```bash
docker compose up -d --build
docker compose ps
```

Para validar Chat Coach completo com IA local:

```bash
docker compose --profile ai up -d --build
docker compose --profile ai ps
```

## CI

Existe um baseline inicial de quality gate em `.github/workflows/quality.yml` cobrindo:

- `frontend`: `npm ci`, `npm run lint`, `npm run typecheck`, `npm run build`
- `compose`: `docker compose config --quiet`
- `api`: trilhas críticas já validadas de draft/state/feedback/contexto/adapters/handlers/entrega/texto/rest/conversation/generation/runtime/websocket/orquestração/utilitários de chat, autofill Lingvist, fluxo legado `/cards/next`, WebSocket, progressão e Spec4
- `e2e-chromium`: Playwright Chromium cobrindo a suíte completa de `tests/e2e/tests/*.spec.ts` contra o stack padrão `db/api/frontend`, sem IA local e sem TTS obrigatório

## Regra prática

- mudanças de backend: rode `pytest` no escopo tocado
- mudanças de frontend: rode `./scripts/frontend_tooling.sh check`
- mudanças de fluxo crítico: rode `npm run test:ci` em `tests/e2e/`; use `npm run test:smoke` apenas quando a intenção for um check curto de sanidade
- mudanças amplas: valide também `docker compose`, `alembic upgrade head` e healthchecks
- se `5432` estiver ocupada no host, use `FTW_DB_PORT=55432` para o stack local sem afetar a rede interna do compose
