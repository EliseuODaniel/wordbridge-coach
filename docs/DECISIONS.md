# Decisions

## 2026-03-23 - Remover OpenSpec e consolidar governança

Status: aceito

### Contexto

O repositório acumulou documentação paralela e múltiplas versões do estado do produto. OpenSpec e documentos auxiliares passaram a competir com o código real, aumentando a confusão.

### Decisão

- remover OpenSpec do fluxo oficial
- remover instruções específicas de Claude do repositório
- usar `AGENTS.md` como política principal
- usar `docs/` como documentação operacional e arquitetural
- usar skills repo-locais apenas para workflows repetitivos

### Impacto

- menos drift documental
- onboarding mais simples
- menos custo para iniciar a refatoração
- futuras decisões arquiteturais devem ser registradas aqui

## 2026-03-23 - Primeira fatia de refatoracao: setup operacional

Status: aceito

### Contexto

Depois da limpeza do repositório, o setup ainda estava desalinhado: `quick_start.sh` usava comandos e caminhos antigos, e o `docker-compose.yml` mantinha um campo `version` obsoleto.

### Decisão

- alinhar `scripts/quick_start.sh` ao fluxo atual com `docker compose`
- usar `api/scripts/seed_data.py` como script de seed oficial dentro do container da API
- remover o `scripts/seed_data.py` legado da raiz
- registrar o baseline real do frontend, incluindo o fato de que o build passa e o lint ainda falha

### Impacto

- onboarding operacional mais confiável
- menos duplicação de scripts
- primeira frente de debt confirmada ficou explícita: lint do frontend

## 2026-03-23 - Primeiros hotspots da refatoracao

Status: aceito

### Contexto

Depois de validar build, lint e a superfície dos módulos, ficou claro que o maior acoplamento atual está no shell do frontend e em endpoints centrais do backend.

### Decisão

Priorizar as próximas fatias nestas áreas:

- `frontend/src/components/ChatCoachSession.tsx`
- `frontend/src/components/LingvistSession.tsx`
- `frontend/src/components/UserSelection.tsx`
- `frontend/src/components/StudySession.tsx`
- `frontend/src/services/api.ts`
- `api/app/api/api_v1/endpoints/cards.py`
- `api/app/api/api_v1/endpoints/chat.py`
- `api/app/services/card_selection.py`

### Impacto

- as próximas rodadas terão alvo claro
- o frontend fica confirmado como maior foco inicial de debt

## 2026-03-23 - Fatiar debt do frontend por tipo de problema

Status: aceito

### Contexto

O lint do frontend mostrava duas categorias bem diferentes de dívida: problemas estruturais de hooks/efeitos e problemas amplos de tipagem com `any`.

### Decisão

- resolver primeiro os componentes-base com erros de hooks e efeitos
- deixar a próxima fatia focada em tipagem e contratos de API

### Impacto

- a fila do lint caiu de 46 para 41 problemas
- o próximo alvo ficou mais claro: remover `any` de `services/api.ts` e das sessões principais

## 2026-03-23 - Centralizar parsing de erro e retry do frontend

Status: aceito

### Contexto

As telas de estudo e analytics repetiam tratamento de erro com `any`, lógica duplicada de retry e mensagens inconsistentes. Isso poluía o lint e espalhava detalhes de transporte por vários componentes.

### Decisão

- centralizar helpers de erro HTTP em `frontend/src/services/api.ts`
- usar `unknown` como entrada padrão para erros e retries
- reaproveitar os mesmos helpers em sessões principais, analytics, settings de LLM e WebSocket client typing
- manter a refatoração sem mudar comportamento funcional das telas

### Impacto

- `frontend lint` voltou a passar
- o contrato de erro ficou consistente entre componentes
- a próxima rodada pode focar em simplificação estrutural, não mais em ruído básico de tipagem

## 2026-03-23 - Consolidar duplicacao antes de mudar regra de negocio

Status: aceito

### Contexto

Os próximos hotspots do projeto estão em infra local e no fluxo de cards. Antes de alterar comportamento, havia duplicação evidente em `docker-compose.yml`, na resolução do usuário demo e nos lookups de usuário/idioma dentro do serviço de seleção.

### Decisão

- consolidar a base comum dos serviços `llama.cpp` no `docker-compose.yml`
- extrair helpers de lookup de usuário, idioma alvo e card excluído em `api/app/services/card_selection.py`
- centralizar a resolução de `user_id` padrão nos endpoints de cards
- preservar o comportamento atual e tratar esta rodada como refatoração estrutural de baixo risco

### Impacto

- a superfície operacional ficou menor e mais legível
- o backend de cards perdeu parte da duplicação interna
- a próxima fatia pode atacar separação de payload, tradução e seleção com menos ruído
- a validação automática de backend ainda depende de reinstalar `pytest` no ambiente local

## 2026-03-23 - Quebrar o endpoint Lingvist em helpers locais

Status: aceito

### Contexto

Mesmo após a limpeza inicial, o endpoint `next-lingvist` ainda concentrava muitas responsabilidades: lookup das entidades, autofill de tradução, cálculo de microprogresso, geração de áudio e serialização final.

### Decisão

- extrair helpers locais para resolver `memory_stage`, carregar entidades do card e montar URLs de áudio relativas
- encapsular a montagem do payload Lingvist em um helper dedicado dentro de `cards.py`
- manter a regra de seleção intacta nesta rodada

### Impacto

- o fluxo do endpoint ficou mais legível
- a próxima extração pode separar melhor enriquecimento de tradução e serialização de resposta
- a refatoração do backend continua em slices pequenos e verificáveis

## 2026-03-23 - Recuperar o caminho local de testes do backend

Status: aceito

### Contexto

Depois da limpeza do repositório, o backend tinha testes, mas o caminho local para executá-los estava quebrado por uma combinação de ambiente sem `pytest`, conftest preso ao hostname Docker `db_test`, `DEBUG` vazando do ambiente real e runner pouco amigável fora de um venv ativado manualmente.

### Decisão

- criar um `.venv` local em `api/` para rodar testes sem depender do Python global
- fazer `api/tests/conftest.py` aceitar `TEST_DATABASE_URL` e forçar variáveis seguras de teste
- ajustar `api/test-runner.sh` para preferir o `.venv` repo-local, exportar `PYTHONPATH=.` e `DEBUG=false`
- manter a validação focada primeiro na trilha Spec4, onde a refatoração está ativa

### Impacto

- `test_spec4_card_selection.py` voltou a passar localmente
- o runner voltou a ser utilizável sem setup manual excessivo
- a próxima rodada pode expandir testes para outros hotspots com base já estável

## 2026-03-23 - Limpar primeiro o bloco REST do Chat Coach

Status: aceito

### Contexto

O `chat.py` segue como hotspot, mas o trecho WebSocket ainda concentra muita complexidade para uma mudança ampla de uma vez. O bloco REST tinha duplicação mais barata de remover: lookup de usuário/conversa e serialização manual de conversas e mensagens.

### Decisão

- extrair helpers para lookup padronizado de `User` e `ChatConversation`
- extrair serialização de conversa, mensagem e item da listagem
- manter a parte WebSocket fora desta fatia
- corrigir o sanitizer para remover simulação de usuário em bloco único ou multiline no final da resposta

### Impacto

- os endpoints REST de chat ficaram menores e mais consistentes
- a suíte `tests/test_chat_utilities.py` voltou a passar com o comportamento esperado
- a próxima fatia pode focar no loop WebSocket sem carregar o mesmo ruído do bloco REST

## 2026-03-23 - Extrair o pipeline comum de draft feedback

Status: aceito

### Contexto

Após a limpeza do bloco REST, os handlers `handle_draft_update` e `handle_request_autocomplete` ainda repetiam partes da mesma lógica: `micro_eval`, montagem do `draft_feedback`, cache e atualização de payload durante throttle.

### Decisão

- extrair um helper único para avaliar e montar `draft_feedback`
- extrair helpers pequenos para cache e atualização do payload throttled
- adicionar testes utilitários para `_merge_issues` e para o comportamento do feedback throttled

### Impacto

- o fluxo de feedback do Chat Coach ficou mais explícito
- `tests/test_chat_utilities.py` agora cobre mais do contrato local do endpoint
- a próxima fatia pode atacar o loop WebSocket com menos duplicação e menor risco

## 2026-03-23 - Extrair funções puras do handle_user_message

Status: aceito

### Contexto

Mesmo depois da limpeza do REST e do pipeline de draft feedback, `handle_user_message` ainda misturava regras de prompt, configuração de geração, sanitização e fallback de teacher analysis no meio do fluxo principal.

### Decisão

- extrair helpers puros para construir o system prompt de chat
- extrair a configuração padrão de geração e a lista de stop sequences
- extrair a construção do fallback de teacher analysis
- aumentar `tests/test_chat_utilities.py` para cobrir essas funções puras

### Impacto

- o fluxo principal do handler ficou mais legível
- a cobertura local do Chat Coach cresceu sem exigir mocks pesados de WebSocket
- a próxima fatia pode focar em persistência e teacher analysis com menos ruído estrutural

## 2026-03-23 - Extrair persistência e payload de teacher analysis

Status: aceito

### Contexto

Depois da extração das funções puras, `handle_user_message` ainda carregava criação de mensagens, persistência da resposta do assistente e montagem manual do evento `teacher_analysis`.

### Decisão

- extrair helper para criação de `ChatMessage`
- extrair helper para persistir a resposta do assistente e atualizar `conversation.updated_at`
- extrair helper para anexar `teacher_analysis` ao `metadata_json` do `user_message`
- extrair helper para montar o payload websocket de `teacher_analysis`

### Impacto

- o `handle_user_message` perdeu mais um bloco de efeito colateral repetitivo
- a suíte utilitária de chat agora cobre também metadados e payloads de teacher analysis
- a próxima fatia pode focar no streaming e na orquestração final do handler

## 2026-03-23 - Separar payload final e teacher analysis do fluxo principal de chat

Status: aceito

### Contexto

Mesmo após a extração de persistência e metadados, `handle_user_message` ainda concentrava streaming do assistente, montagem do `assistant_done` e a dupla geração/envio de `teacher_analysis` com fallback.

### Decisão

- extrair helper para montar o payload final de `assistant_done`
- extrair helper para encapsular o streaming dos tokens do assistente
- extrair helper para gerar `teacher_analysis` com fallback padronizado
- extrair helper para enviar o evento websocket de `teacher_analysis`
- ampliar `tests/test_chat_utilities.py` com cobertura dessas novas peças isoladas

### Impacto

- o handler principal ficou menor e mais legível
- a lógica de fallback do professor ficou centralizada em um único ponto
- a próxima fatia pode mirar testes de fluxo WebSocket e coordenação final do handler, não mais payloads locais

## 2026-03-23 - Extrair o congelamento de feedback e a preparação da geração

Status: aceito

### Contexto

Depois da separação do `assistant_done` e do `teacher_analysis`, `handle_user_message` ainda misturava a avaliação inicial do texto enviado, a persistência do `user_message` e a montagem dos insumos usados pelo streaming do assistente.

### Decisão

- extrair helper para congelar e enviar o `draft_feedback` da mensagem submetida
- extrair helper para persistir o `user_message`
- extrair helper para montar contexto, prompt e config usados na geração do assistente
- ampliar a suíte utilitária de chat para cobrir o congelamento do feedback

### Impacto

- o começo do fluxo de `handle_user_message` ficou mais linear
- a fronteira entre preparação de entrada e coordenação de efeitos ficou mais clara
- a próxima fatia pode focar com mais precisão em testes de fluxo WebSocket e warnings antigos do backend

## 2026-03-23 - Cobrir o fluxo WebSocket do chat e corrigir persistência JSONB

Status: aceito

### Contexto

Depois das extrações locais do `handle_user_message`, o maior risco restante no Chat Coach deixou de ser legibilidade pura e passou a ser confiança no fluxo real do WebSocket. Ao abrir o primeiro teste integrado, ficou visível também um bug de persistência: o `teacher_analysis` era escrito em `metadata_json` com mutação in-place, o que não era confiável para JSONB.

### Decisão

- adicionar um teste integrado para `user_message -> assistant_stream_token -> assistant_done -> teacher_analysis`
- corrigir `_attach_teacher_analysis_metadata` para sempre reatribuir um novo dict em `metadata_json`
- registrar que as suítes que compartilham o banco de teste devem rodar em série, não em paralelo

### Impacto

- o backend agora cobre um fluxo WebSocket real do Chat Coach
- a persistência do `teacher_analysis` ficou confiável no banco
- a próxima fatia pode focar mais em simplificar coordenação e warnings, não mais só em medo de regressão invisível

## 2026-03-23 - Delegar a finalização do turno e o envio da análise do professor

Status: aceito

### Contexto

Depois do teste WebSocket entrar, o restante de complexidade visível em `handle_user_message` ficou concentrado em duas etapas finais: fechar a resposta do assistente e persistir/enviar a análise do professor. As regras já estavam corretas, mas ainda amarradas diretamente no handler.

### Decisão

- extrair helper para sanitizar, persistir e emitir o `assistant_done`
- extrair helper para persistir `teacher_analysis` válido e emitir o evento correspondente
- ampliar `tests/test_chat_utilities.py` para cobrir essas duas etapas isoladamente

### Impacto

- o fluxo principal de `handle_user_message` ficou menor e mais fácil de ler
- a lógica crítica do fim do turno ficou coberta tanto por testes utilitários quanto por teste integrado de WebSocket
- o próximo ganho mais valioso tende a vir de warnings/tempo e de mais simplificação arquitetural, não de extrações locais pequenas

## 2026-03-23 - Tornar o setup de testes backend mais idempotente

Status: aceito

### Contexto

Ao repetir a trilha de WebSocket em execuções normais, apareceram falhas de setup por resíduos de schema do PostgreSQL, principalmente em tipos enum criados durante `create_all`. O problema não era a lógica do chat, e sim o fixture de banco começar sem limpar restos de rodadas anteriores.

### Decisão

- ajustar o fixture `db` de `api/tests/conftest.py` para executar `drop_all(checkfirst=True)` antes do `create_all`
- manter também o `drop_all(checkfirst=True)` no teardown
- continuar tratando paralelismo no mesmo banco como não suportado, mas deixar a execução serial repetida mais robusta

### Impacto

- o ciclo local de testes ficou mais confiável entre execuções consecutivas
- a trilha de WebSocket pode ser rerrodada em série sem depender de limpeza manual do banco
- a próxima fatia pode voltar a mirar warnings reais do backend com menos ruído de infraestrutura

## 2026-03-23 - Centralizar UTC e reduzir ruído de Pydantic no caminho quente

Status: aceito

### Contexto

Com a trilha de testes mais estável, a próxima fonte de ruído ficou concentrada em dois pontos recorrentes: uso espalhado de tempo UTC em endpoints/serviços centrais e configurações legadas de Pydantic nos schemas mais usados por chat e cards.

### Decisão

- criar um helper compartilhado de tempo UTC em `api/app/core/time.py`
- migrar os módulos quentes de chat, cards, stats, users, seleção e SM-2 para esse helper
- substituir `class Config` por `model_config` nos schemas/configs mais próximos das trilhas críticas já cobertas

### Impacto

- o backend ficou mais consistente no tratamento de tempo UTC
- parte relevante do ruído de warnings caiu nas suítes de utilitários do chat
- a próxima fatia pode atacar warnings residuais restantes e debt estrutural fora do miolo de chat/cards

## 2026-03-23 - Limpar os warnings centrais da trilha de chat

Status: aceito

### Contexto

Depois da centralização inicial de UTC e da migração parcial para Pydantic atual, a trilha de chat ainda deixava três warnings bem objetivos: `declarative_base()` legado, `class Config` restante em schemas importados pelo app e defaults `datetime.utcnow()` vindo da base dos modelos.

### Decisão

- migrar `app/core/database.py` para `sqlalchemy.orm.declarative_base`
- trocar os defaults de `created_at` e `updated_at` da base de modelos para o helper UTC compartilhado
- migrar `api/app/schemas/lingvist.py` e `api/app/schemas/llm_profiles.py` para `model_config`

### Impacto

- `tests/test_chat_utilities.py` ficou sem warnings visíveis
- `tests/integration/test_chat_websocket_flow.py` ficou sem warnings visíveis
- o próximo alvo de warnings pode sair do miolo de chat e mirar o restante do backend com mais foco

## 2026-03-23 - Limpar os warnings visíveis da trilha Spec4

Status: aceito

### Contexto

Depois da limpeza do miolo de chat, a trilha Spec4 ainda mantinha ruído em três pontos: `IN (subquery)` no endpoint de cards, defaults UTC restantes em modelos usados por analytics e fixtures de teste com `datetime.utcnow()`.

### Decisão

- trocar os `IN (subquery)` de `cards.py` para `select(...)` explícito
- migrar os defaults UTC restantes de `WordTheme`, `WordThemeMapping` e `UserDailyStats` para o helper compartilhado
- alinhar os fixtures e asserts da suíte Spec4 ao helper UTC compartilhado

### Impacto

- `tests/integration/test_spec4_card_selection.py` ficou sem warnings visíveis
- a trilha principal de cards ficou mais limpa e menos ruidosa para próximas refatorações
- os warnings residuais restantes agora tendem a estar fora do fluxo crítico já estabilizado

## 2026-03-23 - Reduzir timers fantasmas no StudySession antes de mexer em comportamento

Status: aceito

### Contexto

Depois da estabilização de lint e build do frontend, o `StudySession` ainda concentrava coordenação local de audio, avanço para o próximo card e retries de carregamento. O comportamento estava correto, mas o retry com `setTimeout` ainda ficava solto e podia sobreviver além do ciclo de vida do componente.

### Decisão

- manter a regra de negócio do modo de estudo inalterada nesta fatia
- extrair helpers locais para tocar audio e para limpar/agendar timers
- rastrear explicitamente tanto o timer de avanço do próximo card quanto o timer de retry do carregamento

### Impacto

- o `StudySession` ficou mais previsível ao desmontar ou reinicializar
- o risco de retry fantasma caiu sem introduzir nova abstração global
- a próxima fatia de frontend pode focar em coordenação de sessão e não mais em housekeeping de timers

## 2026-03-23 - Limpar coordenação local no ChatCoachSession antes de extrações maiores

Status: aceito

### Contexto

Mesmo com o backend de chat mais estável, o `ChatCoachSession` ainda espalhava housekeeping de UI em vários pontos: cleanup do autocomplete, refocus do composer e desconexão do WebSocket apareciam repetidos no componente.

### Decisão

- extrair helpers locais para limpar timeout de autocomplete, focar o textarea e desconectar o socket
- manter o fluxo funcional do Chat Coach inalterado nesta fatia
- ajustar a ordem das declarações para manter os hooks consistentes e o lint limpo

### Impacto

- o componente ficou mais linear e menos propenso a esquecer cleanup em fluxos de saída
- a próxima fatia do frontend pode mirar responsabilidades maiores em vez de housekeeping repetido
- `frontend lint` e `frontend build` seguiram verdes após a mudança

## 2026-03-23 - Consolidar operações repetidas no LingvistSession antes de mexer em UX

Status: aceito

### Contexto

Depois das fatias em `StudySession` e `ChatCoachSession`, o maior ruído restante no frontend estava no `LingvistSession`: reset de rodada, preload de audio e playback manual ainda apareciam como blocos repetidos e pouco coesos.

### Decisão

- extrair helper de reset da rodada para reaproveitar a limpeza de estado antes de carregar o próximo card
- centralizar o preload de audio do card
- centralizar o playback manual de word/sentence audio em um helper único

### Impacto

- o componente ficou menor e mais previsível sem alterar a mecânica do modo Lingvist
- a próxima simplificação de frontend pode focar no shell geral ou na separação entre modos, não mais em housekeeping local
- `frontend lint` e `frontend build` seguiram verdes após a mudança

## 2026-03-23 - Tirar regra incidental de borda do endpoint de cards antes de mexer no submit_answer

Status: aceito

### Contexto

Depois de extrair o payload Lingvist, `cards.py` ainda misturava duas responsabilidades que não são regra de negócio principal: resolver o `demo` user quando `user_id` vinha omitido e serializar o payload comum de `CardResponse`. Esse miolo aumentava o peso do endpoint mesmo sem tocar na seleção de cards nem no `submit_answer`.

### Decisão

- extrair a resolução de `user_id` padrão para `api/app/services/card_response_service.py`
- extrair a serialização comum de `CardResponse` para o mesmo serviço
- manter wrappers compatíveis em `cards.py` para preservar contrato e reduzir risco da fatia
- validar com uma suíte unitária nova e com a integração Spec4 já existente

### Impacto

- `cards.py` ficou menor e mais focado em orquestração de endpoint
- a próxima fatia pode atacar `submit_answer` ou a serialização restante com menos ruído incidental
- o quality gate agora cobre também `tests/test_card_response_service.py`

## 2026-03-23 - Tirar o ciclo base de answer submission de cards.py antes de rever regras de progressão

Status: aceito

### Contexto

Mesmo depois da extração de `CardResponse`, o `submit_answer` ainda carregava um bloco grande de efeito colateral: carregar ou criar `UserCardState`, montar `ReviewEvent`, aplicar o resultado do SM-2 de volta no estado e serializar o `AnswerResponse`. Isso deixava o endpoint pesado demais para a próxima rodada de simplificação.

### Decisão

- extrair esse ciclo base para `api/app/services/card_answer_service.py`
- manter no endpoint apenas a validação principal, os updates agregados e a orquestração de progressão
- preservar wrappers compatíveis para reduzir risco da fatia
- validar com uma suíte unitária nova e com a integração Spec4 já existente

### Impacto

- `submit_answer` ficou menor e mais legível
- a próxima fatia pode focar em progressão, stats ou commit/orquestração, sem precisar reler boilerplate de estado/resposta
- o quality gate agora cobre também `tests/test_card_answer_service.py`

## 2026-03-23 - Tirar a orquestração agregada de progresso de cards.py antes de revisar seleção

Status: aceito

### Contexto

Depois da extração do ciclo base de `submit_answer`, o endpoint ainda conhecia detalhes demais de atualização agregada: stats diárias, rolling accuracy, relearn do modo Lingvist, stats por tema e avanço da progressão Spec4. Esse bloco já não era mais validação central nem contrato HTTP, só coordenação de domínio espalhada.

### Decisão

- extrair esse bloco para `api/app/services/card_progress_service.py`
- manter wrappers compatíveis em `cards.py` para reduzir risco da fatia
- concentrar no endpoint apenas a validação principal, a atualização do estado SM-2 e o commit/resposta
- validar com suíte unitária focal e com a integração Spec4 já existente

### Impacto

- `submit_answer` ficou mais próximo de uma borda fina
- a próxima fatia pode focar em commit/orquestração restante ou em simplificar `next-spec4`
- o quality gate agora cobre também `tests/test_card_progress_service.py`

## 2026-03-23 - Consolidar a submissão de resposta em um serviço único antes de simplificar next-spec4

Status: aceito

### Contexto

Mesmo depois das extrações anteriores, `submit_answer` ainda concentrava a costura entre validação do card, avaliação da resposta, cálculo do SM-2, aplicação das atualizações e commit. O endpoint já tinha pouca regra própria, mas ainda exigia leitura longa para entender o fluxo completo.

### Decisão

- criar `api/app/services/card_submission_service.py` como orquestrador principal da submissão
- deixar `cards.py` apenas delegar para esse serviço e traduzir exceções HTTP/ValueError como antes
- manter as extrações anteriores (`card_answer_service.py` e `card_progress_service.py`) como blocos reutilizáveis abaixo desse orquestrador
- validar com suíte unitária própria, Spec4 e integração de theme stats

### Impacto

- `cards.py` ficou mais próximo do padrão de endpoint fino já aplicado em `chat.py`
- a próxima fatia pode sair do `submit_answer` e focar em `next-spec4` ou em simplificação de serialização/contexto
- o quality gate agora cobre também `tests/test_card_submission_service.py`

## 2026-03-23 - Tirar a seleção/serialização de next-spec4 de cards.py antes de mexer no Lingvist

Status: aceito

### Contexto

Depois de afinar `submit_answer`, o maior bloco restante em `cards.py` passou a ser `next-spec4`: resolver usuário, chamar `CardSelectionService`, tratar ausência de contexto e montar manualmente o `CardResponse`. Era um endpoint menor do que antes, mas ainda destoava do padrão fino já aplicado em chat e no próprio fluxo de answer submission.

### Decisão

- extrair a seleção e a serialização de `next-spec4` para `api/app/services/card_spec4_service.py`
- manter o endpoint apenas delegando ao novo serviço e traduzindo exceções como antes
- validar com suíte unitária própria, Spec4 e integração de theme stats

### Impacto

- `cards.py` ficou ainda mais coeso como camada de borda
- a próxima fatia pode focar em `next-lingvist` ou em reduzir wrappers legados restantes
- o quality gate agora cobre também `tests/test_card_spec4_service.py`

## 2026-03-23 - Tirar a orquestração de next-lingvist de cards.py antes de fechar o endpoint

Status: aceito

### Contexto

Depois da extração de `next-spec4`, o maior bloco remanescente em `cards.py` era `next-lingvist`: resolver usuário, aplicar override temporário de mix, chamar a seleção, montar o payload enriquecido e fazer commit de efeitos colaterais de autofill.

### Decisão

- extrair esse fluxo para `api/app/services/card_lingvist_service.py`
- manter o endpoint apenas delegando e traduzindo exceções como antes
- preservar o payload enriquecido em `lingvist_payload_service.py` como camada separada abaixo do novo orquestrador
- validar com suíte unitária própria, `test_lingvist_payload_service.py` e regressão de Spec4

### Impacto

- `cards.py` ficou muito mais próximo de uma camada de borda fina em todos os endpoints principais
- a próxima fatia pode focar em wrappers/resíduos restantes ou sair de `cards.py`
- o quality gate agora cobre também `tests/test_card_lingvist_service.py`

## 2026-03-23 - Centralizar a troca entre modos no App em vez de recarregar a página

Status: aceito

### Contexto

Mesmo depois das simplificações locais das sessões, `StudySession` e `LingvistSession` ainda alternavam entre si com links `href` que recarregavam a aplicação inteira. Isso funcionava, mas mantinha a navegação entre modos dependente de reload e espalhava a responsabilidade de troca fora do shell principal.

### Decisão

- fazer a troca entre `spec4` e `lingvist` passar por `App.tsx`
- preservar a preferência de modo ao sair da sessão, em vez de forçar retorno para `spec4`
- trocar os links internos por callbacks explícitos de mudança de modo

### Impacto

- o shell do frontend ficou mais coerente com uma SPA React
- a navegação entre modos perdeu um reload completo desnecessário
- a fase atual fecha com a separação entre modos mais limpa do que no baseline inicial

## 2026-03-23 - Preparar o repositório para uso mais forte com Codex

Status: aceito

### Contexto

Depois da limpeza e da refatoração principal, o repositório já tinha uma boa base documental, mas ainda faltavam peças práticas para um uso mais forte com Codex no dia a dia: instruções por área, skills mais específicas, guia oficial de setup e quality gates versionados.

### Decisão

- adicionar `AGENTS.md` específicos para `api/`, `frontend/`, `tts/` e `tests/e2e/`
- adicionar skills repo-locais para readiness de Codex, fatias de endpoint backend e fatias de sessão frontend
- documentar setup recomendado de Codex e MCP em `docs/CODEX_SETUP.md`
- adicionar um workflow inicial de qualidade em `.github/workflows/quality.yml`

### Impacto

- o repositório fica mais preparado para uso repetível com Codex
- o onboarding técnico do agente fica mais claro por área
- quality gates deixam de depender apenas de disciplina manual local

## 2026-03-23 - Remover hardcodes de idioma da progressão antes de ampliar features multilíngues

Status: aceito

### Contexto

Mesmo após a estabilização geral do baseline, partes do `VocabularyProgressionService` ainda assumiam inglês de forma fixa. Isso era especialmente perigoso porque o produto já expõe seleção de idioma e perfis com língua alvo diferente.

### Decisão

- resolver o idioma alvo do usuário dentro do serviço de progressão
- usar esse idioma nas consultas de próximo rank, revisão e avanço do prefixo contíguo
- adicionar testes focados para proteger esse comportamento

### Impacto

- o domínio de progressão ficou mais coerente com a proposta multilíngue
- uma classe de bug silencioso entre usuários de idiomas diferentes deixou de depender de comportamento implícito
- a próxima rodada pode ampliar regras multilíngues sobre uma base menos frágil

## 2026-03-23 - Reduzir detalhes operacionais no loop WebSocket do Chat Coach

Status: aceito

### Contexto

O loop WebSocket de `chat.py` já tinha melhorado bastante, mas ainda carregava detalhes de lookup, setup de providers, inicialização de throttle, dispatch de evento e payloads de erro no mesmo bloco.

### Decisão

- extrair helpers de setup da conversa WebSocket
- extrair helper de carregamento de providers por conversa
- padronizar payload de erro WebSocket
- extrair o dispatch principal de eventos para um helper dedicado

### Impacto

- o loop WebSocket ficou mais legível e mais fácil de continuar quebrando em slices
- erros e setup ficaram mais consistentes
- a próxima fatia de chat pode focar em separar orquestração restante, não em housekeeping do loop

## 2026-03-23 - Fazer teacher analysis usar contexto real do aluno quando disponível

Status: aceito

### Contexto

O Chat Coach já tinha um helper para construir contexto apenas com mensagens do aluno, mas a `teacher_analysis` ainda dependia principalmente de `session_summary`. Isso deixava uma fonte de contexto mais genérica do que o histórico real já persistido no banco.

### Decisão

- encapsular o turno `user_message` em um helper próprio
- construir o contexto da `teacher_analysis` a partir das mensagens do aluno quando houver histórico
- manter `session_summary` apenas como fallback para preservar comportamento em conversas sem histórico persistido

### Impacto

- a orquestração de `handle_user_message` ficou menor
- a análise pedagógica do professor ficou mais coerente com o que o aluno realmente escreveu
- os testes utilitários e o fluxo integrado de WebSocket passaram a proteger esse comportamento novo

## 2026-03-23 - Resolver dependências da sessão WebSocket de chat em um runtime dedicado

Status: aceito

### Contexto

Mesmo depois das extrações anteriores, o endpoint WebSocket ainda precisava resolver conversa, providers e tracking de throttle no próprio corpo do handler. Isso deixava o setup da sessão espalhado e pouco reutilizável.

### Decisão

- introduzir um runtime dedicado para a sessão WebSocket do Chat Coach
- concentrar resolução de conversa, providers e estado inicial de throttle nesse runtime
- manter o comportamento externo do endpoint igual nesta fatia

### Impacto

- o endpoint ficou mais próximo de um orchestrator fino
- o próximo passo pode mover esse runtime para `services/` com menos risco
- a evolução do Chat Coach ganhou uma fronteira interna mais clara

## 2026-03-23 - Remover placeholders aleatórios da seleção de perfil

Status: aceito

### Contexto

`UserSelection.tsx` ainda mostrava stats aleatórias e assumia idioma/meta padrão em pontos onde o backend já tinha ou podia ter dados reais. Isso passava uma sensação de produto provisório, mesmo com a base já bem mais madura.

### Decisão

- fazer o backend de usuários devolver `target_language` e `word_goal_rank`
- fazer o frontend carregar stats reais por perfil quando disponíveis
- preservar fallback seguro para zero quando uma consulta de stats falhar

### Impacto

- a seleção de perfil ficou mais honesta e previsível
- o frontend perdeu um dos placeholders mais visíveis do produto
- o contrato de usuários ficou mais útil para futuras evoluções da tela de onboarding/perfil

## 2026-03-23 - Mover runtime e roteamento base do WebSocket de chat para services

Status: aceito

### Contexto

Mesmo após várias extrações locais, `api/app/api/api_v1/endpoints/chat.py` ainda acumulava inicialização de sessão WebSocket, lookup de conversa, carregamento de providers e roteamento de eventos. Isso mantinha o endpoint mais pesado do que o ideal para uma fronteira HTTP/WS.

### Decisão

- criar `api/app/services/chat_runtime_service.py` para concentrar:
  - runtime resolvido da sessão WebSocket
  - carregamento de providers por conversa
  - montagem do payload padrão de erro WS
  - roteamento base de eventos WS
- manter `chat.py` responsável pelos handlers de domínio e pelo endpoint em si
- adicionar cobertura unitária própria para essa nova fronteira e colocá-la no quality gate

### Impacto

- o endpoint de chat fica mais fino e mais próximo de uma camada de borda
- a orquestração WebSocket ganha uma fronteira interna testável fora do endpoint
- o próximo corte pode focar em mover mais coordenação de turno ou isolar melhor integrações externas sem reabrir o mesmo acoplamento estrutural

## 2026-03-23 - Mover a coordenação do turno user_message para services

Status: aceito

### Contexto

Mesmo com o runtime do WebSocket já extraído, `chat.py` ainda carregava a sequência completa do turno `user_message`: congelamento de feedback, persistência da mensagem do aluno, geração da resposta, finalização do turno e emissão de `teacher_analysis`.

### Decisão

- criar `api/app/services/chat_turn_service.py` para concentrar a orquestração do turno `user_message`
- manter os helpers já validados em `chat.py` por enquanto, injetando-os como dependências explícitas
- adicionar um teste focal de ordem/orquestração e incluir essa suíte no quality gate

### Impacto

- `chat.py` perde mais uma responsabilidade de coordenação sem exigir uma migração brusca dos helpers internos
- a sequência do turno fica testável como unidade própria
- o próximo corte pode atacar `draft_update` e `request_autocomplete`, ou então isolar melhor integrações externas como LLM e LanguageTool

## 2026-03-23 - Mover a orquestração de draft_update e request_autocomplete para services

Status: aceito

### Contexto

Depois de extrair o runtime WebSocket e o turno `user_message`, os handlers de `draft_update` e `request_autocomplete` ainda mantinham throttle, cache, ghost suggestion e envio de payload no endpoint.

### Decisão

- criar `api/app/services/chat_draft_service.py` para concentrar:
  - decisão de throttle do micro-eval
  - reuso de feedback cacheado
  - orquestração do autocomplete com ghost suggestion
- manter a lógica de avaliação/mapeamento de feedback em `chat.py` por enquanto, injetada como dependência
- adicionar testes focais e incluir a nova suíte no quality gate

### Impacto

- `chat.py` fica mais próximo de um conjunto de handlers finos
- draft feedback e autocomplete ganham uma fronteira de serviço pequena e testável
- o próximo corte pode mirar a extração dos helpers de feedback/contexto ou o isolamento das integrações LLM/LanguageTool

## 2026-03-23 - Mover o feedback draft e as integrações externas do Chat Coach para services

Status: aceito

### Contexto

Mesmo depois das extrações de runtime, draft orchestration e turno `user_message`, `chat.py` ainda concentrava montagem de `draft_feedback`, chamada de `micro_eval`, merge com LanguageTool e congelamento do feedback enviado no submit.

### Decisão

- criar `api/app/services/chat_feedback_service.py` para concentrar:
  - montagem de `draft_feedback`
  - merge de issues heurísticas com LanguageTool
  - avaliação de draft via `micro_eval`
  - congelamento do feedback enviado no submit
- manter em `chat.py` apenas wrappers finos para adaptar config/env e preservar compatibilidade local
- adicionar cobertura dedicada e incluir a nova suíte no quality gate

### Impacto

- o endpoint de chat perde mais uma camada de detalhe técnico e de integração externa
- LanguageTool e `micro_eval` passam a ter uma fronteira mais clara para futuras trocas ou mocks
- o próximo corte pode focar no restante dos helpers de contexto/persistência ou em expandir testes de integração do fluxo completo

## 2026-03-23 - Mover a construção de contexto do Chat Coach para services

Status: aceito

### Contexto

Depois de extrair runtime, draft orchestration, feedback e turno `user_message`, `chat.py` ainda carregava diretamente a construção de contexto para geração do assistente e para `teacher_analysis`. Isso mantinha queries e detalhes de montagem ainda concentrados no endpoint.

### Decisão

- criar `api/app/services/chat_context_service.py` para concentrar:
  - contexto cronológico de chat
  - contexto apenas do aluno para `teacher_analysis`
  - montagem dos insumos de geração
  - fallback do contexto do professor para `session_summary`
- manter wrappers finos em `chat.py` para preservar compatibilidade com os testes locais existentes
- adicionar cobertura dedicada e incluir a nova suíte no quality gate

### Impacto

- `chat.py` perde mais um bloco de queries e montagem de contexto
- a fronteira de contexto do Chat Coach fica testável fora do endpoint
- o próximo corte pode focar em persistência/eventos ou em cobertura mais integrada do fluxo completo

## 2026-03-23 - Mover persistência e entrega final do Chat Coach para services

Status: aceito

### Contexto

Depois das extrações anteriores, `chat.py` ainda acumulava persistência de mensagens, construção dos payloads finais de `assistant_done` e `teacher_analysis`, e envio desses eventos ao cliente. Isso mantinha efeitos colaterais importantes ainda centralizados no endpoint.

### Decisão

- criar `api/app/services/chat_delivery_service.py` para concentrar:
  - persistência das mensagens do usuário e do assistente
  - atualização de metadados com `teacher_analysis`
  - construção dos payloads finais
  - envio do evento de `teacher_analysis`
  - finalização do turno do assistente com sanitização injetada
- manter wrappers finos em `chat.py` para preservar compatibilidade com os testes locais
- adicionar cobertura dedicada e incluir a nova suíte no quality gate

### Impacto

- `chat.py` perde mais uma faixa de efeitos colaterais diretos
- persistência e entrega final do Chat Coach passam a ter fronteira própria e testável
- o próximo corte pode focar no restante dos helpers puros do endpoint ou no endurecimento da cobertura integrada do fluxo completo

## 2026-03-23 - Mover os helpers puros do Chat Coach para services

Status: aceito

### Contexto

Depois das extrações de runtime, draft, feedback, contexto e delivery, `chat.py` ainda mantinha alguns helpers puros importantes: prompt do tutor, stop sequences, config de geração, fallback de `teacher_analysis` e sanitização da resposta do assistente.

### Decisão

- criar `api/app/services/chat_text_service.py` para concentrar:
  - prompt do tutor
  - stop sequences e config de geração
  - fallback de `teacher_analysis`
  - sanitização da resposta do assistente
- manter wrappers finos em `chat.py` para preservar compatibilidade com os testes locais
- adicionar cobertura dedicada e incluir a nova suíte no quality gate

### Impacto

- `chat.py` fica muito mais próximo de uma camada adaptadora de borda
- os helpers puros ganham uma fronteira própria e testável fora do endpoint
- o próximo corte pode focar no bloco REST/serialização ou em ampliar cobertura integrada do fluxo completo

## 2026-03-23 - Mover lookup e serialização REST do Chat Coach para services

Status: aceito

### Contexto

Depois das extrações de runtime, draft, feedback, contexto, delivery e texto, `chat.py` ainda mantinha lookup de usuário/conversa e serialização do bloco REST. Isso era o restante mais evidente do acoplamento entre roteamento e detalhes de payload no endpoint.

### Decisão

- criar `api/app/services/chat_rest_service.py` para concentrar:
  - lookup padronizado de usuário e conversa
  - serialização de conversa e mensagem
  - montagem do item de listagem com `message_count`
- manter wrappers finos em `chat.py` para preservar compatibilidade com os testes e com os chamadores locais
- adicionar cobertura dedicada e incluir a nova suíte no quality gate

### Impacto

- `chat.py` fica ainda mais próximo de um roteador/adaptador fino
- o bloco REST do Chat Coach ganha fronteira própria e testável
- o próximo corte natural já pode sair de `chat.py` e voltar para outros hotspots do backend, como `cards.py` e `card_selection.py`

## 2026-03-23 - Mover o enriquecimento Lingvist de cards para services

Status: aceito

### Contexto

Depois de estabilizar o Chat Coach, o próximo hotspot confirmado voltou a ser `cards.py`. A parte de enriquecimento Lingvist ainda misturava lookup de entidades, geração de URLs de áudio, micro-progress e transformação do payload no próprio endpoint.

### Decisão

- criar `api/app/services/lingvist_payload_service.py` para concentrar:
  - lookup de entidades do card Lingvist
  - resolução de `memory_stage` e idioma alvo
  - geração de URLs de áudio relativas
  - montagem de `grammar_tag_pt`, tradução e `micro_progress`
  - payload final `LingvistCardResponse`
- manter wrappers finos em `cards.py` para preservar compatibilidade
- adicionar cobertura dedicada e incluir a nova suíte no quality gate

### Impacto

- `cards.py` perde uma faixa relevante de montagem de payload e enrichment
- a próxima fatia pode focar no fluxo de `submit_answer` ou em serialização comum dos cards com menos ruído estrutural
