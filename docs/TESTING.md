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
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest path/to/test_file.py -q
```

Exemplos já validados:

```bash
cd api
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest tests/test_vocabulary_progression.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest tests/test_chat_draft_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest tests/test_chat_feedback_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest tests/test_chat_context_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest tests/test_chat_delivery_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest tests/test_chat_text_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest tests/test_chat_rest_service.py -q
PYTHONPATH=. .venv/bin/python -m pytest tests/test_chat_conversation_service.py -q
PYTHONPATH=. .venv/bin/python -m pytest tests/test_chat_generation_service.py -q
PYTHONPATH=. .venv/bin/python -m pytest tests/test_chat_draft_state_service.py -q
PYTHONPATH=. .venv/bin/python -m pytest tests/test_chat_handler_service.py -q
PYTHONPATH=. .venv/bin/python -m pytest tests/test_chat_endpoint_adapter_service.py -q
PYTHONPATH=. .venv/bin/python -m pytest tests/test_chat_websocket_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest tests/test_lingvist_payload_service.py -q
PYTHONPATH=. .venv/bin/python -m pytest tests/test_lingvist_autofill_service.py -q
PYTHONPATH=. .venv/bin/python -m pytest tests/test_card_next_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest tests/test_card_answer_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest tests/test_card_progress_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest tests/test_card_response_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest tests/test_card_submission_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest tests/test_card_spec4_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest tests/test_card_lingvist_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest tests/test_card_selection_payload_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest tests/test_card_selection_policy_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest tests/test_card_selection_query_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest tests/test_card_selection_fallback_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest tests/test_card_selection_progress_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest tests/test_chat_runtime_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest tests/test_chat_turn_service.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest tests/test_pedagogical_prompt_snapshots.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest -s -q tests/test_chat_feedback_service.py tests/test_chat_delivery_service.py tests/test_chat_text_service.py tests/test_chat_generation_service.py tests/test_llamacpp_provider_sse.py tests/test_lingvist_difficulty_service.py tests/integration/test_chat_websocket_flow.py
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest -s -q tests/test_chat_profile_service.py tests/test_chat_conversation_service.py tests/test_chat_feedback_service.py tests/test_chat_delivery_service.py tests/test_chat_text_service.py tests/test_chat_generation_service.py tests/test_chat_context_service.py tests/test_llamacpp_provider_sse.py tests/test_chat_coach_mock_provider.py tests/test_lingvist_difficulty_service.py tests/integration/test_chat_websocket_flow.py
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest -s -q tests/test_chat_profile_service.py tests/test_chat_conversation_service.py tests/test_chat_context_service.py tests/test_chat_text_service.py tests/test_chat_generation_service.py tests/test_chat_delivery_service.py tests/test_chat_endpoint_adapter_service.py tests/test_chat_turn_service.py tests/test_chat_utilities.py tests/integration/test_chat_websocket_flow.py
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest -s -q tests/test_chat_profile_service.py tests/test_chat_conversation_service.py tests/test_chat_delivery_service.py tests/test_chat_endpoint_adapter_service.py tests/test_chat_utilities.py tests/test_lingvist_payload_service.py tests/test_card_lingvist_service.py tests/test_card_spec4_service.py tests/integration/test_chat_websocket_flow.py tests/integration/test_spec4_card_selection.py
TMPDIR=/home/edann/projects/wordbridge-coach/.tmp_pytest PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest -s -q tests/test_chat_profile_service.py tests/test_chat_text_service.py tests/test_lingvist_difficulty_service.py tests/test_card_spec4_service.py tests/test_lingvist_payload_service.py tests/integration/test_chat_websocket_flow.py
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest -s -q tests/integration/test_chat_websocket_flow.py
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest tests/integration/test_spec4_card_selection.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest tests/integration/test_chat_websocket_flow.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest tests/integration/test_themes_stats.py -q
PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest tests/test_chat_utilities.py -q
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

Quando for necessário rodar o Vite manualmente, o proxy de desenvolvimento fica em `frontend/viteProxy.ts` e usa:

- `WORDBRIDGE_API_PROXY_TARGET`, default `http://localhost:8000`
- `WORDBRIDGE_TTS_PROXY_TARGET`, default `http://localhost:8001`

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
PATH="$HOME/.local/bin:$PATH" CI=1 BASE_URL=http://127.0.0.1:3007 npx playwright test tests/study-session.spec.ts tests/lingvist-session.spec.ts --project=chromium
PATH="$HOME/.local/bin:$PATH" CI=1 BASE_URL=http://127.0.0.1:3007 npx playwright test tests/chat-coach.spec.ts tests/mode-switch.spec.ts --project=chromium
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
  -v /home/edann/projects/wordbridge-coach/tests/e2e:/app \
  -w /app node:20-bookworm \
  bash -lc "npm ci && npx playwright install --with-deps chromium && BASE_URL=http://127.0.0.1:3007 npm run test:ci"
```

Status da rodada 2026-04-21:

- os specs focais de `tests/e2e/tests/study-session.spec.ts` e `tests/e2e/tests/lingvist-session.spec.ts` foram atualizados para o novo `learning-context-panel` e para o seletor estável `lingvist-inline-input`
- a execução local desses specs foi concluída nesta thread com `Node v20.20.2` Linux no PATH local, stack `api/frontend` rebuildada e resultado `14 passed (53.1s)`

Status da rodada 2026-05-05:

- `tests/e2e/tests/chat-coach.spec.ts` cobre abertura do Chat Coach por `?mode=chat` e por card de perfil existente
- `tests/e2e/tests/mode-switch.spec.ts` cobre a troca Spec4 -> Lingvist -> Spec4 dentro do shell React, sem reload manual de página

## Compose local

Para validar integração local:

```bash
./scripts/smoke_local.sh
```

Esse é o smoke recomendado para o stack padrão. Ele usa `wordbridge-smoke` como projeto Compose temporário, sobe `db/api/frontend`, aplica migrations, roda seed, valida `/health`, valida o frontend, cria um perfil via API e carrega o primeiro card Spec4. Por padrão ele usa portas e subnet próprios (`55433`, `18000`, `13007`, `172.29.0.0/16`) para poder rodar mesmo quando a stack principal está ativa em `55432`, `8000` e `3007`.

Fluxo manual equivalente:

```bash
WORDBRIDGE_DB_PORT=55432 docker compose up -d --build db api frontend
docker compose exec -T api alembic upgrade head
docker compose exec -T api python scripts/seed_data.py
curl -fsS http://localhost:8000/health
curl -fsS http://localhost:3007 >/dev/null
WORDBRIDGE_DB_PORT=55432 docker compose down --remove-orphans
```

Portas e subnet do compose podem ser sobrescritos por:

- `WORDBRIDGE_DB_PORT`
- `WORDBRIDGE_API_PORT`
- `WORDBRIDGE_FRONTEND_PORT`
- `WORDBRIDGE_DOCKER_SUBNET`
- `WORDBRIDGE_TTS_PORT`
- `WORDBRIDGE_LLM_PORT`
- `WORDBRIDGE_LLM_CHAT_PORT`
- `WORDBRIDGE_LLM_TEACHER_PORT`
- `WORDBRIDGE_LANGUAGETOOL_PORT`

Para validar Chat Coach completo com IA local:

```bash
docker compose --profile ai config --quiet
docker compose --profile ai up -d --build
docker compose --profile ai ps
```

O perfil `ai` exige modelos GGUF em `llm_models/`, GPU NVIDIA/CUDA para os serviços `llama.cpp` configurados e portas livres para `8080`, `8081`, `8082` e `8010`. Se uma dessas precondições não estiver disponível, registre a limitação e valide pelo menos `docker compose --profile ai config --quiet`. Na estação usada em 2026-05-05, a porta `8080` estava ocupada por outro projeto, então o runtime completo do perfil não foi iniciado.
Quando as portas padrão estiverem ocupadas, use `WORDBRIDGE_LLM_PORT`, `WORDBRIDGE_LLM_CHAT_PORT`, `WORDBRIDGE_LLM_TEACHER_PORT` e `WORDBRIDGE_LANGUAGETOOL_PORT` para validar os serviços em portas alternativas. Na estação usada em 2026-05-05, LanguageTool validou em `18110`; o LLM completo não foi iniciado porque havia apenas cerca de 3.3 GB de VRAM livre com outro LLM ativo.

Para validar áudio local, o perfil `audio` usa Piper TTS e mantém modelos no volume `tts_models`:

```bash
docker compose --profile audio build tts
docker compose --profile audio up -d tts
docker run --rm wordbridge-coach-tts piper --help >/dev/null
```

O perfil `audio` publica `8001`; quando a porta já estiver ocupada por outro serviço local, prefira validar build/import/CLI da imagem e registrar a limitação antes de subir o serviço. Na estação usada em 2026-05-05, a porta `8001` estava ocupada por outro projeto, então a validação ficou em `docker compose --profile audio config --quiet` e `docker run --rm wordbridge-coach-tts piper --help >/dev/null`.
Com `WORDBRIDGE_TTS_PORT`, o runtime completo pode ser validado sem liberar `8001`; na estação usada em 2026-05-05, `WORDBRIDGE_TTS_PORT=18101 docker compose --profile audio up -d tts` + `/health` passou.

## Calibração pedagógica

Depois de uma sessão real, exporte os sinais atuais do usuário:

```bash
WORDBRIDGE_DB_PORT=55432 docker compose exec -T api python scripts/export_pedagogy_calibration.py --username demo
```

Esse export deve ser comparado com a experiência observada antes de ajustar limiares pedagógicos. O protocolo completo fica em `docs/CALIBRATION.md`.

Na calibração de 2026-05-05, o usuário `demo` sem retenção real exportava `retention_band=unknown` mas ainda recomendava aceleração. O limiar foi ajustado para exigir sinal de retenção antes de `ready_to_push`; com isso o export passou a `difficulty_signal=on_target`, `recommended_pace=balance` e `recommended_mode=spec4`.

## Backup e restore local

Antes de uso continuado ou mudanças destrutivas no banco local, gere um dump:

```bash
./scripts/db_backup.sh
```

Por padrão, o arquivo vai para `backups/wordbridge-YYYYMMDD-HHMMSS.dump`. Esse diretório é ignorado pelo Git.

Restore é destrutivo e exige confirmação explícita:

```bash
./scripts/db_restore.sh --yes backups/wordbridge-YYYYMMDD-HHMMSS.dump
```

Os scripts assumem o serviço Compose `db` ativo e usam `pg_dump`/`pg_restore` dentro do container Postgres.

## Configuração e secrets

O contrato versionado de ambiente fica em `.env.example`. Arquivos `.env` reais são locais, ignorados pelo Git e não devem guardar segredo commitado.

Contrato recomendado:

- local: `ENVIRONMENT=development`, `DEBUG=true`, `STRICT_CONFIG=false`
- staging/produção: `ENVIRONMENT=staging` ou `production`, `DEBUG=false`, `STRICT_CONFIG=true`, `SECRET_KEY` gerado fora do repositório

Validação focal:

```bash
cd api
TMPDIR=/home/edann/projects/wordbridge-coach/.tmp_pytest PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest tests/test_config_runtime.py -q
```

## CI

Existe um baseline inicial de quality gate em `.github/workflows/quality.yml` cobrindo:

- `frontend`: `npm ci`, `npm run lint`, `npm run typecheck`, `npm run build`
- `compose`: `docker compose config --quiet`
- `api`: trilhas críticas já validadas de draft/state/feedback/contexto/adapters/handlers/entrega/texto/rest/conversation/generation/runtime/websocket/orquestração/utilitários de chat, autofill Lingvist, fluxo legado `/cards/next`, WebSocket, progressão, Spec4 e avaliação determinística de sinais pedagógicos
- `e2e-chromium`: Playwright Chromium cobrindo a suíte completa de `tests/e2e/tests/*.spec.ts` contra o stack padrão `db/api/frontend`, sem IA local e sem TTS obrigatório

## Regra prática

- mudanças de backend: rode `pytest` no escopo tocado
- mudanças de frontend: rode `./scripts/frontend_tooling.sh check`
- mudanças de fluxo crítico: rode `npm run test:ci` em `tests/e2e/`; use `npm run test:smoke` apenas quando a intenção for um check curto de sanidade
- mudanças amplas: valide também `docker compose`, `alembic upgrade head` e healthchecks
- mudanças em `docker-compose.yml`, `frontend/nginx.conf`, startup da API ou scripts de setup precisam validar o runtime padrão `db/api/frontend`, não só `docker compose config`
- se `5432` estiver ocupada no host, use `WORDBRIDGE_DB_PORT=55432` para o stack local sem afetar a rede interna do compose
- use `INSTALL_ARGOS=true` apenas quando precisar validar tradução offline por Argos; a imagem base da API não instala essa dependência pesada por padrão
