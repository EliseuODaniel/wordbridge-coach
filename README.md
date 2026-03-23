# FillTheWord

Aplicação local para treino de vocabulário com lacunas, repetição espaçada, áudio local e modos extras de estudo.

## O que existe hoje

- backend FastAPI em `api/`
- frontend React + Vite em `frontend/`
- serviço TTS em `tts/`
- stack local via `docker-compose.yml`
- modos de uso no frontend: estudo principal, Lingvist e Chat Coach
- integrações locais com `llama.cpp` e LanguageTool

## Documentação oficial

- [`AGENTS.md`](AGENTS.md)
- [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md)
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- [`docs/ROADMAP.md`](docs/ROADMAP.md)
- [`docs/DECISIONS.md`](docs/DECISIONS.md)
- [`docs/TESTING.md`](docs/TESTING.md)
- [`docs/LOCAL_LLM_SETUP.md`](docs/LOCAL_LLM_SETUP.md)

## Quick start

```bash
./scripts/quick_start.sh
```

Serviços padrão:

- frontend: `http://localhost:3007`
- api: `http://localhost:8000`
- api docs: `http://localhost:8000/docs`
- tts: `http://localhost:8001/health`
- languagetool: `http://localhost:8010`

Fluxo manual equivalente:

```bash
docker compose up -d --build
docker compose exec api python scripts/seed_data.py
```

## Estrutura principal

```text
filltheword/
├── api/
├── frontend/
├── tts/
├── docs/
├── scripts/
├── tests/
├── docker-compose.yml
└── AGENTS.md
```

## Situação atual

O projeto está em fase de limpeza de governança e preparação para refatoração. A base funcional existe, mas a documentação antiga foi consolidada para reduzir drift e duplicação.
