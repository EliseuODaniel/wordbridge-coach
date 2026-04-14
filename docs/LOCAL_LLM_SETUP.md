# Local LLM Setup

## Objetivo

Registrar o setup local mínimo para os serviços de LLM usados pelo projeto.

## Pré-requisitos

- Docker e Docker Compose
- GPU NVIDIA recomendada para melhor desempenho
- espaço livre para modelos GGUF

Ambiente local validado nesta rodada:

- NVIDIA GeForce RTX 4070 Laptop GPU com 8 GB de VRAM
- `llama.cpp` via `ghcr.io/ggml-org/llama.cpp:server-cuda`

## Modelos

O compose espera modelos em `llm_models/`.

Arquivo principal esperado pelo serviço `llm`:

```bash
llm_models/model.gguf
```

Modelo principal recomendado para este repositório:

```bash
ggml-org/gemma-4-E4B-it-GGUF
```

Perfis opcionais continuam disponíveis para modelos menores em serviços separados:

- `Phi-3 Mini 4K` para chat rápido
- `Qwen2.5 3B Instruct` para teacher analysis rápida

## Download

Script disponível:

```bash
./scripts/download_model.sh
```

Se necessário, crie o link simbólico esperado pelo serviço principal:

Se necessário, crie o link simbólico esperado pelo serviço principal:

```bash
ln -s llm_models/gemma-4-E4B-it-Q4_K_M.gguf llm_models/model.gguf
```

## Subida dos serviços

Modo padrão:

```bash
docker compose up -d
```

Modo com perfis opcionais de LLM secundária:

```bash
docker compose --profile optional-llm --profile fastchat up -d
```

## Verificação

```bash
docker compose ps
docker logs filltheword-llm
docker logs filltheword-llm-teacher
```

## Observação

O padrão recomendado agora é subir apenas o `llm` principal com Gemma 4 E4B e ativar serviços secundários só quando houver ganho claro de latência. Isso reduz pressão de VRAM no ambiente local de 8 GB.
