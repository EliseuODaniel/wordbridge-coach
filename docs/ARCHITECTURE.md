# Architecture

Data de referência: 2026-04-14

## Visão geral

FillTheWord é uma aplicação local composta por frontend web, API principal, serviço de TTS, banco PostgreSQL e serviços auxiliares para experiências de IA local.

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

## Fronteiras operacionais atuais

- a API usa configuração de engine dependente do backend: `StaticPool` fica restrito a SQLite em memória; PostgreSQL usa pool padrão com `pool_pre_ping`
- o frontend gera bundle de produção apontando para rotas relativas (`/api` e `/api/tts`), enquanto o Vite usa proxy explícito para `localhost:8000` e `localhost:8001` no desenvolvimento
- `stats` e `settings` exigem `user_id` explícito e não criam mais usuário demo como efeito colateral de endpoints de leitura
- payloads de áudio e TTS usam URLs relativas, reduzindo acoplamento com host fixo
- o lookup e a serialização de insights por palavra/card vivem em um service dedicado, reduzindo duplicação na borda HTTP

## Fluxos principais

### Estudo principal

1. frontend seleciona usuário
2. frontend pede próximo card
3. API aplica regras de seleção e progresso
4. frontend envia resposta
5. API registra review, feedback e estatísticas

### Lingvist

1. frontend entra no modo Lingvist
2. API retorna conteúdo com apoio de tradução, hints e progressão
3. frontend atualiza a sessão com feedback e métricas

### Chat Coach

1. frontend abre sessão de chat
2. API combina contexto da conversa, perfil do aluno e provider de LLM
3. quando o perfil `ai` está ativo, serviços locais de LLM e LanguageTool participam da resposta
4. frontend exibe feedback, análise e sugestões

## Pontos de acoplamento

- `docker-compose.yml` concentra muita responsabilidade operacional
- Chat Coach depende de múltiplos serviços e configurações
- frontend acumula três experiências diferentes no mesmo app
- parte das features de analytics e progressão atravessa vários modelos e serviços
- o ambiente local de 8 GB de VRAM não deve manter múltiplos modelos médios sempre ativos sem necessidade
- ambiente híbrido Windows/WSL não deve compartilhar o mesmo `frontend/node_modules` entre installs Linux e execução via `node.exe`

## Direção arquitetural desejada

1. Simplificar a documentação e o setup.
2. Reduzir acoplamento entre modos de treino.
3. Tornar regras de domínio mais explícitas.
4. Separar melhor código de produto, código experimental e snapshots históricos.
