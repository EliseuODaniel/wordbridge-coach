# Architecture

Data de referência: 2026-03-23

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
- LanguageTool para apoio de escrita
- `llama.cpp` para inferência local

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
3. serviços locais de LLM e LanguageTool participam da resposta
4. frontend exibe feedback, análise e sugestões

## Pontos de acoplamento

- `docker-compose.yml` concentra muita responsabilidade operacional
- Chat Coach depende de múltiplos serviços e configurações
- frontend acumula três experiências diferentes no mesmo app
- parte das features de analytics e progressão atravessa vários modelos e serviços

## Direção arquitetural desejada

1. Simplificar a documentação e o setup.
2. Reduzir acoplamento entre modos de treino.
3. Tornar regras de domínio mais explícitas.
4. Separar melhor código de produto, código experimental e snapshots históricos.
