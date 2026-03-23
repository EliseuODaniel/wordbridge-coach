# Local LLM Setup

## Objetivo

Registrar o setup local mínimo para os serviços de LLM usados pelo projeto.

## Pré-requisitos

- Docker e Docker Compose
- GPU NVIDIA recomendada para melhor desempenho
- espaço livre para modelos GGUF

## Modelos

O compose espera modelos em `llm_models/`.

Arquivo principal esperado pelo serviço `llm`:

```bash
llm_models/model.gguf
```

Há também referências a modelos dedicados para `llm_chat` e `llm_teacher`.

## Download

Script disponível:

```bash
./scripts/download_model.sh
```

Se necessário, crie o link simbólico esperado pelo serviço principal:

```bash
ln -s llm_models/qwen2.5-7b-instruct-q4_k_m.gguf llm_models/model.gguf
```

## Subida dos serviços

Modo padrão:

```bash
docker compose up -d
```

Modo com perfil `fastchat`:

```bash
docker compose --profile fastchat up -d
```

## Verificação

```bash
docker compose ps
docker logs filltheword-llm
docker logs filltheword-llm-teacher
```

## Observação

Este setup ainda fará parte da próxima rodada de simplificação. A documentação aqui registra o comportamento atual, não uma arquitetura final.
