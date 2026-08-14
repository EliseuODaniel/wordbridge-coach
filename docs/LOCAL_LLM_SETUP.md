# Local LLM Setup

## Contrato atual

O stack padrão usa `CHAT_LLM_PROVIDER=mock` para manter `db/api/frontend` leve. O LLM real é opt-in pelo perfil `ai`.

Baseline validado em 2026-08-14:

- NVIDIA GeForce RTX 4070 Laptop GPU, 8 GB de VRAM
- Intel Core i9-14900HX, 32 threads
- 16 GB de RAM
- `llama.cpp` CUDA via `ghcr.io/ggml-org/llama.cpp:server-cuda`
- Qwen3.5 9B Q4_K_S como modelo principal

O serviço principal usa um único slot, flash attention e 4.096 tokens de contexto. Os modelos legados menores ficam nos perfis explícitos `fastchat`/`optional-llm`; eles não sobem junto com `ai`, porque três servidores simultâneos excedem a VRAM disponível.

## Diretório de modelos

Por padrão, o compose monta `./llm_models`. Para manter GGUFs fora do repositório, defina um caminho absoluto:

```dotenv
WORDBRIDGE_MODELS_PATH=/home/edann/models/wordbridge-coach
```

O diretório precisa conter `model.gguf` ou um link relativo cujo destino esteja dentro do mesmo diretório montado. Um link para fora do bind mount fica quebrado no container.

## Download

O script baixa por padrão o Qwen3.5 9B Q4_K_S e aceita diretório alternativo:

```bash
./scripts/download_model.sh
./scripts/download_model.sh unsloth/Qwen3.5-9B-GGUF /home/edann/models/wordbridge-coach
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
PYTHONPATH=. .venv/bin/python scripts/evaluate_local_llm_candidates.py \
  --runs 2 --summary-only --json-output /tmp/wordbridge-llm-eval.json
```

O benchmark usa os prompts reais de chat, autocomplete, microavaliação e análise do professor em nove cenários por rodada. Ele mede latência/tokens por segundo, valida os schemas Pydantic e verifica idioma do feedback, erros semânticos, falsos positivos, duplicatas, resistência a prompt injection e ausência de correção proativa no chat. O relatório JSON preserva todas as respostas para análise qualitativa; retorno zero continua sendo um gate deliberadamente estrito.

Resultado comparativo bruto em duas repetições por modelo, antes do hardening de prompts e normalização desta mudança:

| Modelo | VRAM usada após carga | Geração | Gate completo | Decisão |
|---|---:|---:|---:|---|
| Qwen2.5 7B Q4_K_M | ~5,3 GB | ~40–42 tok/s | 2/18 | substituir |
| Qwen3.5 4B Q4_K_M | ~3,6 GB | ~54–58 tok/s | 4/18 | rejeitar: qualidade insuficiente |
| Ministral 3 8B Q4_K_M | ~6,1 GB | ~36 tok/s | 6/18; 8/18 contratos | rejeitar: JSON/verbosidade instáveis |
| Qwen3.5 9B Q4_K_S | ~5,6 GB | ~35–36 tok/s | 9/18; 18/18 contratos | promover: melhor qualidade global |

O placar estrito não é uma média de qualidade: cada cenário só passa se todos os checks passarem. A inspeção das respostas mostrou que o Qwen3.5 9B foi o único candidato a melhorar consistentemente português, presente perfeito, expressões de idade e concordância em espanhol mantendo todos os contratos válidos. Parte das nove falhas iniciais era do próprio avaliador — ele rejeitava um destaque exato como `Yesterday I go` por esperar apenas `go` —, corrigido antes da rodada final.

Após o hardening, a rodada de aceitação passou 8/9 diretamente. A única saída restante descrevia uma frase correta como uma melhoria opcional, não como erro; a normalização de borda rejeitou essa contradição e o replay dos mesmos nove payloads passou 9/9. O chat, cuja instrução conflitante também foi removida, passou ainda em três repetições consecutivas isoladas. Os 9/9 contratos JSON permaneceram válidos.

O runtime usa `--reasoning off`, que é a opção atual do `llama.cpp` para evitar raciocínio oculto em tarefas curtas. O Qwen3.5 9B deixa cerca de 2,5 GB de margem na GPU e mantém latência de chat interativa, embora análises estruturadas grandes sejam mais lentas que no 4B. Por isso, o 9B atende melhor ao objetivo pedagógico; o 4B só seria preferível se latência ou memória fossem prioritárias sobre qualidade.

## Fontes

Fontes primárias consultadas:

- [Qwen3.5-9B model card](https://huggingface.co/Qwen/Qwen3.5-9B)
- [Qwen3.5-4B model card](https://huggingface.co/Qwen/Qwen3.5-4B)
- [Ministral 3 8B GGUF model card](https://huggingface.co/mistralai/Ministral-3-8B-Instruct-2512-GGUF)
- [Phi-4 Mini model card](https://huggingface.co/microsoft/Phi-4-mini-instruct)
- [Quantização Qwen3.5 9B usada](https://huggingface.co/unsloth/Qwen3.5-9B-GGUF)
- [llama.cpp server documentation](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md)
- [llama.cpp schema-constrained output example](https://github.com/ggml-org/llama.cpp/blob/master/examples/json_schema_pydantic_example.py)
