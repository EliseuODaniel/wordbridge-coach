# Decisions

## 2026-04-24 - Priorizar confiabilidade do runtime local antes de novas features

Status: aceito

### Contexto

Durante o teste manual no navegador, o fluxo `Create Profile` parecia não fazer nada. A causa imediata era operacional: o banco local havia ficado fora do ar e a API retornava `500`. A segunda causa era de UX: o frontend registrava o erro no console, mas não mostrava feedback visível ao usuário.

Na mesma rodada, o frontend containerizado também expôs uma incoerência de perfil: o stack padrão dizia funcionar com `db/api/frontend`, mas o Nginx tentava resolver o upstream `tts` no startup, mesmo com o perfil `audio` desligado.

O primeiro boot em volume novo também expôs que `scripts/init.sql` criava índices antes das migrations Alembic criarem as tabelas. Além disso, a imagem da API trouxe dependências Torch/CUDA no caminho padrão, tornando o build inicial pesado demais para um smoke simples.

### Decisão

- tratar `db/api/frontend` como contrato obrigatório do runtime padrão
- manter `audio` e `ai` como perfis opcionais reais, sem exigir seus serviços no startup do frontend
- manter `scripts/init.sql` limitado a extensões/permissões; schema e índices pertencem às migrations
- mostrar erro visível no fluxo de perfil quando criação, listagem, edição ou remoção falhar
- criar skill repo-local para triagem de runtime local
- priorizar uma trilha curta de smoke local antes de novas features grandes
- separar ou explicitar dependências pesadas de NLP/LLM para que o runtime base continue viável

### Impacto

- problemas de infraestrutura local deixam de parecer botões quebrados sem explicação
- o onboarding fica mais honesto: o stack padrão precisa funcionar sem TTS e sem LLM
- próximos ajustes em compose, Nginx, startup da API ou scripts de setup devem validar runtime real, não apenas configuração estática
- futuras otimizações de plataforma devem mirar primeiro em build/cache/dependências da API antes de expandir recursos de IA local

## 2026-04-24 - Manter runtime base da API leve e avaliação pedagógica determinística

Status: aceito

### Contexto

O smoke local mostrou que uma validação simples do stack padrão podia gastar vários minutos instalando dependências de tradução offline puxadas por Argos/Torch/CUDA. Isso torna onboarding, CI e debug local mais lentos do que o necessário para o produto principal.

Ao mesmo tempo, os sinais pedagógicos (`pedagogical_metrics`, `lesson_frame` e `learning_context`) passaram a influenciar a experiência entre Chat Coach, Spec4 e Lingvist. Sem fixtures determinísticas, qualquer ajuste de heurística poderia mudar a política pedagógica de forma silenciosa.

### Decisão

- remover Argos Translate do runtime base da API
- manter `api/requirements-argos.txt` como extra opcional via `INSTALL_ARGOS=true`
- manter `api/requirements-test.txt` e `api/requirements-dev.txt` separados do runtime de produção
- adicionar `scripts/smoke_local.sh` como smoke oficial do stack padrão
- adicionar testes determinísticos para cenários de suporte, equilíbrio e aceleração pedagógica
- migrar checks de startup da API para `lifespan`, mantendo a função `run_startup_checks()` testável

### Impacto

- o build padrão da API deixa de carregar a árvore pesada de Argos/Torch/CUDA
- tradução offline continua possível, mas passa a ser escolha explícita
- mudanças futuras nos sinais pedagógicos precisam preservar expectativas claras de retenção, pressão de review, pacing e próximo modo recomendado
- a operação da API fica alinhada ao ciclo de vida atual do FastAPI, sem depender de `@app.on_event("startup")`

## 2026-04-22 - Renomear o produto para WordBridge Coach e manter identificadores operacionais legados

Status: aceito

### Contexto

O nome `FillTheWord` descrevia razoavelmente o MVP original focado em lacunas, mas deixou de representar o escopo atual do produto. Hoje o repositório combina estudo principal com cards, modo estilo Lingvist, Chat Coach com LLM local, TTS e contexto pedagógico compartilhado entre modos.

Ao mesmo tempo, o ambiente local já validado ainda depende de identificadores operacionais como `filltheword` e `filltheword_test` em banco e defaults internos.

### Decisão

- adotar `WordBridge Coach` como nome oficial do produto e do repositório público
- atualizar branding visível, metadata das aplicações, documentação oficial, dados demo e testes que validam esse texto
- manter, por enquanto, identificadores operacionais legados como nomes de banco e alguns defaults/caminhos locais já validados

### Impacto

- o nome público passa a refletir melhor o produto multimodal atual
- onboarding, README, UI e GitHub ficam alinhados com o escopo real do projeto
- evitamos uma migração desnecessária nos identificadores de banco e defaults internos, preservando compatibilidade com o ambiente já validado

## 2026-04-23 - Fortalecer configuração da API sem bloquear desenvolvimento local

Status: em andamento

### Contexto

Havia sinais de que a API ainda carecia de validações de operação mais claras (secret defaults, debug/envos e mensagens de debug no fluxo de produção), enquanto `quick_start.sh` ainda trazia texto legado no contrato com o usuário.

### Decisão

- tornar o `main.py` sensível a problemas de configuração na inicialização
- adicionar validações de configuração em `api/app/core/config.py` com modo estrito opcional (`STRICT_CONFIG`)
- corrigir mensagens de `quick_start.sh` para branding atual e permitir alias de porta legado/novo via `FTW_DB_PORT` e `WORDBRIDGE_DB_PORT`
- substituir `print` de debug remanescentes por `logger.debug` em pontos de backend ativos
- consolidar `.env` com variáveis alinhadas ao runtime (`DEBUG`, `SECRET_KEY`, `ENVIRONMENT`, `STRICT_CONFIG`)

### Impacto

- o ambiente de desenvolvimento continua funcionando com defaults simples, mas com trilha de risco explícita quando a configuração não está adequada
- a API passa a registrar avisos no startup e pode falhar antes de aceitar tráfego se `STRICT_CONFIG=true` em ambiente não-local
- reduzimos o acoplamento de mensagens de debug com stdout de produção, deixando os logs mais úteis

## 2026-04-21 - Tornar adaptação pedagógica explícita e guiada por sinais reais

Status: aceito

### Contexto

Depois da introdução de `pedagogical_state`, `lesson_frame` adaptativo e `learning_context` compartilhado, a trilha pedagógica principal ainda dependia demais de heurísticas textuais simples. Faltavam sinais explícitos de retenção, pressão de review, pacing e prontidão por modo para orientar Chat Coach, Spec4 e Lingvist com a mesma base.

### Decisão

- derivar `pedagogical_metrics` a partir de `UserCardState`, `ReviewEvent` e `UserSessionStats`
- persistir esses sinais dentro de `student_profile_json` e projetá-los em `lesson_frame_json.diagnostics`
- expor uma projeção compacta desses sinais em `learning_context` para `Spec4` e `Lingvist`
- usar esses sinais também para calibrar `determine_scaffolding_level`, `build_chat_system_prompt` e `get_lingvist_difficulty_profile`
- estabilizar o E2E do Lingvist com um seletor explícito (`data-testid="lingvist-inline-input"`) em vez de depender de um `input[type="text"]` genérico

### Impacto

- o Chat Coach passou a usar contexto mais rico e coerente em prompts, memória longitudinal e sidebar
- `lesson_frame` e `learning_context` ficaram auditáveis sem endpoint novo de analytics
- o perfil Lingvist agora desacelera ou acelera com sinais reais de retenção e carga de review
- o E2E focal deixou de depender de um seletor ambíguo que confundia o campo de criação de perfil com o input inline do card

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

## 2026-04-21 - Reusar estado pedagógico explícito entre Chat Coach, Spec4 e Lingvist

Status: aceito

### Contexto

A memória longitudinal do Chat Coach já existia, mas ainda estava implícita demais: o `student_profile_json` não carregava um estado pedagógico suficientemente explícito, o `lesson_frame_json` não era recalculado de forma clara a cada turno e os modos `Spec4` e `Lingvist` não reaproveitavam esse contexto.

Além disso, o repositório já possuía a tabela `chat_lesson_history`, criada em migration anterior, mas ela seguia subutilizada.

### Decisão

- tornar `pedagogical_state` parte explícita do `student_profile_json`
- recalcular `lesson_frame_json` a cada `teacher_analysis`, incluindo `learning_goal`, `expected_intent`, `primary_focus`, `lesson_stage` e `success_criteria`
- persistir snapshots do `lesson_frame` em `chat_lesson_history` em vez de criar nova tabela
- estender o evento WebSocket `teacher_analysis` para devolver o `lesson_frame` atualizado
- projetar um `learning_context` compacto para `Spec4` e `Lingvist`, mantendo o frontend desacoplado da heurística interna completa

### Impacto

- o estado pedagógico deixou de depender só de heurísticas escondidas no prompt ou no frontend
- Chat Coach, Spec4 e Lingvist agora compartilham a mesma memória pedagógica de forma observável
- analytics futuros podem usar `chat_lesson_history` para medir evolução de foco e objetivo entre turnos
- a próxima camada de melhoria sai de refatoração de contrato e entra em calibração/eval de heurísticas

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

## 2026-03-23 - Tirar a montagem de contexto comum de CardSelectionService antes de revisar heurísticas

Status: aceito

### Contexto

Depois de afinar os endpoints de `cards.py`, o maior bloco utilitário remanescente passou a ser `_build_card_context` em `CardSelectionService`. Ele misturava criação automática de `Card`, escolha/criação de deck padrão, idioma alvo do usuário e montagem do payload retornado para Spec4 e Lingvist.

### Decisão

- extrair esse bloco para `api/app/services/card_selection_payload_service.py`
- manter `CardSelectionService` apenas delegando a criação/garantia do card e a serialização comum
- validar com suíte unitária própria e regressões de Spec4/themes

### Impacto

- `CardSelectionService` ficou mais focado nas heurísticas de seleção
- a próxima fatia pode mirar regras de mistura, backlog e relearn, não mais payload/housekeeping
- o quality gate agora cobre também `tests/test_card_selection_payload_service.py`

## 2026-03-23 - Tirar as regras de mistura de CardSelectionService antes de revisar queries

Status: aceito

### Contexto

Depois da extração do payload comum, `CardSelectionService` ainda concentrava o cálculo de share de cards novos, backlog e a decisão de tentar novo card em `spec4` e `lingvist`. Essas regras já eram quase puras, mas continuavam misturadas com a mecânica de buscar candidatos.

### Decisão

- extrair essas regras para `api/app/services/card_selection_policy_service.py`
- manter `CardSelectionService` apenas consultando a política e executando os fluxos de busca
- validar com suíte unitária própria e regressões de Spec4/themes

### Impacto

- `CardSelectionService` ficou mais focado na orquestração de candidatos
- a próxima fatia pode entrar nas queries de review/relearn ou nos fallbacks, sem carregar junto regras de política
- o quality gate agora cobre também `tests/test_card_selection_policy_service.py`

## 2026-03-23 - Tirar as queries de review/relearn de CardSelectionService antes de revisar fallbacks

Status: aceito

### Contexto

Depois da extração do payload e da política de mistura, `CardSelectionService` ainda concentrava boa parte das queries SQL de review, relearn, backlog e anti-repetição. Esse miolo já estava estável, mas ainda misturava acesso a banco com a orquestração da seleção.

### Decisão

- extrair essas queries para `api/app/services/card_selection_query_service.py`
- manter `CardSelectionService` apenas coordenando os fluxos e consumindo os resultados
- validar com suíte unitária própria e regressões de Spec4/themes

### Impacto

- `CardSelectionService` ficou mais próximo de um orquestrador de domínio
- a próxima fatia pode focar nos fallbacks finais e em métodos legados como `_get_word_by_rank`
- o quality gate agora cobre também `tests/test_card_selection_query_service.py`

## 2026-03-23 - Tirar fallbacks e legado de rank de CardSelectionService antes de encerrar o hotspot

Status: aceito

### Contexto

Depois da extração de payload, política e queries, o que sobrava de mais histórico em `CardSelectionService` era o fallback `_get_any_eligible_card` e o método legado `_get_word_by_rank`. Ambos misturavam query, gating e compatibilidade num mesmo ponto.

### Decisão

- extrair esses comportamentos para `api/app/services/card_selection_fallback_service.py`
- manter `CardSelectionService` só coordenando o fluxo e delegando a parte de fallback/legado
- validar com suíte unitária própria e regressões de Spec4/themes

### Impacto

- `CardSelectionService` ficou bem mais próximo do fechamento como hotspot
- a próxima fatia pode ser de limpeza final, remoção de legado morto ou revisão de `record_answer`
- o quality gate agora cobre também `tests/test_card_selection_fallback_service.py`

## 2026-03-23 - Extrair a atualização de progressão Spec4 do CardSelectionService

Status: aceito

### Contexto

Depois das extrações de payload, política, queries e fallback, o que ainda restava de mais incidental em `CardSelectionService` era `record_answer`. Esse método já não participava da seleção em si; ele só resolvia idioma alvo, buscava rank em `WordFrequency` e atualizava a progressão contígua para respostas corretas.

### Decisão

- extrair esse fluxo para `api/app/services/card_selection_progress_service.py`
- fazer `card_progress_service` chamar o novo serviço diretamente, em vez de depender de `CardSelectionService`
- remover de `CardSelectionService` os wrappers legados realmente mortos, incluindo `_get_recent_word_ids`, `_get_word_by_rank` e `record_answer`

### Impacto

- `CardSelectionService` ficou mais coerente com o próprio nome e mais próximo de um orquestrador puro de seleção
- a atualização de progressão Spec4 ganhou cobertura própria em `tests/test_card_selection_progress_service.py`
- o quality gate agora cobre também `tests/test_card_selection_progress_service.py`

## 2026-03-23 - Consolidar o fechamento comum da seleção em helper interno

Status: aceito

### Contexto

Mesmo depois das extrações maiores, `CardSelectionService` ainda repetia o mesmo fechamento de seleção em vários caminhos: resolver sentença, montar o payload do card e registrar o card mostrado na sessão. Isso aparecia em `new`, `review`, `relearn` e `fallback`.

### Decisão

- consolidar esse fechamento em um helper interno de `CardSelectionService`
- manter a mudança local ao próprio serviço, sem abrir mais um módulo só para mover duplicação pequena

### Impacto

- o serviço ficou menor e mais legível sem criar uma camada nova artificial
- os caminhos de seleção agora compartilham o mesmo fechamento, o que reduz risco de drift de comportamento entre modos

## 2026-03-23 - Remover wrappers REST redundantes do endpoint de chat

Status: aceito

### Contexto

Depois da extração do bloco REST para `api/app/services/chat_rest_service.py`, `chat.py` ainda mantinha wrappers locais só para repassar lookup e serialização ao mesmo serviço. Eles já não tinham utilidade além de aumentar o ruído do endpoint.

### Decisão

- remover esses wrappers locais de REST em `chat.py`
- fazer os endpoints HTTP chamarem `chat_rest_service` diretamente
- manter apenas os wrappers que ainda servem aos testes utilitários e aos helpers do fluxo WebSocket

### Impacto

- `chat.py` ficou mais próximo de um adaptador fino de verdade
- o endpoint perdeu uma camada de indireção sem alterar o contrato externo

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

## 2026-04-11 - Tirar bootstrap demo e autofill Lingvist do endpoint de cards

Status: aceito

### Contexto

Depois das extrações principais de Spec4, Lingvist e submit answer, `cards.py` ainda mantinha duas responsabilidades operacionais que não pertenciam à borda HTTP: criação do bootstrap demo local e autofill de traduções do Lingvist com cache TSV e fallback de MT.

### Decisão

- criar `api/app/services/card_bootstrap_service.py` para concentrar a garantia de dados mínimos locais do usuário demo
- criar `api/app/services/lingvist_autofill_service.py` para concentrar cache TSV e autofill on-demand de traduções do Lingvist
- manter wrappers finos em `cards.py` para preservar compatibilidade com chamadores e testes locais
- adicionar cobertura dedicada de autofill e incluir a nova suíte no quality gate

### Impacto

- `cards.py` fica mais próximo de um adaptador fino e perde mais uma camada operacional
- bootstrap demo e tradução Lingvist passam a ter fronteiras explícitas para manutenção futura
- a próxima fatia em `cards.py` pode focar mais em fluxo de endpoint e menos em detalhes auxiliares de infraestrutura local

## 2026-04-11 - Mover o fluxo legado de /cards/next para service próprio

Status: aceito

### Contexto

Mesmo depois das extrações anteriores, `cards.py` ainda mantinha a orquestração inteira do endpoint legado `/cards/next`: bootstrap demo, resolução do usuário, contagem de cards novos do dia e priorização `due -> new -> learning`.

### Decisão

- criar `api/app/services/card_next_service.py` para concentrar esse fluxo legado
- manter o endpoint `/cards/next` como adaptador fino para preservar contrato HTTP
- adicionar cobertura unitária própria para a ordem de seleção e incluir a suíte no quality gate

### Impacto

- `cards.py` perde o maior bloco residual de seleção legado fora de Spec4/Lingvist
- o fluxo `/cards/next` fica mais fácil de revisar, evoluir ou eventualmente descontinuar
- a próxima fatia em `cards.py` pode focar em wrappers residuais ou em simplificação adicional da borda

## 2026-04-11 - Remover wrappers locais redundantes de cards.py

Status: aceito

### Contexto

Depois das extrações para services próprios, `cards.py` ainda mantinha wrappers locais só para repassar chamadas aos serviços de legado, Spec4 e Lingvist. Eles já não carregavam regra de negócio nem ajudavam os chamadores.

### Decisão

- remover esses wrappers locais redundantes em `cards.py`
- fazer os endpoints chamarem diretamente `card_next_service`, `card_spec4_service` e `card_lingvist_service`
- manter o contrato HTTP inalterado

### Impacto

- `cards.py` fica mais curto e mais próximo de uma camada de borda de verdade
- a próxima rodada pode sair de `cards.py` com pouco risco, já que o endpoint perdeu boa parte da indireção restante

## 2026-04-11 - Mover a gestão REST de conversas do Chat Coach para service próprio

Status: aceito

### Contexto

Mesmo após as extrações de runtime, draft, feedback, contexto, delivery e rest serialization, `chat.py` ainda mantinha a criação, listagem, listagem de mensagens e remoção de conversas. Esse bloco REST já não dependia do loop WebSocket, mas ainda aumentava o peso do endpoint.

### Decisão

- criar `api/app/services/chat_conversation_service.py` para concentrar:
  - defaults de conversa nova
  - criação de conversa e mensagem inicial de sistema
  - listagem de conversas
  - listagem de mensagens
  - remoção de conversa
- manter `chat.py` como adaptador fino dos endpoints REST e do WebSocket
- adicionar cobertura unitária própria e incluir a nova suíte no quality gate

### Impacto

- `chat.py` perde mais um bloco REST e fica mais concentrado no runtime de chat
- a gestão de conversas passa a ter fronteira explícita para futuras mudanças de onboarding ou setup pedagógico
- a próxima fatia em `chat.py` pode focar melhor no estado local de draft/WebSocket ou nos wrappers utilitários restantes

## 2026-04-11 - Mover geração e streaming do Chat Coach para service próprio

Status: aceito

### Contexto

Depois da extração do bloco REST de conversas, `chat.py` ainda mantinha duas responsabilidades operacionais ligadas à geração: streaming do assistente token a token e geração da `teacher_analysis` com fallback seguro. Ambas já eram reutilizáveis e não dependiam da borda HTTP em si.

### Decisão

- criar `api/app/services/chat_generation_service.py` para concentrar:
  - streaming do assistente via websocket
  - geração da `teacher_analysis`
  - fallback seguro para falhas do provider
- manter wrappers compatíveis em `chat.py` para preservar os testes utilitários existentes
- adicionar cobertura unitária própria e incluir a nova suíte no quality gate

### Impacto

- `chat.py` perde mais uma faixa operacional do fluxo de geração
- a fronteira entre endpoint e comportamento de geração do Chat Coach fica mais explícita
- a próxima fatia pode focar no estado local de draft/websocket ou em remover wrappers utilitários restantes com menos risco

## 2026-04-11 - Mover o estado local de draft/throttle do Chat Coach para service próprio

Status: aceito

### Contexto

Depois das extrações de conversa e geração, `chat.py` ainda mantinha três dicts globais e helpers simples para throttle/cache de draft: timestamps de micro-eval, último feedback e último texto digitado por conversa. Isso era estado operacional de websocket, não detalhe da borda HTTP.

### Decisão

- criar `api/app/services/chat_draft_state_service.py` para concentrar:
  - store em memória do estado de draft
  - inicialização do throttle por conversa
  - cache do último feedback
  - montagem do payload throttled
- manter wrappers compatíveis em `chat.py` para preservar os testes utilitários existentes
- adicionar cobertura unitária própria e incluir a nova suíte no quality gate

### Impacto

- `chat.py` perde mais um detalhe de estado operacional do websocket
- o estado local de draft fica explícito e mais fácil de trocar ou encapsular no futuro
- a próxima fatia pode focar em wrappers utilitários restantes ou em reduzir ainda mais o tamanho do endpoint WebSocket

## 2026-04-11 - Mover o lifecycle do endpoint WebSocket do Chat Coach para service próprio

Status: aceito

### Contexto

Mesmo após as extrações de conversa, geração e estado de draft, `chat.py` ainda mantinha o lifecycle inteiro do endpoint WebSocket: `accept`, abertura da sessão de banco, carregamento de runtime, loop de receive/dispatch, tratamento de erro e fechamento.

### Decisão

- criar `api/app/services/chat_websocket_service.py` para concentrar o lifecycle do endpoint WebSocket
- manter `chat.py` responsável apenas por montar as dependências do session runner e expor o endpoint FastAPI
- adicionar cobertura unitária própria para o session runner e manter o teste integrado de fluxo WebSocket existente

### Impacto

- `chat.py` perde mais um bloco estrutural importante e fica mais próximo de uma camada adaptadora
- o lifecycle do WebSocket ganha uma fronteira testável fora do endpoint
- a próxima fatia pode focar nos wrappers utilitários restantes ou em reduzir ainda mais o acoplamento do arquivo de borda

## 2026-04-11 - Mover os handlers de evento do WebSocket do Chat Coach para service próprio

Status: aceito

### Contexto

Depois da extração do lifecycle da sessão WebSocket, `chat.py` ainda montava localmente `ChatDraftFeedbackState`, `ChatDraftFeedbackHelpers` e `ChatUserMessageTurnHelpers` dentro dos handlers de evento. O fluxo já estava quebrado em services menores, mas o endpoint ainda concentrava wiring operacional repetido.

### Decisão

- criar `api/app/services/chat_handler_service.py` para concentrar:
  - a montagem dos handlers de `draft_update`, `request_autocomplete` e `user_message`
  - a construção dos bundles de state/helpers usados nesses eventos
  - a injeção do timestamp do endpoint no fluxo de autocomplete
- manter `chat.py` responsável apenas por expor wrappers utilitários compatíveis e montar as dependências de alto nível do endpoint
- adicionar cobertura unitária própria e incluir a nova suíte no quality gate

### Impacto

- `chat.py` perde mais um bloco de wiring operacional e fica mais próximo de uma borda fina
- a montagem de handlers do WebSocket passa a ter fronteira explícita e testável
- a próxima fatia pode focar nos wrappers utilitários restantes sem reabrir a orquestração do fluxo de eventos

## 2026-04-12 - Mover os adapters configurados por ambiente de `chat.py` para service próprio

Status: aceito

### Contexto

Depois da extração do lifecycle e dos handlers de evento, `chat.py` ainda mantinha várias closures locais só para bindar configuração de ambiente e helpers já existentes: provider de LLM, URL/estratégia de grammar check, sanitizer, sender de `teacher_analysis` e builders de contexto.

### Decisão

- criar `api/app/services/chat_endpoint_adapter_service.py` para concentrar factories de adapters do endpoint
- manter `chat.py` exportando os mesmos símbolos utilitários compatíveis para os testes existentes
- adicionar cobertura unitária própria para garantir o bind correto de stores, providers, helpers e callbacks

### Impacto

- `chat.py` perde mais uma faixa de closures locais e fica ainda mais próximo de uma borda fina
- o bind de configuração e callbacks do Chat Coach passa a ser testado fora do endpoint
- a próxima fatia pode focar no frontend ou no pouco wiring utilitário restante do backend

## 2026-04-12 - Mover a montagem de `ChatHandlerDeps` de `chat.py` para o service de handlers

Status: aceito

### Contexto

Depois da extração dos handlers WebSocket e dos adapters configurados por ambiente, `chat.py` ainda mantinha um bloco relativamente grande só para montar o bundle `ChatHandlerDeps` com todas as dependências do fluxo de eventos.

### Decisão

- adicionar em `api/app/services/chat_handler_service.py` um builder explícito para `ChatHandlerDeps`
- deixar `chat.py` apenas chamar esse builder com as dependências já resolvidas
- ampliar a cobertura focal do service de handlers para garantir que o builder preserve os campos injetados

### Impacto

- `chat.py` perde mais um bloco de configuração de alto nível e fica ainda mais enxuto
- a montagem do bundle principal do WebSocket fica centralizada no mesmo service que já constrói os handlers
- a próxima fatia pode sair do backend ou atacar só o resíduo compatível de wrappers do endpoint

## 2026-04-12 - Mover a montagem de `ChatWebSocketSessionDeps` de `chat.py` para o service de websocket

Status: aceito

### Contexto

Depois da extração dos handlers, adapters e do bundle `ChatHandlerDeps`, o endpoint `chat.py` ainda montava localmente o bundle `ChatWebSocketSessionDeps` e mantinha wrappers triviais para contexto de chat e teacher context.

### Decisão

- adicionar em `api/app/services/chat_websocket_service.py` um builder explícito para `ChatWebSocketSessionDeps`
- centralizar também um helper `default_now_ms` no mesmo service para evitar mais uma closure local do endpoint
- trocar os wrappers triviais de `_build_context_messages` e `_build_teacher_context` por aliases diretos

### Impacto

- `chat.py` fica ainda mais próximo de uma borda fina e declarativa
- a configuração da sessão WebSocket passa a viver junto do runner que a consome
- o próximo corte pode encerrar o resíduo do backend ou mover o foco para os hotspots do frontend

## 2026-04-12 - Extrair cliente Axios e helpers de erro de `frontend/src/services/api.ts`

Status: aceito

### Contexto

Mesmo depois das simplificações nas sessões do frontend, `frontend/src/services/api.ts` ainda era um hotspot grande e misturava três responsabilidades diferentes no mesmo arquivo: cliente HTTP, helpers de erro e contratos/APIs por domínio.

### Decisão

- criar `frontend/src/services/apiClient.ts` para concentrar a criação do cliente Axios e seus interceptors
- criar `frontend/src/services/apiErrors.ts` para concentrar parsing de erro, status, code e regra de retry
- manter `frontend/src/services/api.ts` como fachada compatível, reexportando os mesmos helpers e contratos já consumidos pelos componentes

### Impacto

- `api.ts` perde parte do ruído estrutural sem exigir mudanças de import nos componentes
- cliente HTTP e tratamento de erro passam a ter fronteiras próprias para futuras extrações por domínio
- a próxima fatia do frontend pode separar APIs por área sem misturar novamente esse miolo comum

## 2026-04-12 - Separar `frontend/src/services/api.ts` por domínio mantendo uma fachada compatível

Status: aceito

### Contexto

Depois da extração do cliente Axios e dos helpers de erro, `frontend/src/services/api.ts` ainda concentrava contratos e chamadas HTTP de cards, usuários, insights, chat, perfis de LLM e healthcheck no mesmo arquivo.

### Decisão

- criar módulos por domínio em `frontend/src/services/`:
  - `apiCards.ts`
  - `apiUsers.ts`
  - `apiInsights.ts`
  - `apiChat.ts`
  - `apiLlmProfiles.ts`
  - `apiHealth.ts`
- manter `frontend/src/services/api.ts` como fachada de reexports para preservar os imports existentes no restante do app
- validar a fatia com `eslint` e `tsc -b`, registrando separadamente o bloqueio já conhecido do `vite build` no ambiente híbrido

### Impacto

- `api.ts` deixa de ser um hotspot operacional e vira uma fachada curta
- futuras fatias podem mover consumidores para imports por domínio sem precisar reabrir a estrutura interna
- o risco da refatoração cai porque a divisão interna melhora sem exigir churn imediato nos componentes

## 2026-04-12 - Migrar consumidores do frontend para imports diretos por domínio

Status: aceito

### Contexto

Depois da divisão de `frontend/src/services/api.ts`, a maior parte do app ainda importava tudo da fachada antiga. Isso preservava compatibilidade, mas mantinha um acoplamento desnecessário com um arquivo que já não era mais a melhor fronteira para evolução.

### Decisão

- migrar os consumidores principais para imports diretos de:
  - `apiCards`
  - `apiUsers`
  - `apiInsights`
  - `apiChat`
  - `apiLlmProfiles`
  - `apiHealth`
  - `apiErrors`
- manter `frontend/src/services/api.ts` apenas como camada de compatibilidade para evitar churn total de uma vez
- validar a fatia com `eslint` e `tsc -b`

### Impacto

- a divisão por domínio deixa de ser só interna e passa a ser usada pelo app real
- `api.ts` deixa de ser o ponto central de dependência do frontend
- a próxima fatia pode focar em componentes grandes como `ChatCoachSession.tsx` com menos ruído de transporte

## 2026-04-12 - Extrair helpers locais de mensagem e scroll de `ChatCoachSession.tsx`

Status: aceito

### Contexto

Depois da limpeza do transporte em `services/`, o próximo hotspot visível do frontend continuava sendo `ChatCoachSession.tsx`, ainda concentrando helpers puros de mensagem, título, scroll e algumas operações repetidas de limpeza do composer.

### Decisão

- criar `frontend/src/components/chatCoachSessionHelpers.ts` para concentrar:
  - montagem de `MessageDisplay`
  - mapeamento das mensagens carregadas da conversa
  - título padrão da conversa
  - helpers puros de scroll
- encapsular em callbacks locais do componente as operações repetidas de:
  - append de mensagens
  - limpeza do composer
  - limpeza do snapshot do último feedback

### Impacto

- `ChatCoachSession.tsx` perde parte da repetição local sem alterar o fluxo do WebSocket
- a próxima fatia no componente pode focar em transporte/estado de feedback sem carregar utilitários puros no mesmo arquivo
- o hotspot do frontend segue sendo reduzido em slices pequenas e verificáveis

## 2026-04-14 - Extrair o bootstrap de transporte de `ChatCoachSession.tsx` e encerrar o uso real da fachada `services/api`

Status: aceito

### Contexto

Depois da divisão por domínio de `services/`, o `ChatCoachSession.tsx` ainda fazia localmente o bootstrap da conversa e a criação do `ChatWS`, e parte do frontend ainda podia teoricamente depender da fachada `services/api` mesmo ela já não sendo a melhor fronteira.

### Decisão

- criar `frontend/src/components/chatCoachSessionTransport.ts` para concentrar:
  - bootstrap de conversa inicial
  - carregamento das mensagens persistidas
  - criação do `ChatWS` com `conversationId`
- trocar `frontend/src/services/chatWs.ts` para consumir tipos direto de `apiChat`
- concluir a migração dos imports do `frontend/src` para módulos por domínio, deixando `services/api` apenas como camada de compatibilidade

### Impacto

- `ChatCoachSession.tsx` perde mais um bloco de transporte e fica mais focado em estado visual e callbacks da tela
- o frontend deixa de depender operacionalmente da fachada `services/api`
- a próxima fatia pode focar no estado de feedback/autocomplete do `ChatCoachSession` sem reabrir a base de transporte

## 2026-04-14 - Consolidar o estado de feedback/autocomplete de `ChatCoachSession.tsx`

Status: aceito

### Contexto

Depois da extração do transporte, `ChatCoachSession.tsx` ainda mantinha muitos `useState` e updates coordenados manualmente para os sinais de draft: score, issues, ghost suggestion, micro tip, suggested words, topic, intent e rewrite.

### Decisão

- criar `frontend/src/components/chatCoachSessionFeedback.ts` para concentrar:
  - shape do estado de feedback
  - estado inicial
  - mapeamento de `DraftFeedbackEvent` para state local
  - limpeza da ghost suggestion
  - snapshot mínimo do feedback enviado
- trocar o componente para usar um state object de feedback em vez de múltiplos setters independentes

### Impacto

- o componente perde parte da coordenação manual de `setState` ligada ao draft
- a próxima fatia pode separar melhor autocomplete/composer ou teacher analysis em cima de uma base de estado mais coesa
- o fluxo visual permanece o mesmo, mas a manutenção fica menos frágil

## 2026-04-14 - Extrair o bloco visual do composer de `ChatCoachSession.tsx`

Status: aceito

### Contexto

Depois da extração de transporte e da consolidação do estado de feedback, `ChatCoachSession.tsx` ainda carregava o JSX completo do composer, incluindo score bar, textarea, ghost suggestion, botão de envio e hint textual.

### Decisão

- criar `frontend/src/components/ChatCoachComposer.tsx` como componente visual dedicado para o bloco de entrada
- manter no componente pai apenas os callbacks e o estado necessários para envio, autocomplete e foco
- validar a fatia com `eslint` e `tsc -b`

### Impacto

- `ChatCoachSession.tsx` perde mais um bloco de UI repetitiva e fica mais legível
- a próxima fatia pode focar no restante da coordenação do componente, especialmente teacher analysis ou message list, sem misturar o composer no mesmo arquivo
- a UX permanece idêntica, mas a manutenção do bloco de entrada fica isolada

## 2026-04-14 - Extrair a área de mensagens e streaming de `ChatCoachSession.tsx`

Status: aceito

### Contexto

Depois da extração do composer, `ChatCoachSession.tsx` ainda carregava um bloco grande de JSX para a lista de mensagens, a resposta em streaming e o botão `jump to latest`. Era um pedaço visual denso, mas com pouca lógica própria do container.

### Decisão

- criar `frontend/src/components/ChatCoachMessagePane.tsx` para concentrar:
  - lista de mensagens
  - estado visual da resposta em streaming
  - botão `jump to latest`
- manter no componente pai apenas os estados e callbacks necessários para scroll e streaming
- validar a fatia com `eslint` e `tsc -b`

### Impacto

- `ChatCoachSession.tsx` perde mais um bloco relevante de UI e fica bem mais fácil de percorrer
- a próxima fatia pode focar no header/settings/teacher analysis ou em reduzir ainda mais a coordenação do container
- o comportamento visível permanece o mesmo, com menor custo cognitivo para manutenção


## 2026-04-14 - Extrair o header e a tela de loading de `ChatCoachSession.tsx`

Status: aceito

### Contexto

Depois da extração do composer e da área de mensagens, `ChatCoachSession.tsx` ainda mantinha no mesmo arquivo o header da tela e o estado visual de loading. Eram blocos puramente visuais, mas ainda poluíam a leitura do container principal.

### Decisão

- criar `frontend/src/components/ChatCoachHeader.tsx` para concentrar o cabeçalho da sessão
- criar `frontend/src/components/ChatCoachLoading.tsx` para concentrar o estado de carregamento inicial
- manter no container apenas a composição desses blocos e seus callbacks de alto nível
- validar a fatia com `eslint` e `tsc -b`

### Impacto

- `ChatCoachSession.tsx` perde o restante do JSX incidental de chrome da tela
- a próxima fatia pode atacar só a coordenação de estado/lifecycle sem carregar ruído visual no mesmo arquivo
- a UX permanece idêntica, com menor custo cognitivo para manutenção

## 2026-04-14 - Extrair a coordenação de sessão de `ChatCoachSession.tsx` para um hook dedicado

Status: aceito

### Contexto

Mesmo depois das extrações visuais, `ChatCoachSession.tsx` ainda concentrava bootstrap da conversa, lifecycle do WebSocket, timers de autocomplete, scroll pinning, envio de mensagens e handlers de feedback. O componente já não era um hotspot de JSX, mas ainda era um hotspot de coordenação.

### Decisão

- criar `frontend/src/components/useChatCoachSession.ts` para concentrar:
  - bootstrap da conversa
  - lifecycle do `ChatWS`
  - coordenação de draft, feedback, streaming e envio
  - scroll pinning, foco do composer e timers de autocomplete
  - estado do painel de settings
- deixar `frontend/src/components/ChatCoachSession.tsx` como composição fina de UI sobre o hook
- validar a fatia com `eslint` e `tsc -b`

### Impacto

- `ChatCoachSession.tsx` deixa de ser hotspot estrutural e vira principalmente um container declarativo
- o estado operacional da sessão fica isolado em uma fronteira mais fácil de testar e evoluir
- o próximo foco do frontend pode sair do Chat Coach e ir para os hotspots restantes, principalmente `LingvistSession.tsx` e o residual de `StudySession.tsx`

## 2026-04-14 - Adotar Gemma 4 E4B como modelo local principal

Status: aceito

### Contexto

O stack local já usava `llama.cpp`, mas o perfil principal ainda estava ancorado em Qwen 2.5 7B. Depois da análise do repositório, da GPU disponível localmente e da documentação oficial atual de Gemma, o melhor encaixe para o ambiente local de 8 GB de VRAM deixou de ser manter o modelo anterior como default.

### Decisão

- adotar `gemma-4-e4b-it` como perfil padrão de chat e teacher
- manter Phi-3 Mini e Qwen 2.5 3B como perfis opcionais para latência ou experimentação
- normalizar preferências persistidas antigas para evitar que perfis removidos continuem presos no banco
- alinhar compose, docs operacionais e script oficial de download ao novo default

### Impacto

- o modelo local principal fica mais coerente com o hardware atual e com a família recomendada no estado atual da stack
- o repositório passa a ter um default único e explícito para Chat Coach local
- a evolução futura de perfis continua possível sem reabrir a configuração base

## 2026-04-14 - Tornar o frontend reproduzível em ambiente híbrido Windows/WSL

Status: aceito

### Contexto

O `vite build` local falhava porque o mesmo `frontend/node_modules` estava sendo materializado de um lado e executado do outro: install Linux e execução via `node.exe` do Windows. Isso quebrava a resolução do binário nativo do Rollup e deixava o build dependente de limpeza manual do diretório de dependências.

### Decisão

- separar `typecheck` de `build` no `frontend/package.json`
- criar `scripts/frontend_tooling.sh` como caminho oficial para `install`, `lint`, `typecheck`, `build` e `check` em um container Node fixo
- mover cache npm e `node_modules` desse fluxo para `.cache/frontend-tooling`
- ajustar `frontend/Dockerfile` para instalar dependências de build reais e validar o bundle no mesmo contrato do CI

### Impacto

- o frontend volta a ter `lint`, `typecheck` e `build` reproduzíveis no mesmo ambiente local
- o repositório deixa de depender de `frontend/node_modules` híbrido para validar mudanças
- a superfície de troubleshooting local fica menor e mais previsível

## 2026-04-14 - Reduzir o compose padrão e introduzir um smoke E2E curto no CI

Status: aceito

### Contexto

O compose padrão ainda subia IA local por default, o que aumentava custo de setup e impedia aproveitar o stack mínimo em validações automáticas. Ao mesmo tempo, o quality gate ainda não exercitava nenhum fluxo real de frontend a ponta a ponta.

### Decisão

- mover `llm`, `llm_chat`, `llm_teacher` e `languagetool` para o perfil opcional `ai`
- deixar `db`, `api` e `frontend` como stack padrão mínima
- mover `tts` para perfil opcional `audio`
- ajustar `quick_start.sh` para expor `--with-ai` e `--with-audio`
- adicionar ao quality gate: `npm run typecheck`, `docker compose config --quiet` e um smoke E2E Chromium curto para onboarding/entrada no estudo
- usar `global-setup.ts` baseado em requests HTTP, não em browser lançado só para healthcheck

### Impacto

- o stack local padrão sobe mais rápido e com menos dependências pesadas
- o Chat Coach completo continua disponível, mas agora como escolha explícita de perfil operacional
- a confiança do pipeline aumenta porque existe uma verificação E2E curta e barata antes de expandir para uma suíte maior


## 2026-04-14 - Estabilizar fronteiras de plataforma entre banco, transporte frontend e endpoints de leitura

Status: aceito

### Contexto

A revisão arquitetural mostrou três fragilidades de plataforma: o runtime principal usava `StaticPool` mesmo fora de SQLite em memória, o bundle do frontend ainda podia embutir `localhost` para API/TTS e os endpoints de `stats`/`settings` ainda criavam usuário demo como efeito colateral de leitura.

### Decisão

- restringir `StaticPool` a SQLite em memória e usar `pool_pre_ping` no caminho normal de PostgreSQL
- padronizar o frontend para consumir rotas relativas (`/api` e `/api/tts`) no build de produção, mantendo proxy explícito do Vite no desenvolvimento
- remover bootstrap implícito de usuário demo de `stats` e `settings`, exigindo `user_id` explícito na borda
- mover lookup/serialização de insights por palavra/card para `api/app/services/insights_service.py`
- mover a orquestração por modo de `CardSelectionService` para `api/app/services/card_selection_mode_service.py`

### Impacto

- o runtime principal fica coerente com PostgreSQL sem perder o caso especial de testes com SQLite em memória
- o frontend passa a gerar artefato portátil atrás do proxy local sem embutir host fixo
- leitura de stats/settings deixa de causar seed implícito e fica mais previsível para teste, cache e operação
- analytics de palavra/card e seleção por modo ficam mais fáceis de evoluir sem inflar endpoints e services centrais

## 2026-04-14 - Expandir o quality gate de E2E para a suíte Chromium completa

Status: aceito

### Contexto

O CI já tinha um smoke curto de frontend, mas o repositório mantinha uma suíte Playwright bem maior sem execução oficial. Ao mesmo tempo, os testes ainda estavam parcialmente presos à UI antiga de meta de vocabulário por slider, embora a tela real já tivesse migrado para botões.

### Decisão

- promover a suíte Chromium completa (`tests/e2e/playwright.ci.config.ts`) ao quality gate oficial
- manter `global-setup.ts` com healthchecks HTTP para reduzir ruído no bootstrap da suíte
- alinhar os testes de criação de perfil à UI atual baseada em botões de meta de vocabulário
- adicionar `data-testid` e `aria-pressed` explícitos para as metas no formulário de criação de perfil

### Impacto

- o CI passa a exercer o comportamento real de onboarding, estudo, Lingvist, insights e seleção de perfil
- a suíte E2E fica alinhada com a UI atual e mais resiliente a mudanças superficiais de layout
- o projeto reduz dependência de validação manual para fluxos críticos do frontend


## 2026-04-14 - Fechar o hotspot residual de resolução em `CardSelectionService`

Status: aceito

### Contexto

Depois da extração da orquestração por modo, `CardSelectionService` ainda mantinha internamente a resolução de card novo, review, fallback elegível e relearn. O arquivo já tinha melhorado, mas ainda concentrava mais detalhe operacional do que precisava.

### Decisão

- criar `api/app/services/card_selection_resolution_service.py`
- mover para esse módulo a montagem do payload selecionado e os fluxos de `new`, `review`, `fallback` e `relearn`
- manter `CardSelectionService` como orquestrador fino e compatível com os testes/integrações atuais

### Impacto

- `CardSelectionService` deixa de ser hotspot estrutural principal
- a lógica de resolução de candidatos fica isolada para futuras mudanças de regra
- a trilha Spec4/Lingvist continua validada sem mudança de contrato externo

## 2026-04-14 - Dividir o `MockLLMProvider` em módulos por responsabilidade

Status: aceito

### Contexto

Mesmo funcionando, `api/app/llm/mock_provider.py` continuava como um arquivo grande demais, misturando análise textual, geração de resposta conversacional, payloads de micro-eval/autocomplete e teacher analysis. Isso mantinha um hotspot técnico desnecessário no caminho de desenvolvimento local e testes.

### Decisão

- mover análise textual para `api/app/llm/mock_text_analysis.py`
- mover geração de resposta conversacional e streaming para `api/app/llm/mock_chat_responses.py`
- mover micro-eval, autocomplete e teacher analysis para `api/app/llm/mock_feedback_payloads.py`
- deixar `api/app/llm/mock_provider.py` como adaptador fino para a interface de provider
- incluir `tests/test_chat_coach_mock_provider.py` no quality gate principal

### Impacto

- o provider local fica muito mais fácil de percorrer e manter
- a heurística mock continua disponível para desenvolvimento sem GPU, mas agora organizada por responsabilidade
- a regressão de comportamento fica protegida pela suíte existente do mock provider e pela fábrica de LLM

## 2026-04-21 - Usar structured outputs para as tarefas pedagógicas do Chat Coach

Status: aceito

### Contexto

O `Chat Coach` já usava LLM real para a resposta principal, mas `micro_eval` e autocomplete ainda ficavam presos à heurística mock, enquanto a `teacher_analysis` dependia de parsing textual frágil e expunha um schema didático raso. Isso desperdiçava capacidade do modelo justamente na parte mais pedagógica do produto.

### Decisão

- introduzir `api/app/llm/pedagogical_tasks.py` com prompts e schemas explícitos para `micro_eval`, autocomplete e `teacher_analysis`
- fazer `LlamaCppLLMProvider` e `OpenAILLMProvider` pedirem JSON estruturado por schema nessas três tarefas, mantendo fallback seguro para `MockLLMProvider`
- enriquecer o contrato do `Chat Coach` com scaffolds adicionais:
  - `self_check_prompt`
  - `encouragement`
  - `strengths`
  - `focus_areas`
  - `reflection_question`
- normalizar o payload de `teacher_analysis` na camada de entrega para manter compatibilidade com payloads antigos/incompletos

### Impacto

- o Chat Coach passa a aproveitar LLM real também nas camadas de feedback e não só na resposta conversacional
- o contrato de análise fica mais estável e menos dependente de parsing permissivo
- a sidebar do frontend ganha sinais mais didáticos, sem alterar o fluxo principal do chat

## 2026-04-21 - Fechar a variedade real do lookahead no Lingvist

Status: aceito

### Contexto

O WIP local do Lingvist já introduzia perfil de dificuldade por fase e melhor escolha de sentenças, mas a função `choose_frequency_ordered_new_word()` ainda sempre devolvia o menor rank disponível no pool. Na prática, o comentário prometia lookahead com variedade, mas a implementação ainda era determinística demais.

### Decisão

- ordenar explicitamente os candidatos por rank dentro de `choose_frequency_ordered_new_word()`
- escolher dentro da janela com pesos decrescentes por posição, preservando viés forte para palavras mais frequentes sem eliminar variedade
- ampliar a suíte focal de `api/tests/test_lingvist_difficulty_service.py` para cobrir ordenação do pool, exclusões e lookahead real

### Impacto

- o modo Lingvist continua frequency-first, mas deixa de repetir um comportamento excessivamente mecânico
- a regra fica coerente com o comentário do código e com a intenção pedagógica do modo
- futuras calibrações de dificuldade ficam mais fáceis porque a escolha do novo item agora tem uma fronteira explícita

## 2026-04-21 - Persistir memória pedagógica do Chat Coach em `student_profile_json` e `session_summary`

Status: aceito

### Contexto

Depois dos structured outputs, o Chat Coach ainda reagia principalmente ao turno isolado. O repositório já tinha sinais úteis em `User` e no histórico de `teacher_analysis`, mas eles não eram reinjetados de forma consistente em novas conversas nem em novos prompts.

### Decisão

- criar `api/app/services/chat_profile_service.py` para derivar um perfil pedagógico longitudinal a partir de `User` e do histórico recente de `teacher_analysis`
- usar `student_profile_json` e `session_summary` como memória persistida do Chat Coach, sem introduzir nova tabela nesta fase
- atualizar essa memória a cada `teacher_analysis`, preservando strengths, focus areas, recent topics, scaffolding e idioma de feedback
- devolver `student_profile` e `session_summary` atualizados no evento WebSocket de `teacher_analysis`

### Impacto

- novas conversas do Chat Coach passam a nascer com contexto pedagógico real, e não mais com perfil genérico
- o frontend consegue mostrar o "coach memory" sem fazer roundtrip REST extra
- a arquitetura ganha um ponto explícito para calibrar heurísticas de CEFR, scaffolding e foco pedagógico sem espalhar regra por handlers e prompts

## 2026-04-21 - Separar idioma do feedback pedagógico do idioma-alvo

Status: aceito

### Contexto

O produto já conhecia `language_preference` do aluno, mas o Chat Coach quase sempre devolvia feedback pedagógico em inglês, misturando explicação, scaffold e exercício no mesmo idioma. Isso reduzia clareza didática justamente para alunos mais iniciantes.

### Decisão

- usar `language_preference` como fonte para `feedback_language` no perfil pedagógico do Chat Coach
- orientar prompts estruturadas para que explicações, summaries, strengths, focus areas, reflection questions e encouragement apareçam no idioma de feedback
- manter rewrites, sugestões e exercícios no idioma-alvo, para não perder o papel de treino
- alinhar também o `MockLLMProvider` a esse contrato multilíngue básico, para desenvolvimento local sem GPU continuar representativo

### Impacto

- o Chat Coach fica mais didático para perfis iniciantes sem abandonar a prática no idioma-alvo
- o contrato entre backend, prompts e frontend fica mais explícito sobre o que deve ser localizado e o que deve permanecer em inglês
- futuras melhorias multilíngues passam a ter uma fronteira de implementação clara
