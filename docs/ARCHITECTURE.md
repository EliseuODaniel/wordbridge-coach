# Architecture

Data de referência: 2026-04-24

## Visão geral

WordBridge Coach é uma aplicação local composta por frontend web, API principal, serviço de TTS, banco PostgreSQL e serviços auxiliares para experiências de IA local.

## Serviços

### Frontend

Local: `frontend/`

Stack observada:

- React 18
- TypeScript
- Vite
- TailwindCSS

Responsabilidades:

- seleção de usuário
- navegação entre modos de treino
- renderização das sessões de estudo
- consumo da API principal e serviços auxiliares

Entradas importantes:

- `frontend/src/App.tsx`
- `frontend/src/components/StudySession.tsx`
- `frontend/src/components/LingvistSession.tsx`
- `frontend/src/components/ChatCoachSession.tsx`

### API principal

Local: `api/`

Stack observada:

- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- pytest

Responsabilidades:

- usuários, configurações e progresso
- seleção de cards e lógica de estudo
- estatísticas e insights
- orquestração do Chat Coach
- preferências de LLM

Rotas agregadas em:

- `cards`
- `stats`
- `settings`
- `users`
- `insights`
- `chat`
- `llm-profiles`

Arquivo central:

- `api/app/api/api_v1/api.py`

### TTS

Local: `tts/`

Responsabilidades:

- geração de áudio
- cache de áudio em volume compartilhado
- runtime opcional baseado em Piper TTS; Coqui/Torch não fazem parte da imagem local suportada nesta fase

### Infra local

Arquivo central: `docker-compose.yml`

Dependências observadas:

- PostgreSQL para dados
- volume de áudio para cache
- modelos locais em `llm_models/`
- perfil opcional `ai` para LanguageTool e `llama.cpp`

Topologia local atual de LLM:

- `llm`: perfil principal recomendado, usando Gemma 4 E4B quantizado em GGUF
- `llm_chat`: perfil opcional de baixa latência com Phi-3 Mini
- `llm_teacher`: perfil opcional de teacher analysis rápida com Qwen2.5 3B

Topologia operacional padrão:

- stack default: `db`, `api`, `frontend`
- stack com áudio local: `docker compose --profile audio up -d --build`
- stack com IA local: `docker compose --profile ai up -d --build`
- `Chat Coach` completo depende do perfil `ai`; áudio local depende do perfil `audio`; Study Session e Lingvist seguem funcionais no stack padrão
- o perfil `audio` usa uma imagem TTS pequena e sob demanda; modelos Piper ficam no volume `tts_models` e devem ser baixados separadamente quando áudio real for necessário

## Fronteiras operacionais atuais

- a API usa configuração de engine dependente do backend: `StaticPool` fica restrito a SQLite em memória; PostgreSQL usa pool padrão com `pool_pre_ping`
- a API usa `lifespan` do FastAPI para checks leves de startup e logs de ciclo de vida
- configuração local é documentada em `.env.example`; `.env` real fica fora do Git, e ambientes `staging`/`production` devem rodar com `DEBUG=false`, `STRICT_CONFIG=true` e segredo real em `SECRET_KEY`
- backup/restore local do banco usa `pg_dump`/`pg_restore` pelo container `db`; dumps ficam em `backups/` e não fazem parte do repositório
- o frontend gera bundle de produção apontando para rotas relativas (`/api` e `/api/tts`), enquanto o Vite usa um contrato explícito de proxy em `frontend/viteProxy.ts` para API, Chat Coach WebSocket, TTS opcional e `/health`; os targets de desenvolvimento podem ser sobrescritos por `WORDBRIDGE_API_PROXY_TARGET` e `WORDBRIDGE_TTS_PROXY_TARGET`
- o Nginx do frontend resolve o upstream opcional de TTS de forma tardia, permitindo que o stack padrão suba mesmo quando o perfil `audio` está desligado
- `stats` e `settings` exigem `user_id` explícito e não criam mais usuário demo como efeito colateral de endpoints de leitura
- payloads de áudio e TTS usam URLs relativas, reduzindo acoplamento com host fixo
- o lookup e a serialização de insights por palavra/card vivem em um service dedicado, reduzindo duplicação na borda HTTP
- o runtime base da API não instala Argos Translate; tradução offline é extra opcional via `INSTALL_ARGOS=true`

## Fluxos principais

### Estudo principal

1. frontend seleciona usuário
2. frontend pede próximo card
3. API aplica regras de seleção e progresso
4. API injeta `learning_context` derivado da memória pedagógica mais recente quando existir contexto longitudinal de Chat Coach
5. frontend mostra o foco atual, o objetivo da sessão e o racional pedagógico do modo
6. frontend envia resposta
7. API registra review, feedback e estatísticas

### Lingvist

1. frontend entra no modo Lingvist
2. API retorna conteúdo com apoio de tradução, hints, progressão e `learning_context` compartilhado
3. frontend mostra contexto pedagógico compacto acima do card
4. frontend atualiza a sessão com feedback e métricas

### Chat Coach

1. frontend abre sessão de chat
2. API combina contexto da conversa, perfil longitudinal do aluno, analytics recentes e provider de LLM
3. quando o perfil `ai` está ativo, serviços locais de LLM e LanguageTool participam da resposta
4. `micro_eval`, autocomplete e `teacher_analysis` agora preferem structured outputs com schema explícito, mantendo fallback seguro para o mock
5. `api/app/services/chat_profile_service.py` deriva o perfil pedagógico de `User` + histórico recente de `teacher_analysis`, agrega `pedagogical_metrics` reais de `UserCardState`, `ReviewEvent` e `UserSessionStats`, mantém um `pedagogical_state` explícito e recalcula `student_profile_json`, `lesson_frame_json` e `session_summary` a cada turno
6. cada atualização de `teacher_analysis` persiste um snapshot do `lesson_frame` em `chat_lesson_history`
7. frontend exibe feedback, análise, sugestões, o "coach memory" e o `lesson_frame` adaptativo atualizado, incluindo scaffolds cognitivos, metacognitivos e motivacionais
8. `VocabularyProgressionService` reaproveita esses sinais para ajustar o perfil Lingvist antes de escolher dificuldade de sentença, faixa de comprimento e pool de lookahead

## Estado pedagógico compartilhado

- `student_profile_json` guarda sinais longitudinais, idioma de feedback, scaffolding, `pedagogical_state` e `pedagogical_metrics`
- `lesson_frame_json` guarda o objetivo adaptativo do turno atual (`learning_goal`, `expected_intent`, `primary_focus`, `lesson_stage`, `success_criteria`) e um bloco `diagnostics`
- `chat_lesson_history` guarda snapshots desse frame para analytics e replay pedagógico
- `learning_context` é a projeção compacta desse estado para modos de card (`Spec4` e `Lingvist`), incluindo sinais de retenção, pressão de review, pacing e melhor próximo modo
- `build_pedagogical_analytics_projection()` é a projeção read-side atual para analytics pedagógico; endpoint ou tabela dedicada ficam adiados até existir necessidade de consulta longitudinal mais pesada

## Pontos de acoplamento

- `docker-compose.yml` concentra muita responsabilidade operacional
- Chat Coach depende de múltiplos serviços e configurações
- frontend acumula três experiências diferentes no mesmo app
- parte das features de analytics e progressão atravessa vários modelos e serviços
- o ambiente local de 8 GB de VRAM não deve manter múltiplos modelos médios sempre ativos sem necessidade
- ambiente híbrido Windows/WSL não deve compartilhar o mesmo `frontend/node_modules` entre installs Linux e execução via `node.exe`
- a efetividade pedagógica do Chat Coach agora já usa memória longitudinal entre sessões, métricas explícitas de estudo e projeção cross-mode para `Spec4`/`Lingvist`; o refinamento futuro passa mais por calibração de limiares do que por ausência de sinais

## Direção arquitetural desejada

1. Simplificar a documentação e o setup.
2. Reduzir acoplamento entre modos de treino.
3. Tornar regras de domínio mais explícitas.
4. Separar melhor código de produto, código experimental e snapshots históricos.
5. Expandir smoke automatizado para cobrir troca de modo e Chat Coach quando o custo de runtime estiver menor.
6. Transformar sinais pedagógicos em métricas avaliáveis cada vez mais próximas de dados reais, mantendo datasets pequenos e estáveis para regressão.
