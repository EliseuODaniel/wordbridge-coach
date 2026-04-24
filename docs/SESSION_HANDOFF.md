# Session Handoff

Data: 2026-04-24

## Ponto de retomada

- workspace atual: `/home/edann/projects/wordbridge-coach`
- repositório GitHub: `EliseuODaniel/wordbridge-coach`
- branch ativa: `main`
- `HEAD` remoto alinhado antes desta implementação: `5b60a64`
- estado atual: esta rodada alterou smoke local, dependências da API, testes pedagógicos, operabilidade e docs; revisar `git status --short` antes de publicar

## O que mudou nesta rodada

- análise geral registrou que o projeto já passou da fase de existência funcional e agora precisa priorizar confiabilidade, avaliação pedagógica e operabilidade
- `frontend/nginx.conf` passou a resolver o upstream opcional de TTS de forma tardia, para o stack padrão não depender do perfil `audio`
- `scripts/init.sql` deixou de criar índices em tabelas ainda inexistentes; schema e índices ficam sob responsabilidade das migrations Alembic
- `scripts/quick_start.sh` passou a exportar `WORDBRIDGE_DB_PORT` como variável principal e subir explicitamente `db api frontend` no caminho padrão
- `docs/PROJECT_STATUS.md`, `docs/ROADMAP.md`, `docs/ARCHITECTURE.md`, `docs/TESTING.md`, `docs/DECISIONS.md`, `docs/CODEX_SETUP.md` e `README.md` foram alinhados com essa direção
- nova skill local `local-runtime-triage` foi adicionada para subir, diagnosticar e derrubar o runtime local com menos improviso
- `engineering-hygiene` e `git-hygiene` ganharam regras sobre runtime, feedback visível e limpeza de processos
- `scripts/smoke_local.sh` virou o smoke oficial curto do stack padrão
- `api/requirements-argos.txt` concentra Argos Translate como dependência opcional via `INSTALL_ARGOS=true`
- `api/app/main.py` migrou os checks de startup para `lifespan`
- `api/tests/test_pedagogical_metrics_eval.py` adicionou regressões determinísticas para política pedagógica
- logs mínimos foram adicionados para criação de perfil, seleção de card, turno do Chat Coach e fallback de teacher analysis

## Onde pesquisar primeiro

1. `docs/PROJECT_STATUS.md`
2. `docs/ROADMAP.md`
3. `docs/DECISIONS.md`
4. `docs/ARCHITECTURE.md`
5. `docs/CODEX_SETUP.md`
6. `.agents/skills/local-runtime-triage/SKILL.md`
7. `scripts/smoke_local.sh`
8. `api/tests/test_pedagogical_metrics_eval.py`
9. `api/app/main.py`

## Status funcional real

- `main` e `origin/main` estavam alinhados em `5b60a64` antes desta implementação
- o fluxo de criação de perfil foi corrigido na rodada anterior e confirmado manualmente
- o runtime padrão deve ser tratado como `db/api/frontend`
- `audio` e `ai` são opcionais e devem ser testados separadamente
- o stack local deve ser derrubado depois de testes para preservar recursos da máquina
- o smoke curto agora cria um perfil real e carrega o primeiro card Spec4
- o build padrão da API não deve mais instalar Argos/Torch/CUDA; isso fica restrito ao extra opcional de Argos

## Validação executada nesta rodada

```bash
docker compose config --quiet
./scripts/frontend_tooling.sh check
cd api && TMPDIR=/home/edann/projects/wordbridge-coach/.tmp_pytest PYTHONPATH=. .venv/bin/python -m pytest tests/test_config_runtime.py tests/test_pedagogical_metrics_eval.py tests/test_chat_turn_service.py tests/test_chat_generation_service.py -q
cd api && TMPDIR=/home/edann/projects/wordbridge-coach/.tmp_pytest PYTHONPATH=. .venv/bin/python -m pytest tests/test_lingvist_difficulty_service.py -k 'not sentence_selection' -q
./scripts/smoke_local.sh
docker run --rm wordbridge-smoke-api python -c "import importlib.util; assert importlib.util.find_spec('argostranslate') is None; print('argos-not-installed')"
```

Depois da validação, não ficaram containers nem volumes WordBridge rodando. O check de frontend passou, mantendo o aviso de npm audit com `13 vulnerabilities (5 moderate, 8 high)`.

## Próximo passo recomendado

Não abrir feature grande ainda. O melhor próximo passo é validar se a imagem base da API ficou leve o suficiente no CI e então ampliar o smoke para troca de modo e Chat Coach sem perder velocidade.
