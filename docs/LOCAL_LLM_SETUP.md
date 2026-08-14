# Local LLM Setup

## Contrato atual

O stack padrão usa `CHAT_LLM_PROVIDER=mock` para manter `db/api/frontend` leve. O LLM real é opt-in pelo perfil `ai`.

Baseline validado em 2026-08-14:

- NVIDIA GeForce RTX 4070 Laptop GPU, 8 GB de VRAM
- Intel Core i9-14900HX, 32 threads
- 16 GB de RAM
- `llama.cpp` CUDA via `ghcr.io/ggml-org/llama.cpp:server-cuda`
- Qwen2.5 7B Instruct Q4_K_M como modelo principal efetivamente instalado

O serviço principal usa um único slot, flash attention e 4.096 tokens de contexto. Os modelos legados menores ficam nos perfis explícitos `fastchat`/`optional-llm`; eles não sobem junto com `ai`, porque três servidores simultâneos excedem a VRAM disponível.

## Diretório de modelos

Por padrão, o compose monta `./llm_models`. Para manter GGUFs fora do repositório, defina um caminho absoluto:

```dotenv
WORDBRIDGE_MODELS_PATH=/home/edann/models/wordbridge-coach
```

O diretório precisa conter `model.gguf` ou um link relativo cujo destino esteja dentro do mesmo diretório montado. Um link para fora do bind mount fica quebrado no container.

## Download

O script baixa por padrão o Qwen2.5 7B Instruct Q4_K_M oficial e aceita diretório alternativo:

```bash
./scripts/download_model.sh
./scripts/download_model.sh Qwen/Qwen2.5-7B-Instruct-GGUF /home/edann/models/wordbridge-coach
```

O script suporta GGUF dividido em múltiplos arquivos e cria `model.gguf` apontando para a primeira parte.

## Subida

Stack leve:

```bash
docker compose up -d
```

LLM local real, sem iniciar os modelos opcionais:

```bash
CHAT_LLM_PROVIDER=llamacpp CHAT_LLM_STRICT=true docker compose --profile ai up -d --build
```

Verificação:

```bash
docker compose ps
docker compose logs llm
curl -fsS http://127.0.0.1:8080/health
```

## Benchmark da aplicação

Com `llm` saudável:

```bash
cd api
PYTHONPATH=. .venv/bin/python scripts/benchmark_local_llm.py --summary-only
```

O benchmark usa os prompts reais de chat, autocomplete, microavaliação e análise do professor. Ele mede latência/tokens por segundo, valida os schemas Pydantic e aplica checks pedagógicos pequenos, incluindo idioma do feedback e a irregularidade de `go -> went`. Retorno zero exige que todos os contratos e checks passem.

Resultado observado em três repetições no hardware acima:

| Modelo | VRAM usada após carga | Geração | Gate completo | Decisão |
|---|---:|---:|---:|---|
| Qwen2.5 7B Q4_K_M | ~5,2 GB usados | ~48–51 tok/s | 2/3 | manter como baseline local |
| Gemma 4 E4B Q4_0 | ~3,8 GB usados | ~59–63 tok/s | 0/3 | não promover ainda |

O Gemma 4 exigiu `--reasoning-budget 0` e `--chat-template-kwargs '{"enable_thinking":false}'` para não consumir todo o limite em raciocínio oculto. Mesmo assim, ignorou repetidamente o idioma de feedback do professor e por vezes sugeriu `-ed` no contexto do verbo irregular `go`.

## Próxima candidata

Qwen3.5 4B é a candidata preferencial para a próxima avaliação por combinar 4B parâmetros, arquitetura eficiente e cobertura oficial de 201 idiomas. A troca só deve ocorrer depois de existir uma quantização GGUF confiável para o runtime adotado e de ela superar este benchmark em múltiplas repetições. Não basta comparar benchmarks gerais publicados pelos fabricantes.

Fontes primárias consultadas:

- [Qwen3.5-4B model card](https://huggingface.co/Qwen/Qwen3.5-4B)
- [Gemma 4 model card](https://ai.google.dev/gemma/docs/core/model_card_4)
- [llama.cpp server documentation](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md)
- [llama.cpp schema-constrained output example](https://github.com/ggml-org/llama.cpp/blob/master/examples/json_schema_pydantic_example.py)
