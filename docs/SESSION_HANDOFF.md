# Session Handoff

Data: 2026-04-24

## Ponto de retomada

- workspace atual: `/home/edann/projects/wordbridge-coach`
- repositório GitHub: `EliseuODaniel/wordbridge-coach`
- branch ativa: `main`
- `HEAD` remoto alinhado antes desta rodada: `245039f`
- estado atual: esta rodada alterou runtime, skills e docs; revisar `git status --short` antes de publicar

## O que mudou nesta rodada

- análise geral registrou que o projeto já passou da fase de existência funcional e agora precisa priorizar confiabilidade, avaliação pedagógica e operabilidade
- `frontend/nginx.conf` passou a resolver o upstream opcional de TTS de forma tardia, para o stack padrão não depender do perfil `audio`
- `scripts/init.sql` deixou de criar índices em tabelas ainda inexistentes; schema e índices ficam sob responsabilidade das migrations Alembic
- `scripts/quick_start.sh` passou a exportar `WORDBRIDGE_DB_PORT` como variável principal e subir explicitamente `db api frontend` no caminho padrão
- `docs/PROJECT_STATUS.md`, `docs/ROADMAP.md`, `docs/ARCHITECTURE.md`, `docs/TESTING.md`, `docs/DECISIONS.md`, `docs/CODEX_SETUP.md` e `README.md` foram alinhados com essa direção
- nova skill local `local-runtime-triage` foi adicionada para subir, diagnosticar e derrubar o runtime local com menos improviso
- `engineering-hygiene` e `git-hygiene` ganharam regras sobre runtime, feedback visível e limpeza de processos

## Onde pesquisar primeiro

1. `docs/PROJECT_STATUS.md`
2. `docs/ROADMAP.md`
3. `docs/DECISIONS.md`
4. `docs/ARCHITECTURE.md`
5. `docs/CODEX_SETUP.md`
6. `.agents/skills/local-runtime-triage/SKILL.md`
7. `frontend/nginx.conf`

## Status funcional real

- `main` e `origin/main` estavam alinhados em `245039f` antes desta rodada
- o fluxo de criação de perfil foi corrigido na rodada anterior e confirmado manualmente
- o runtime padrão deve ser tratado como `db/api/frontend`
- `audio` e `ai` são opcionais e devem ser testados separadamente
- o stack local deve ser derrubado depois de testes para preservar recursos da máquina
- smoke temporária `wordbridge-smoke` validou volume novo, migrations, seed, API health e frontend em `localhost:3007`
- o build da imagem da API ainda é pesado: a instalação/exportação trouxe dependências Torch/CUDA no caminho padrão

## Validação executada nesta rodada

```bash
docker compose config --quiet
./scripts/frontend_tooling.sh check
WORDBRIDGE_DB_PORT=55433 docker compose -p wordbridge-smoke up -d --build db api frontend
docker compose -p wordbridge-smoke exec -T api alembic upgrade head
docker compose -p wordbridge-smoke exec -T api python scripts/seed_data.py
curl -fsS http://localhost:8000/health
curl -fsS http://localhost:3007 >/dev/null
docker compose -p wordbridge-smoke down -v --remove-orphans
```

Depois da validação, não ficaram containers WordBridge rodando. Os volumes descartáveis criados pela primeira tentativa de smoke também foram removidos.

## Próximo passo recomendado

Não abrir feature grande ainda. O melhor próximo passo é formalizar uma smoke local curta e automatizável para criação de perfil, carregamento do primeiro card e troca de modo no stack padrão, depois partir para avaliação pedagógica dos sinais `pedagogical_metrics`, `lesson_frame` e `learning_context`.
