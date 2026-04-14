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
- [`docs/CODEX_SETUP.md`](docs/CODEX_SETUP.md)

## Quick start

```bash
./scripts/quick_start.sh
```

Perfis opcionais:

```bash
./scripts/quick_start.sh --with-audio
./scripts/quick_start.sh --with-ai
./scripts/quick_start.sh --with-ai --with-audio
```

Serviços padrão:

- frontend: `http://localhost:3007`
- api: `http://localhost:8000`
- api docs: `http://localhost:8000/docs`

Serviços opcionais com `--with-audio`:

- tts: `http://localhost:8001/health`

Serviços opcionais com `--with-ai`:

- LLM local principal em `http://localhost:8080`
- LanguageTool em `http://localhost:8010`

Fluxo manual equivalente:

```bash
docker compose up -d --build
docker compose exec api alembic upgrade head
docker compose exec api python scripts/seed_data.py
```

Se `5432` ja estiver ocupada no host, suba com outra porta para o Postgres local:

```bash
FTW_DB_PORT=55432 docker compose up -d --build
```

Fluxo manual com áudio local:

```bash
docker compose --profile audio up -d --build
docker compose --profile audio exec api alembic upgrade head
docker compose --profile audio exec api python scripts/seed_data.py
```

Fluxo manual com IA local:

```bash
docker compose --profile ai up -d --build
docker compose --profile ai exec api alembic upgrade head
docker compose --profile ai exec api python scripts/seed_data.py
```

Para áudio e IA local juntos:

```bash
docker compose --profile audio --profile ai up -d --build
docker compose --profile audio --profile ai exec api alembic upgrade head
docker compose --profile audio --profile ai exec api python scripts/seed_data.py
```

## Checks locais do frontend

Em ambiente hibrido Windows/WSL, o caminho suportado para `lint`, `typecheck` e `build` e:

```bash
./scripts/frontend_tooling.sh check
```

Isso evita corromper `frontend/node_modules` ao misturar installs Linux e execucao via `node.exe` do Windows.

O bundle de produção do frontend agora usa rotas relativas para API e TTS (`/api` e `/api/tts`), então o mesmo artefato funciona atrás do Nginx local sem embutir `localhost` no build.

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
