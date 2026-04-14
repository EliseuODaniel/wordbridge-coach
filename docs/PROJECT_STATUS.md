# Project Status

Data de referência: 2026-04-14

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
- `./scripts/frontend_tooling.sh check`: OK no fluxo Dockerizado suportado para ambiente híbrido Windows/WSL
- `docker build -t ftw-frontend-localcheck -f frontend/Dockerfile frontend`: OK
- `python3 -m py_compile api/app/services/card_selection.py api/app/api/api_v1/endpoints/cards.py`: OK
- `cd api && PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/integration/test_spec4_card_selection.py -q`: OK
- `cd api && PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_card_answer_service.py -q`: OK
- `cd api && PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_card_progress_service.py -q`: OK
- `cd api && PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_card_response_service.py -q`: OK
- `cd api && PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_card_submission_service.py -q`: OK
- `cd api && PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_card_spec4_service.py -q`: OK
- `cd api && PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_card_lingvist_service.py -q`: OK
- `cd api && PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_card_selection_payload_service.py -q`: OK
- `cd api && PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_card_selection_policy_service.py -q`: OK
- `cd api && PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_card_selection_query_service.py -q`: OK
- `cd api && PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_card_selection_fallback_service.py -q`: OK
- `cd api && PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_card_selection_progress_service.py -q`: OK
- `cd api && PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_chat_utilities.py -q`: OK
- `cd api && PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/integration/test_chat_websocket_flow.py -q`: OK
- `cd api && PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/integration/test_themes_stats.py -q`: OK
- `python3 -m py_compile api/app/api/api_v1/endpoints/chat.py api/tests/test_chat_utilities.py`: OK
- `cd api && PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest -o addopts='' tests/test_chat_utilities.py -W default -rw`: OK sem warnings visíveis
- `cd api && PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest -o addopts='' tests/integration/test_chat_websocket_flow.py -W default -rw`: OK sem warnings visíveis
- `cd api && PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest -o addopts='' tests/integration/test_spec4_card_selection.py -W default -rw`: OK sem warnings visíveis
- `cd api && TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test ./test-runner.sh --spec4`: OK

### Áreas implementadas

- API principal em FastAPI com rotas de cards, stats, settings, users, insights, chat e perfis de LLM
- frontend React com seleção de usuário e três modos de treino
- serviço TTS separado
- compose local com stack padrão reduzida para banco, API e frontend; perfil `audio` habilita TTS local e perfil `ai` habilita Gemma 4 E4B, LanguageTool e perfis opcionais de LLM secundária
- suíte de testes backend e uma suíte E2E Playwright Chromium validada contra o stack padrão `db/api/frontend`

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
- o `StudySession` agora concentra principalmente composição visual e delega coordenação de sessão para `useStudySession.ts`
- o `ChatCoachSession` agora também centraliza melhor cleanup local de autocomplete, foco do composer e desconexão do WebSocket, reduzindo coordenação espalhada no componente
- o `ChatCoachSession` agora também isola helpers locais de mensagens, scroll e limpeza do composer em `chatCoachSessionHelpers.ts` e callbacks mais focados, reduzindo repetição dentro do componente
- o `ChatCoachSession` agora também delega o bootstrap da conversa e a criação do `ChatWS` para `chatCoachSessionTransport.ts`, enquanto `chatWs.ts` já consome tipos direto de `apiChat`, reduzindo mais um pedaço de coordenação local e de acoplamento com a fachada antiga
- o `ChatCoachSession` agora também concentra os sinais de draft em um state object com helpers locais em `chatCoachSessionFeedback.ts`, reduzindo o espalhamento de `setState` de feedback/autocomplete no componente
- o bloco visual do composer do `ChatCoachSession` agora também vive em `ChatCoachComposer.tsx`, deixando o componente principal mais focado em estado e callbacks da sessão
- a área de mensagens, streaming e botão `jump to latest` do `ChatCoachSession` agora também vive em `ChatCoachMessagePane.tsx`, reduzindo mais um bloco de UI densa do componente principal
- o header e a tela de carregamento do `ChatCoachSession` agora também vivem em `ChatCoachHeader.tsx` e `ChatCoachLoading.tsx`, reduzindo o ruído visual restante do container
- a coordenação de estado, timers, bootstrap, scroll e lifecycle do `ChatCoachSession` agora também vive em `useChatCoachSession.ts`, deixando `ChatCoachSession.tsx` como composição fina da tela
- o `LingvistSession` agora concentra principalmente o shell visual do modo e delega reset, preload, playback e coordenação de rodada para `useLingvistSession.ts`
- o `frontend/src/services/api.ts` agora também delega o cliente Axios, os helpers de erro e as APIs por domínio para `apiClient.ts`, `apiErrors.ts`, `apiCards.ts`, `apiUsers.ts`, `apiInsights.ts`, `apiChat.ts`, `apiLlmProfiles.ts` e `apiHealth.ts`, reduzindo o hotspot sem mudar os imports externos
- os consumidores principais do frontend já passaram a importar APIs e tipos direto dos módulos de domínio, então `frontend/src/services/api.ts` ficou de fato como fachada compatível e não mais como ponto central de acoplamento
- o restante do `frontend/src` já não importa mais de `services/api`, então a fachada compatível ficou como camada de transição e não mais como dependência real dos fluxos principais
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
- a persistência de mensagens e os payloads/eventos finais do Chat Coach agora também vivem em `api/app/services/chat_delivery_service.py`, deixando `chat.py` com menos efeito colateral direto
- os helpers puros de prompt, configuração de geração, fallback e sanitização do Chat Coach agora também vivem em `api/app/services/chat_text_service.py`, deixando `chat.py` quase todo como camada adaptadora
- o streaming do assistente e a geração com fallback de `teacher_analysis` do Chat Coach agora também vivem em `api/app/services/chat_generation_service.py`, reduzindo mais uma camada operacional de `chat.py`
- o estado em memória de throttle/cache de draft do Chat Coach agora também vive em `api/app/services/chat_draft_state_service.py`, reduzindo mais um detalhe operacional de `chat.py`
- o lifecycle do endpoint WebSocket do Chat Coach agora também vive em `api/app/services/chat_websocket_service.py`, deixando `chat.py` mais próximo de uma borda fina
- os handlers de evento do WebSocket do Chat Coach agora também vivem em `api/app/services/chat_handler_service.py`, tirando de `chat.py` a montagem repetida de state/helpers por evento
- os adapters configurados por ambiente do Chat Coach agora também vivem em `api/app/services/chat_endpoint_adapter_service.py`, deixando `chat.py` com menos closures e menos wiring local
- o bundle `ChatHandlerDeps` do Chat Coach agora também é montado por `api/app/services/chat_handler_service.py`, removendo mais um bloco de configuração direta de `chat.py`
- o bundle `ChatWebSocketSessionDeps` do Chat Coach agora também é montado por `api/app/services/chat_websocket_service.py`, deixando `chat.py` quase só com a superfície FastAPI
- o lookup e a serialização do bloco REST do Chat Coach agora também vivem em `api/app/services/chat_rest_service.py`, reduzindo o miolo restante de `chat.py`
- a criação, listagem, listagem de mensagens e remoção de conversas do Chat Coach agora também vivem em `api/app/services/chat_conversation_service.py`, reduzindo mais um bloco REST de `chat.py`
- `chat.py` também deixou de manter wrappers REST locais redundantes para lookup e serialização, passando a chamar `chat_rest_service` diretamente nos endpoints HTTP
- o enriquecimento do payload Lingvist agora também vive em `api/app/services/lingvist_payload_service.py`, reduzindo o peso de `cards.py` sem mexer na regra de seleção
- o bootstrap local de dados demo e o autofill de traduções Lingvist agora também vivem em services dedicados, reduzindo mais uma camada operacional de `cards.py`
- o fluxo legado de `/cards/next` agora também vive em `api/app/services/card_next_service.py`, deixando `cards.py` mais próximo de uma borda HTTP
- `cards.py` também deixou de manter wrappers locais redundantes para os fluxos legado, Spec4 e Lingvist, passando a chamar os services diretamente nos endpoints
- a resolução de `user_id` padrão e a serialização comum de `CardResponse` agora também vivem em `api/app/services/card_response_service.py`, deixando `cards.py` com menos regra incidental de borda
- o fluxo de `submit_answer` agora também delega criação de `UserCardState`, `ReviewEvent`, aplicação do resultado SM-2 e serialização de `AnswerResponse` para `api/app/services/card_answer_service.py`
- a orquestração agregada pós-resposta de `submit_answer` agora também delega stats diárias, rolling accuracy, relearn, theme stats e progressão Spec4 para `api/app/services/card_progress_service.py`
- o `submit_answer` agora delega quase todo o fluxo para `api/app/services/card_submission_service.py`, deixando `cards.py` mais próximo de um adaptador de FastAPI
- o `next-spec4` agora também delega seleção e serialização para `api/app/services/card_spec4_service.py`, reduzindo mais um bloco de orquestração em `cards.py`
- o `next-lingvist` agora também delega seleção com override de mix, montagem do payload enriquecido e commit para `api/app/services/card_lingvist_service.py`
- `CardSelectionService` agora também delega a criação/garantia de `Card` e a montagem do payload comum para `api/app/services/card_selection_payload_service.py`
- `CardSelectionService` agora também delega as regras de mistura e decisão de tentativa de card novo para `api/app/services/card_selection_policy_service.py`
- `CardSelectionService` agora também delega queries de review, relearn, backlog e anti-repetição correta para `api/app/services/card_selection_query_service.py`
- `CardSelectionService` agora também delega o fallback de card elegível e o lookup legado por rank para `api/app/services/card_selection_fallback_service.py`
- a atualização de progressão Spec4 após resposta correta agora também vive em `api/app/services/card_selection_progress_service.py`, permitindo limpar o legado residual de `CardSelectionService`
- `CardSelectionService` agora também centraliza o fechamento comum de seleção em um helper interno, reduzindo duplicação entre os caminhos `new`, `review`, `relearn` e `fallback`
- `VocabularyProgressionService` deixou de depender de idioma hardcoded para partes centrais da progressão, e agora respeita melhor a lingua alvo do usuário
- existe agora cobertura focal para progressão em `api/tests/test_vocabulary_progression.py`
- o `UserSelection` agora concentra principalmente composição da tela e delega criação/edição/remoção/atalhos para `useUserSelection.ts`, `UserProfileCreateForm.tsx` e `UserProfileEditModal.tsx`
- o frontend ganhou um runner oficial em Docker (`./scripts/frontend_tooling.sh`) para estabilizar `lint`, `typecheck` e `build` em ambiente híbrido Windows/WSL
- o quality gate agora cobre explicitamente `typecheck`, `docker compose config --quiet`, novos testes focais de plataforma/insights/request-user/card-selection-mode e a suíte E2E Chromium completa em `tests/e2e/playwright.ci.config.ts`
- o stack padrão deixou de exigir LLM local, LanguageTool e TTS para subir; os perfis `ai` e `audio` passaram a ser opcionais conforme o fluxo
- o runtime principal da API agora usa configuração de pool coerente com o banco: `StaticPool` fica restrito a SQLite em memória, enquanto PostgreSQL usa pool padrão com `pool_pre_ping`
- o frontend passou a consumir URLs relativas (`/api` e `/api/tts`) no bundle de produção, com proxy explícito no Vite para desenvolvimento local
- `stats` e `settings` deixaram de depender de bootstrap implícito do usuário demo; os endpoints agora exigem `user_id` explícito na borda de leitura
- o lookup e a serialização de insights por palavra/card agora vivem em `api/app/services/insights_service.py`, reduzindo drift entre backend e frontend
- `CardSelectionService` agora delega a orquestração por modo para `api/app/services/card_selection_mode_service.py`, reduzindo o miolo residual mais acoplado
- `CardSelectionService` agora também delega montagem de payload, novo/review/fallback/relearn para `api/app/services/card_selection_resolution_service.py`, encerrando o hotspot residual de resolução dentro do service principal
- o `MockLLMProvider` agora ficou como adaptador fino e delega análise, respostas conversacionais e payloads pedagógicos para `mock_text_analysis.py`, `mock_chat_responses.py` e `mock_feedback_payloads.py`

### Hotspots residuais

Nesta fase, os hotspots estruturais principais de backend foram fechados. O que sobra agora é otimização incremental de heurísticas e cobertura, não mais refatoração obrigatória de arquivos monolíticos centrais.

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
3. A superfície do `docker-compose.yml` cresceu e precisa ser revisada com foco em simplicidade, embora a porta do Postgres local agora possa ser parametrizada por `FTW_DB_PORT`.
4. Parte da documentação operacional ainda precisa ser validada durante a próxima rodada de refatoração.

## Objetivo desta nova fase

Entrar em um ciclo de refatoração com uma única base documental, reduzindo:

- drift entre docs e código
- acoplamento desnecessário
- ruído histórico no repositório
- custo cognitivo de onboarding

## Próximos passos imediatos

1. Observar a estabilidade da suíte E2E Chromium completa no CI e decidir se vale separar smoke e regressão por custo/tempo.
2. Confirmar se `alembic upgrade head` e `seed_data.py` devem permanecer explícitos em todos os fluxos operacionais documentados.
3. Continuar reduzindo a superfície operacional do stack local, principalmente nas dependências opcionais de IA e áudio.
4. Voltar a investir em evolução de produto e analytics com a base estrutural já saneada.
