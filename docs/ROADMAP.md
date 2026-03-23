# Roadmap

Data de início desta nova fase: 2026-03-23

## Objetivo

Refatorar o projeto com segurança, reduzindo complexidade e melhorando legibilidade, testabilidade e onboarding.

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
- `cd api && PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/integration/test_spec4_card_selection.py -q`: OK
- `cd api && PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/pytest tests/test_chat_utilities.py -q`: OK
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

## Fase 2: Limpeza estrutural

- [x] remover arquivos legados e snapshots que não são mais documentação viva
- [x] revisar comentários e referências internas para evitar apontar para docs removidas
- [x] consolidar documentação útil sob `docs/`

## Fase 3: Primeira onda de refatoração

Prioridade alta:

- [x] simplificar a entrada do frontend e a separação entre modos
- [~] continuar reduzindo timers e coordenação local nas sessões de frontend, começando por `StudySession`
- [~] continuar reduzindo coordenação espalhada no `ChatCoachSession`
- [~] continuar reduzindo duplicação operacional no `LingvistSession`
- [ ] revisar os serviços da API com maior acoplamento
- [~] continuar quebrando o fluxo WebSocket de `chat.py` em helpers menores e testáveis
- [~] continuar removendo pressupostos de idioma do domínio de progressão
- [ ] isolar melhor integrações de LLM local e LanguageTool
- [x] decidir e aplicar a extração do runtime/service próprio para o WebSocket
- [~] continuar removendo pontos provisórios visíveis do frontend, começando pela seleção de perfil

## Fase 4: Qualidade e confiança

- [ ] alinhar testes ao comportamento realmente suportado
- [~] manter suítes de backend com banco compartilhado em execução serial
- [ ] revisar lacunas de cobertura nos fluxos críticos
- [ ] eliminar falsos positivos de documentação e scripts antigos
- [~] consolidar quality gates locais e em CI para frontend e backend crítico
- [~] ampliar cobertura focal de regras de domínio no backend, além de chat e Spec4

## Critérios de sucesso

- onboarding mais curto
- menos arquivos concorrendo como fonte de verdade
- documentação compatível com o código atual
- refatorações futuras divididas em fatias pequenas e verificáveis
