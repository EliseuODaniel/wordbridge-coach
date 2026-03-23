# Project Status

Data de referência: 2026-03-23

## Resumo executivo

FillTheWord já funciona como uma aplicação local multi-serviço para estudo de vocabulário. O projeto foi além do MVP original e hoje mistura:

- loop principal de estudo com SRS
- um modo estilo Lingvist
- um modo Chat Coach com LLM local
- TTS local com cache em disco
- LanguageTool para apoio de escrita

O código existe, mas a governança documental antiga gerou múltiplas versões da verdade. A partir desta data, este arquivo passa a registrar o estado oficial do projeto.

## Estado atual do produto

### Baseline tecnico validado nesta fase

- `docker compose config --quiet`: OK depois da remocao do campo `version` obsoleto e da consolidacao do bloco compartilhado dos servicos LLM
- `cd frontend && npm ci`: OK
- `cd frontend && npm run build`: OK
- `cd frontend && npm run lint`: OK apos a limpeza de hooks, contratos de erro e tipagem de APIs no frontend
- `python3 -m py_compile api/app/services/card_selection.py api/app/api/api_v1/endpoints/cards.py`: OK
- `cd api && PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/integration/test_spec4_card_selection.py -q`: OK
- `cd api && PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_chat_utilities.py -q`: OK
- `cd api && PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/integration/test_chat_websocket_flow.py -q`: OK
- `python3 -m py_compile api/app/api/api_v1/endpoints/chat.py api/tests/test_chat_utilities.py`: OK
- `cd api && PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest -o addopts='' tests/test_chat_utilities.py -W default -rw`: OK sem warnings visíveis
- `cd api && PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest -o addopts='' tests/integration/test_chat_websocket_flow.py -W default -rw`: OK sem warnings visíveis
- `cd api && PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest -o addopts='' tests/integration/test_spec4_card_selection.py -W default -rw`: OK sem warnings visíveis
- `cd api && TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test ./test-runner.sh --spec4`: OK

### Áreas implementadas

- API principal em FastAPI com rotas de cards, stats, settings, users, insights, chat e perfis de LLM
- frontend React com seleção de usuário e três modos de treino
- serviço TTS separado
- compose local com banco, API, frontend, TTS, LLM principal, LLM teacher, LLM chat opcional e LanguageTool
- suíte de testes backend e uma base de testes E2E com Playwright

### Áreas que precisam de atenção

- documentação estava espalhada e conflitante
- README anterior misturava estado atual com snapshots antigos de implementação
- há sinais de crescimento orgânico forte em Chat Coach e Lingvist
- o projeto ainda precisa de uma rodada de simplificação arquitetural antes de novas features
- o próximo foco técnico saiu de lint básico e passou para simplificação estrutural dos módulos mais acoplados
- o ambiente de testes do backend voltou a funcionar localmente para a trilha Spec4 e utilitários de chat, mas ainda faltam mais suítes e redução de warnings
- agora existe também um teste integrado do WebSocket do Chat Coach cobrindo `user_message -> stream -> assistant_done -> teacher_analysis`
- o Chat Coach REST e o pipeline de feedback já começaram a ser desacoplados, mas o loop WebSocket ainda concentra muita responsabilidade
- o bloco `handle_user_message` já perdeu parte da duplicação estrutural, da persistência, do congelamento de feedback, do payload final e da geração/envio de teacher analysis, mas ainda concentra coordenação demais para um único handler
- o `handle_user_message` agora já delega também a finalização do turno do assistente e a persistência/envio de `teacher_analysis`, então o restante do debt nesse fluxo ficou mais concentrado em orquestração e warnings do que em blocos repetidos
- o fixture de banco dos testes backend ficou mais resiliente para execuções seriais repetidas, reduzindo falhas por resíduos de schema e enums PostgreSQL
- o backend agora centraliza mais do tempo UTC em helper compartilhado e já migrou parte dos schemas/configs quentes para padrões atuais de Pydantic
- a trilha principal de chat backend ficou sem warnings visíveis nas validações direcionadas; o maior volume residual agora está concentrado fora desse miolo
- a trilha Spec4 também ficou sem warnings visíveis nas validações direcionadas, então o debt residual de warnings saiu do fluxo principal de cards
- as suítes que compartilham o mesmo banco de teste devem rodar em série; em paralelo elas brigam pelo ciclo `create_all/drop_all`
- o `StudySession` já teve uma primeira simplificação estrutural no frontend, com helpers dedicados para audio e limpeza explícita dos timers de avancar e retry
- o `ChatCoachSession` agora também centraliza melhor cleanup local de autocomplete, foco do composer e desconexão do WebSocket, reduzindo coordenação espalhada no componente
- o `LingvistSession` agora reaproveita melhor reset de rodada, preload de audio e playback manual, reduzindo duplicação sem alterar o fluxo de treino
- a troca entre `Spec4` e `Lingvist` agora passa pelo shell React em vez de recarregar a página, o que reduz acoplamento com URL e deixa a navegação entre modos mais consistente
- o repositório agora tem `AGENTS.md` por área em `api/`, `frontend/`, `tts/` e `tests/e2e/`, além de um guia oficial de setup em `docs/CODEX_SETUP.md`
- as skills repo-locais agora cobrem também readiness de Codex, fatias de endpoint backend e fatias de sessão frontend
- existe um quality gate inicial em `.github/workflows/quality.yml` para frontend e trilhas críticas de backend
- o `chat.py` perdeu mais um pouco de acoplamento no loop WebSocket, com setup, dispatch e payloads de erro mais padronizados
- o fluxo `user_message` do Chat Coach agora também está mais encapsulado, e a `teacher_analysis` passou a preferir contexto real das mensagens do aluno em vez de depender apenas de `session_summary`
- a sessão WebSocket do Chat Coach agora resolve suas dependências por um runtime dedicado, reduzindo setup espalhado no endpoint
- o runtime e o roteamento base do WebSocket do Chat Coach agora vivem em `api/app/services/chat_runtime_service.py`, deixando `chat.py` mais próximo de uma fronteira de endpoint
- a coordenação do turno `user_message` do Chat Coach agora também saiu do endpoint e passou a viver em `api/app/services/chat_turn_service.py`, reduzindo o peso de `chat.py`
- o fluxo de `draft_update` e `request_autocomplete` do Chat Coach agora também é orquestrado por `api/app/services/chat_draft_service.py`, deixando os handlers do endpoint mais finos
- a montagem de `draft_feedback` e as integrações com `micro_eval` e LanguageTool do Chat Coach agora vivem em `api/app/services/chat_feedback_service.py`, reduzindo mais uma camada de detalhe em `chat.py`
- a construção de contexto de geração e de teacher analysis do Chat Coach agora também vive em `api/app/services/chat_context_service.py`, mantendo `chat.py` mais focado em adaptação de borda
- `VocabularyProgressionService` deixou de depender de idioma hardcoded para partes centrais da progressão, e agora respeita melhor a lingua alvo do usuário
- existe agora cobertura focal para progressão em `api/tests/test_vocabulary_progression.py`
- o `UserSelection` deixou de usar stats aleatórias e agora consome idioma alvo, meta de vocabulário e stats reais disponíveis por perfil

### Hotspots confirmados para refatoracao

Frontend:

- `frontend/src/components/ChatCoachSession.tsx`
- `frontend/src/components/LingvistSession.tsx`
- `frontend/src/components/UserSelection.tsx`
- `frontend/src/components/StudySession.tsx`
- `frontend/src/services/api.ts`

Backend:

- `api/app/api/api_v1/endpoints/cards.py`
- `api/app/api/api_v1/endpoints/chat.py`
- `api/app/llm/mock_provider.py`
- `api/app/services/card_selection.py`

## Componentes ativos

### Backend

Local: `api/`

Capacidades observadas:

- seleção de cards e regras de progressão
- estatísticas e insights
- configurações de usuário
- modo Chat Coach
- preferências de perfil de LLM
- integração com tradução e LanguageTool

### Frontend

Local: `frontend/`

Capacidades observadas:

- fluxo de seleção de usuário
- Study Session
- Lingvist Session
- Chat Coach Session
- painéis de analytics e componentes auxiliares

### TTS

Local: `tts/`

Capacidades observadas:

- geração e cache de áudio
- endpoints próprios de saúde e áudio

### Infra local

Arquivo principal: `docker-compose.yml`

Serviços hoje definidos:

- `db`
- `db_test`
- `api`
- `tts`
- `llm`
- `llm_chat`
- `llm_teacher`
- `languagetool`
- `frontend`

## Riscos principais

1. O produto prometido em docs antigas não batia mais com o código.
2. Há acoplamento considerável entre modos de estudo, analytics e integrações de IA local.
3. A superfície do `docker-compose.yml` cresceu e precisa ser revisada com foco em simplicidade.
4. Parte da documentação operacional ainda precisa ser validada durante a próxima rodada de refatoração.

## Objetivo desta nova fase

Entrar em um ciclo de refatoração com uma única base documental, reduzindo:

- drift entre docs e código
- acoplamento desnecessário
- ruído histórico no repositório
- custo cognitivo de onboarding

## Próximos passos imediatos

1. Continuar a simplificação do `docker-compose.yml`, agora focando em perfis opcionais e surface area do Chat Coach local.
2. Continuar a extração do Chat Coach, agora avaliando se o próximo corte deve mover a persistência/eventos restantes para services ou endurecer mais a cobertura de integração do fluxo completo.
3. Expandir a cobertura do backend para regras de progressão e idioma além da trilha recém-adicionada.
4. Consolidar o quality gate novo em CI e decidir se a próxima etapa adiciona E2E automatizado no mesmo pipeline.
