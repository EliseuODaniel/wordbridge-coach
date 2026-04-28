# WordBridge Coach

Aplicação local para treino de vocabulário com cards, cloze, repetição espaçada, áudio local e coaching com LLM.

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

O projeto se chamava `FillTheWord`, mas o escopo atual já é mais amplo do que treino de lacunas. O branding oficial passa a ser `WordBridge Coach`, enquanto alguns identificadores internos legados (`filltheword_*`) continuam por compatibilidade operacional.

## Quick start

Para customizar o ambiente local, use o template versionado:

```bash
cp .env.example .env
```

`.env` é local e não deve ser commitado. Para `staging` ou `production`, use `DEBUG=false`, `STRICT_CONFIG=true` e um `SECRET_KEY` gerado fora do repositório.

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
- runtime Piper TTS sob demanda, com modelos em `tts_models`

Serviços opcionais com `--with-ai`:

- LLM local principal em `http://localhost:8080`
- LanguageTool em `http://localhost:8010`

Fluxo manual equivalente:

```bash
docker compose up -d --build db api frontend
docker compose exec -T api alembic upgrade head
docker compose exec -T api python scripts/seed_data.py
```

Se `5432` ja estiver ocupada no host, suba com outra porta para o Postgres local:

```bash
WORDBRIDGE_DB_PORT=55432 docker compose up -d --build db api frontend
```

Smoke local automatizado:

```bash
./scripts/smoke_local.sh
```

Esse smoke usa um projeto Compose temporário, roda migrations/seed, valida API/frontend, cria um perfil e carrega o primeiro card. Por padrão ele derruba a stack e remove os volumes temporários ao terminar.

Backup/restore do banco local:

```bash
./scripts/db_backup.sh
./scripts/db_restore.sh --yes backups/wordbridge-YYYYMMDD-HHMMSS.dump
```

Os dumps ficam em `backups/`, ignorado pelo Git.

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

Quando rodar o Vite manualmente dentro de `frontend/`, o proxy de desenvolvimento usa por padrão `http://localhost:8000` para a API e `http://localhost:8001` para TTS. Para apontar para outros targets sem mudar o bundle:

```bash
WORDBRIDGE_API_PROXY_TARGET=http://localhost:8000 WORDBRIDGE_TTS_PROXY_TARGET=http://localhost:8001 npm run dev
```

O stack padrão deve subir sem áudio e sem IA local. TTS e LLM continuam opcionais para preservar memória, VRAM e tempo de build durante testes comuns.

O perfil `audio` usa Piper TTS. Coqui/Torch não fazem parte da imagem local suportada nesta fase.

A imagem base da API não instala Argos Translate por padrão. Para testar tradução offline com Argos, use:

```bash
INSTALL_ARGOS=true docker compose up -d --build db api frontend
```

## Estrutura principal

```text
wordbridge-coach/
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

O produto já funciona como um treinador local multimodal de vocabulário. A base funcional existe e a documentação oficial foi consolidada para reduzir drift e duplicação.
