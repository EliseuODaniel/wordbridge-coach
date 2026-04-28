# Roadmap

Data de início desta nova fase: 2026-03-23

## Status de retomada em 2026-04-24

- branding público renomeado de `FillTheWord` para `WordBridge Coach`
- repositório GitHub renomeado para `EliseuODaniel/wordbridge-coach`
- workspace local movido para `/home/edann/projects/wordbridge-coach`
- `api/test-runner.sh` e docs de teste foram ajustados para continuar funcionando após a mudança de pasta
- `main` local e `origin/main` estavam alinhados no commit `245039f` antes desta rodada de análise
- a próxima frente deve priorizar confiabilidade operacional e avaliação pedagógica antes de novas features grandes

## Objetivo

Refatorar o projeto com segurança, reduzindo complexidade e melhorando legibilidade, testabilidade e onboarding.

## Direção recomendada

O produto já passou da fase de "fazer existir". A próxima fase deve provar que ele é confiável, avaliável e agradável de usar repetidamente.

Prioridades:

- runtime local padrão previsível: `db/api/frontend` deve subir sem `audio` e sem `ai`
- feedback de falhas visível no frontend, sem ações silenciosas
- métricas pedagógicas calibradas com casos reais e datasets pequenos de regressão
- observabilidade mínima para startup, criação de perfil, sessão de estudo, Chat Coach e fallback de LLM
- fronteiras claras entre experiência principal, áudio opcional e IA local opcional

## Fase 0: Reset de governança

Status: concluida

- [x] definir `AGENTS.md` como regra única do repositório
- [x] criar documentação oficial em `docs/`
- [x] remover OpenSpec e instruções específicas de Claude
- [x] revisar o restante da documentação operacional após a limpeza

## Fase 1: Baseline técnico

Status: concluida

- [x] validar comandos reais de setup, lint, build e testes
- [x] reduzir a fila inicial de lint do frontend ate voltar para baseline limpo
- [~] revisar o `docker-compose.yml` com foco em simplicidade
- [x] mapear módulos mais acoplados no backend e frontend
- [x] registrar riscos confirmados em `docs/DECISIONS.md`

Notas do baseline:

- `docker compose config --quiet`: OK
- `frontend npm ci`: OK
- `frontend build`: OK
- `frontend lint`: OK depois das fatias de hooks/efeitos e tipagem de erros/contratos
- `python3 -m py_compile api/app/services/card_selection.py api/app/api/api_v1/endpoints/cards.py`: OK
- `api/.venv` local criado para testes de backend
- `cd api && PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest tests/integration/test_spec4_card_selection.py -q`: OK
- `cd api && PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest tests/test_chat_utilities.py -q`: OK
- `python3 -m py_compile api/app/api/api_v1/endpoints/chat.py api/tests/test_chat_utilities.py`: OK
- `cd api && TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test ./test-runner.sh --spec4`: OK
- primeira microfatia aplicada: alinhamento do setup operacional e simplificacao do shell inicial do frontend
- segunda microfatia aplicada: limpeza de hooks/efeitos em componentes base; lint caiu de 46 para 41 problemas
- terceira microfatia aplicada: padronizacao de erros da API, remocao de `any` e fechamento da fila residual de lint
- quarta microfatia aplicada: consolidacao da configuracao repetida dos servicos LLM no compose e extracao de helpers de usuario/idioma no fluxo de cards
- quinta microfatia aplicada: extracao de helpers locais no endpoint Lingvist para separar lookup, audio e montagem de payload
- sexta microfatia aplicada: extracao de helpers de stats/relearn em `submit_answer` e recuperacao do fluxo local de testes do backend
- setima microfatia aplicada: limpeza do bloco REST de `chat.py`, correção do sanitizer e validação utilitária local de Chat Coach
- oitava microfatia aplicada: extração do pipeline comum de `draft_feedback` no Chat Coach e cobertura utilitária dos novos helpers
- nona microfatia aplicada: extração das funções puras de prompt/config/fallback em `handle_user_message` com expansão da suíte utilitária de chat
- decima microfatia aplicada: extração de helpers de persistência/event payload em `handle_user_message` com ampliação da cobertura utilitária de teacher analysis
- decima primeira microfatia aplicada: extração do payload `assistant_done` e da geração/envio de `teacher_analysis` com fallback, mantendo chat utilitário e Spec4 verdes
- decima segunda microfatia aplicada: extração do congelamento de feedback do envio, da persistência do `user_message` e da preparação dos inputs de geração em `handle_user_message`
- decima terceira microfatia aplicada: primeiro teste integrado do WebSocket de chat e correção da persistência de `teacher_analysis` em `metadata_json`
- decima quarta microfatia aplicada: extração da finalização do turno do assistente e da persistência/envio de `teacher_analysis`, com expansão da suíte utilitária de chat
- decima quinta microfatia aplicada: endurecimento do fixture de banco em `conftest.py` para reduzir resíduos de schema em execuções seriais repetidas
- decima sexta microfatia aplicada: centralização de tempo UTC em helper compartilhado e migração parcial de schemas/configs quentes para padrões atuais do Pydantic
- decima setima microfatia aplicada: remoção dos warnings visíveis da trilha principal de chat (`declarative_base`, `class Config`, defaults UTC de modelo)
- decima oitava microfatia aplicada: remoção dos warnings visíveis da trilha Spec4 (`IN (subquery)`, defaults UTC restantes e fixtures de teste)
- decima nona microfatia aplicada: simplificação do `StudySession` com helpers de audio e limpeza explícita dos timers de avanço e retry
- vigesima microfatia aplicada: simplificação do `ChatCoachSession` com cleanup centralizado de autocomplete, foco e desconexão do WebSocket
- vigesima primeira microfatia aplicada: simplificação do `LingvistSession` com reset de rodada, preload de audio e playback manual centralizados
- vigesima segunda microfatia aplicada: centralização da troca entre `Spec4` e `Lingvist` no shell React, removendo reload completo entre modos
- vigesima terceira microfatia aplicada: preparação do repositório para Codex com `AGENTS.md` por área, skills adicionais, guia de setup e quality gate inicial em CI
- vigesima quarta microfatia aplicada: redução do peso do loop WebSocket de `chat.py` com helpers de setup, dispatch e erro
- vigesima quinta microfatia aplicada: remoção de hardcodes de idioma em `VocabularyProgressionService` com cobertura focal nova
- vigesima sexta microfatia aplicada: encapsulamento do turno `user_message` do Chat Coach e uso de contexto teacher baseado nas mensagens do aluno
- vigesima setima microfatia aplicada: criação de runtime dedicado para a sessão WebSocket do Chat Coach
- vigesima oitava microfatia aplicada: limpeza do `UserSelection` para usar idioma/meta reais e stats reais por perfil
- vigesima nona microfatia aplicada: extração do runtime e do roteamento base do WebSocket de chat para `api/app/services/chat_runtime_service.py`, com cobertura unitária própria e inclusão no quality gate
- trigesima microfatia aplicada: extração da coordenação do turno `user_message` para `api/app/services/chat_turn_service.py`, com teste focal de orquestração e inclusão no quality gate
- trigesima primeira microfatia aplicada: extração da orquestração de `draft_update` e `request_autocomplete` para `api/app/services/chat_draft_service.py`, com testes focais e inclusão no quality gate
- trigesima segunda microfatia aplicada: extração da montagem de `draft_feedback` e das integrações de micro-eval/LanguageTool para `api/app/services/chat_feedback_service.py`, com cobertura própria e inclusão no quality gate
- trigesima terceira microfatia aplicada: extração da construção de contexto de chat/teacher para `api/app/services/chat_context_service.py`, com wrappers compatíveis e cobertura própria no quality gate
- trigesima quarta microfatia aplicada: extração da persistência de mensagens e dos payloads/eventos finais para `api/app/services/chat_delivery_service.py`, com wrappers compatíveis e cobertura própria no quality gate
- trigesima quinta microfatia aplicada: extração dos helpers puros de prompt, geração, fallback e sanitização para `api/app/services/chat_text_service.py`, com wrappers compatíveis e cobertura própria no quality gate
- trigesima sexta microfatia aplicada: extração do lookup e da serialização REST para `api/app/services/chat_rest_service.py`, com wrappers compatíveis e cobertura própria no quality gate
- trigesima setima microfatia aplicada: extração do enriquecimento do payload Lingvist para `api/app/services/lingvist_payload_service.py`, com wrappers compatíveis e cobertura própria no quality gate
- trigesima oitava microfatia aplicada: extração da resolução do usuário padrão e da serialização comum de `CardResponse` para `api/app/services/card_response_service.py`, com wrappers compatíveis e cobertura própria no quality gate
- trigesima nona microfatia aplicada: extração da criação de `UserCardState`, de `ReviewEvent`, da aplicação do resultado SM-2 e da serialização de `AnswerResponse` para `api/app/services/card_answer_service.py`, com wrappers compatíveis e cobertura própria no quality gate
- quadragesima microfatia aplicada: extração da orquestração agregada de stats e progressão de `submit_answer` para `api/app/services/card_progress_service.py`, com wrappers compatíveis e cobertura própria no quality gate
- quadragesima primeira microfatia aplicada: extração da orquestração principal de `submit_answer` para `api/app/services/card_submission_service.py`, com endpoint reduzido a adaptador fino e cobertura própria no quality gate
- quadragesima segunda microfatia aplicada: extração da seleção e serialização de `next-spec4` para `api/app/services/card_spec4_service.py`, com endpoint reduzido a adaptador fino e cobertura própria no quality gate
- quadragesima terceira microfatia aplicada: extração da orquestração de `next-lingvist` para `api/app/services/card_lingvist_service.py`, com endpoint reduzido a adaptador fino e cobertura própria no quality gate
- quadragesima quarta microfatia aplicada: extração da criação/garantia de `Card` e da montagem do payload comum de seleção para `api/app/services/card_selection_payload_service.py`, reduzindo o peso de `CardSelectionService`
- quadragesima quinta microfatia aplicada: extração das regras de mistura e decisão de tentativa de card novo para `api/app/services/card_selection_policy_service.py`, reduzindo o peso de `CardSelectionService`
- quadragesima sexta microfatia aplicada: extração das queries de review, relearn, backlog e anti-repetição correta para `api/app/services/card_selection_query_service.py`, reduzindo o peso de `CardSelectionService`
- quadragesima setima microfatia aplicada: extração do fallback de card elegível e do lookup legado por rank para `api/app/services/card_selection_fallback_service.py`, reduzindo o peso de `CardSelectionService`
- quadragesima oitava microfatia aplicada: extração da atualização de progressão Spec4 pós-resposta para `api/app/services/card_selection_progress_service.py`, com limpeza do legado residual de `CardSelectionService` e cobertura própria no quality gate
- quadragesima nona microfatia aplicada: consolidação do fechamento comum de seleção dentro de `CardSelectionService`, reduzindo duplicação entre os fluxos `new`, `review`, `relearn` e `fallback`
- quinquagesima microfatia aplicada: remoção dos wrappers REST redundantes de `chat.py`, deixando os endpoints HTTP chamarem `chat_rest_service` diretamente
- quinquagesima primeira microfatia aplicada: extração do bootstrap demo e do autofill de traduções Lingvist de `cards.py` para services dedicados, com cobertura focal própria e inclusão no quality gate
- quinquagesima segunda microfatia aplicada: extração do fluxo legado de `/cards/next` para `api/app/services/card_next_service.py`, com cobertura focal própria e inclusão no quality gate
- quinquagesima terceira microfatia aplicada: remoção dos wrappers locais redundantes de `cards.py`, deixando os endpoints chamarem diretamente os services de legado, Spec4 e Lingvist
- quinquagesima quarta microfatia aplicada: extração da criação/listagem/remoção de conversas de `chat.py` para `api/app/services/chat_conversation_service.py`, com cobertura focal própria e inclusão no quality gate
- quinquagesima quinta microfatia aplicada: extração do streaming do assistente e da geração com fallback de `teacher_analysis` de `chat.py` para `api/app/services/chat_generation_service.py`, com cobertura focal própria e wrappers compatíveis
- quinquagesima sexta microfatia aplicada: extração do estado em memória de draft/throttle de `chat.py` para `api/app/services/chat_draft_state_service.py`, com cobertura focal própria e wrappers compatíveis
- quinquagesima sétima microfatia aplicada: extração do lifecycle do endpoint WebSocket de `chat.py` para `api/app/services/chat_websocket_service.py`, com cobertura focal própria e manutenção do fluxo integrado
- quinquagesima oitava microfatia aplicada: extração dos handlers de evento do WebSocket de `chat.py` para `api/app/services/chat_handler_service.py`, com cobertura focal própria e redução do wiring residual do endpoint
- quinquagesima nona microfatia aplicada: extração dos adapters configurados por ambiente de `chat.py` para `api/app/services/chat_endpoint_adapter_service.py`, com cobertura focal própria e redução adicional das closures locais do endpoint
- sexagesima microfatia aplicada: extração da montagem de `ChatHandlerDeps` de `chat.py` para `api/app/services/chat_handler_service.py`, reduzindo mais um bloco de wiring de alto nível do endpoint
- sexagesima primeira microfatia aplicada: extração da montagem de `ChatWebSocketSessionDeps` de `chat.py` para `api/app/services/chat_websocket_service.py`, com limpeza adicional das aliases de contexto e redução final do wiring local do endpoint
- sexagesima segunda microfatia aplicada: extração do cliente Axios e dos helpers de erro de `frontend/src/services/api.ts` para `frontend/src/services/apiClient.ts` e `frontend/src/services/apiErrors.ts`, mantendo `api.ts` como fachada compatível
- sexagesima terceira microfatia aplicada: extração das APIs por domínio de `frontend/src/services/api.ts` para `apiCards.ts`, `apiUsers.ts`, `apiInsights.ts`, `apiChat.ts`, `apiLlmProfiles.ts` e `apiHealth.ts`, reduzindo `api.ts` a uma fachada curta de reexports
- sexagesima quarta microfatia aplicada: migração dos consumidores do frontend para imports diretos por domínio (`apiCards`, `apiUsers`, `apiInsights`, `apiChat`, `apiLlmProfiles`, `apiHealth`, `apiErrors`), reduzindo o acoplamento remanescente com a fachada `api.ts`
- sexagesima quinta microfatia aplicada: extração de helpers locais de mensagem/scroll em `frontend/src/components/chatCoachSessionHelpers.ts` e encapsulamento de callbacks repetidos do composer em `ChatCoachSession.tsx`
- sexagesima sexta microfatia aplicada: extração do bootstrap da conversa e da criação do `ChatWS` para `frontend/src/components/chatCoachSessionTransport.ts`, além da remoção dos imports restantes de `services/api` no `frontend/src`
- sexagesima sétima microfatia aplicada: consolidação do estado de feedback/autocomplete de `ChatCoachSession.tsx` em `chatCoachSessionFeedback.ts`, reduzindo a coordenação de sinais de draft espalhados no componente
- sexagesima oitava microfatia aplicada: extração do bloco visual do composer de `ChatCoachSession.tsx` para `frontend/src/components/ChatCoachComposer.tsx`, reduzindo o peso do componente principal sem alterar a UX
- sexagesima nona microfatia aplicada: extração da lista de mensagens, do streaming e do botão `jump to latest` de `ChatCoachSession.tsx` para `frontend/src/components/ChatCoachMessagePane.tsx`, reduzindo significativamente o peso do componente principal
- septuagesima microfatia aplicada: extração do header e da tela de carregamento de `ChatCoachSession.tsx` para `frontend/src/components/ChatCoachHeader.tsx` e `frontend/src/components/ChatCoachLoading.tsx`, reduzindo o ruído visual residual do container
- septuagesima primeira microfatia aplicada: extração da coordenação de sessão de `ChatCoachSession.tsx` para `frontend/src/components/useChatCoachSession.ts`, deixando o componente principal como composição fina de UI
- septuagesima segunda microfatia aplicada: adoção do Gemma 4 E4B como perfil local principal, com normalização de defaults, docs e fallback seguro para preferências persistidas antigas
- septuagesima terceira microfatia aplicada: extração da coordenação do `LingvistSession` para `frontend/src/components/useLingvistSession.ts` e `lingvistSessionHelpers.ts`, reduzindo o peso do container principal
- septuagesima quarta microfatia aplicada: extração da coordenação do `StudySession` para `frontend/src/components/useStudySession.ts`, deixando a tela principal mais próxima de composição visual
- septuagesima quinta microfatia aplicada: extração da coordenação do `UserSelection` para `frontend/src/components/useUserSelection.ts`, com formulários dedicados para criação e edição de perfil
- septuagesima sexta microfatia aplicada: criação de `scripts/frontend_tooling.sh` e separação explícita de `typecheck`/`build`, estabilizando o fluxo local de frontend no ambiente híbrido Windows/WSL
- septuagesima sétima microfatia aplicada: redução do stack padrão do compose para `db/api/frontend`, tornando TTS opcional via perfil `audio` e IA local opcional via perfil `ai`
- septuagesima oitava microfatia aplicada: adição de smoke E2E Chromium ao quality gate e cobertura explícita de `typecheck`, `compose config` e `test_user_llm_preferences_service.py`
- septuagesima nona microfatia aplicada: estabilização das fronteiras de plataforma com pool de banco dependente do backend, transporte frontend relativo (`/api` e `/api/tts`) e remoção do bootstrap implícito de usuário demo em `stats`/`settings`
- octogesima microfatia aplicada: extração de insights por palavra/card para `api/app/services/insights_service.py` e extração da orquestração por modo para `api/app/services/card_selection_mode_service.py`
- octogesima primeira microfatia aplicada: expansão do quality gate de E2E para a suíte Chromium completa e alinhamento dos testes de criação de perfil à nova UI de metas por botões
- octogesima segunda microfatia aplicada: extração da resolução de novo/review/fallback/relearn de `CardSelectionService` para `api/app/services/card_selection_resolution_service.py`, fechando o hotspot residual do service principal
- octogesima terceira microfatia aplicada: divisão do `MockLLMProvider` em `mock_text_analysis.py`, `mock_chat_responses.py` e `mock_feedback_payloads.py`, deixando o provider como adaptador fino e validado por suíte própria
- octogesima quarta microfatia aplicada: adoção de structured outputs pedagógicos no Chat Coach para `micro_eval`, autocomplete e `teacher_analysis`, com fallback seguro para o mock e sidebar enriquecida com sinais cognitivos, metacognitivos e motivacionais
- octogesima quinta microfatia aplicada: fechamento do lookahead real do Lingvist com ordenação explícita por frequência, escolha ponderada dentro do pool e cobertura focal para a nova variedade controlada
- octogesima sexta microfatia aplicada: criação de `chat_profile_service.py` para derivar memória pedagógica longitudinal de `User` + histórico recente de `teacher_analysis`, sem nova tabela e com atualização a cada turno
- octogesima sétima microfatia aplicada: alinhamento do Chat Coach ao idioma do aluno e ao perfil longitudinal em prompts, payloads WebSocket e sidebar de "coach memory", conectando analytics, scaffolding e feedback entre sessões
- octogesima oitava microfatia aplicada: introdução de `pedagogical_state` explícito, `lesson_frame` adaptativo por turno e snapshots persistidos em `chat_lesson_history`, reaproveitando a tabela já existente em vez de abrir nova árvore de estado
- octogesima nona microfatia aplicada: extensão do contrato WebSocket de `teacher_analysis` com `lesson_frame` atualizado e integração de `learning_context` compartilhado entre Chat Coach, Spec4 e Lingvist, com painéis visuais dedicados no frontend e cobertura focal nova
- nonagesima microfatia aplicada: introdução de `pedagogical_metrics` explícitos derivados de progresso real (`UserCardState`, `ReviewEvent`, `UserSessionStats`), projeção desses sinais em `lesson_frame.diagnostics` e `learning_context`, calibração adaptativa do perfil Lingvist e estabilização do E2E com seletor dedicado para o input inline
- nonagesima primeira microfatia aplicada: centralização do proxy de desenvolvimento do Vite em `frontend/viteProxy.ts`, com rota explícita para WebSocket do Chat Coach, targets configuráveis por ambiente e remoção do proxy legado divergente de `/api/audio`
- nonagesima segunda microfatia aplicada: simplificação do runtime TTS para Piper-only, removendo Coqui/Torch/librosa/numpy e a instalação duplicada de `piper-tts` do build do perfil `audio`
- nonagesima terceira microfatia aplicada: criação de snapshots determinísticos para prompt/schema de `teacher_analysis`, com schema strict exigindo todos os campos declarados nos structured outputs do OpenAI
- nonagesima quarta microfatia aplicada: simulações determinísticas de usuários para medir a adaptação do Lingvist contra o baseline da fase, cobrindo suporte, equilíbrio, aceleração e bloqueio por pressão alta de review
- nonagesima quinta microfatia aplicada: decisão de manter analytics pedagógico projetado a partir de `student_profile_json`, `lesson_frame_json`, `chat_lesson_history` e tabelas cruas nesta fase, com helper explícito de projeção para endpoint futuro
- nonagesima sexta microfatia aplicada: formalização do contrato de configuração com `.env.example`, defaults locais explícitos no compose e validação de `ENVIRONMENT`, `DEBUG`, `STRICT_CONFIG` e `SECRET_KEY`
- nonagesima sétima microfatia aplicada: criação de scripts locais de backup/restore do Postgres (`scripts/db_backup.sh` e `scripts/db_restore.sh`) com dumps ignorados em `backups/` e restore destrutivo protegido por `--yes`

## Fase 2: Limpeza estrutural

- [x] remover arquivos legados e snapshots que não são mais documentação viva
- [x] revisar comentários e referências internas para evitar apontar para docs removidas
- [x] consolidar documentação útil sob `docs/`

## Fase 3: Primeira onda de refatoração

Prioridade alta:

- [x] simplificar a entrada do frontend e a separação entre modos
- [x] continuar reduzindo timers e coordenação local nas sessões de frontend, começando por `StudySession`
- [x] continuar reduzindo coordenação espalhada no `ChatCoachSession`
- [x] continuar reduzindo duplicação operacional no `LingvistSession`
- [x] revisar os serviços da API com maior acoplamento
- [~] continuar quebrando o fluxo WebSocket de `chat.py` em helpers menores e testáveis
- [~] continuar removendo pressupostos de idioma do domínio de progressão
- [~] isolar melhor integrações de LLM local e LanguageTool
- [x] decidir e aplicar a extração do runtime/service próprio para o WebSocket
- [x] continuar removendo pontos provisórios visíveis do frontend, começando pela seleção de perfil

## Fase 4: Qualidade e confiança

- [x] alinhar testes ao comportamento realmente suportado
- [~] manter suítes de backend com banco compartilhado em execução serial
- [~] revisar lacunas de cobertura nos fluxos críticos
- [x] eliminar falsos positivos de documentação e scripts antigos (mensagens de setup legadas em quick_start, strings de debug em paths de produção, `.env` duplicado)
- [x] consolidar quality gates locais e em CI para frontend, backend crítico e suíte Chromium de E2E
- [~] ampliar cobertura focal de regras de domínio no backend, além de chat e Spec4
- [x] rerodar localmente os specs Playwright focais de `StudySession` e `LingvistSession` quando houver runtime Node/Playwright estável na thread
- [x] validar novamente backend, frontend, test-runner e Playwright focal depois do rename público e da mudança do workspace
- [x] adicionar validação de startup da API com modo estrito opcional (`STRICT_CONFIG`) e registrar issues de configuração com logger

## Fase 5: Runtime local confiável

Prioridade alta:

- [x] garantir que o frontend containerizado não dependa do upstream `tts` quando o perfil `audio` estiver desligado
- [x] mostrar erro visível no fluxo de criação de perfil quando a API falhar
- [x] corrigir boot de volume novo do Postgres removendo índices prematuros de `scripts/init.sql`
- [x] formalizar smoke local curto para `db/api/frontend`: health, listagem/criação de perfil e carregamento do frontend
- [x] alinhar `quick_start.sh`, README e `docs/TESTING.md` com `WORDBRIDGE_DB_PORT` como variável principal
- [x] separar dependências pesadas de NLP/Torch/CUDA do runtime base da API ou documentar explicitamente esse custo
- [x] revisar o custo de build do serviço `tts` e decidir se ele deve ser uma imagem separada, pré-buildada ou documentação de instalação sob demanda
- [x] reduzir divergência entre Vite dev server e Nginx containerizado

## Fase 6: Avaliação pedagógica

Prioridade alta:

- [x] criar fixtures pequenas de histórico de estudo para validar `pedagogical_metrics`, `lesson_frame` e `learning_context`
- [x] registrar expectativas de retenção, pressão de review, pacing e melhor próximo modo em testes determinísticos
- [x] medir se o ajuste de dificuldade do Lingvist melhora ou piora previsibilidade em usuários simulados
- [x] avaliar se `student_profile_json` continua suficiente ou se analytics pedagógico merece endpoint/tabela própria
- [x] criar snapshots de prompt/teacher-analysis para evitar regressão silenciosa na qualidade do Chat Coach

## Fase 7: Operabilidade e preparação de release local

Prioridade média:

- [x] migrar startup checks da API de `@app.on_event("startup")` para `lifespan`
- [x] definir contrato de configuração local, staging e produção (`SECRET_KEY`, `DEBUG`, `ENVIRONMENT`, `STRICT_CONFIG`)
- [x] adicionar logs estruturados mínimos para criação de perfil, seleção de card, chat turn e fallback de provider
- [x] decidir política de secrets e `.env.example`
- [x] preparar um fluxo de backup/restore local do banco antes de uso continuado

## Critérios de sucesso

- onboarding mais curto
- menos arquivos concorrendo como fonte de verdade
- documentação compatível com o código atual
- refatorações futuras divididas em fatias pequenas e verificáveis
- estado pedagógico compartilhado entre modos sem depender de memória implícita ou heurística escondida no frontend
- adaptação pedagógica guiada por sinais explícitos de retenção, pressão de review e pacing, e não só por heurísticas textuais implícitas
- próxima retomada conseguir se orientar pelos docs oficiais sem depender da memória desta thread
