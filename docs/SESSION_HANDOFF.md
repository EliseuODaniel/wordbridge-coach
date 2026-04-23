# Session Handoff

Data: 2026-04-22

## Ponto de retomada

- workspace atual: `/home/edann/projects/wordbridge-coach`
- repositório GitHub: `EliseuODaniel/wordbridge-coach`
- branch ativa na última sessão: `codex/refactor-local-platform-quality`
- `HEAD` observado na última sessão: `469358c`
- estado do repositório ao encerrar esta sessão: worktree sujo com mudanças locais importantes; não assumir estado limpo

## O que mudou nesta rodada

- o nome público do produto foi renomeado de `FillTheWord` para `WordBridge Coach`
- o repositório GitHub foi renomeado para `wordbridge-coach`
- o workspace local foi movido de `/home/edann/vscode_projects/filltheword` para `/home/edann/projects/wordbridge-coach`
- docs e scripts foram ajustados para não depender do caminho antigo
- `api/test-runner.sh` passou a usar `.venv/bin/python -m pytest` e a configurar `TMPDIR` estável, o que evita quebra quando a pasta do projeto muda

## Onde pesquisar primeiro

Se a próxima sessão for retomar desenvolvimento e não só onboarding, comece por:

1. `docs/PROJECT_STATUS.md`
2. `docs/ROADMAP.md`
3. `docs/DECISIONS.md`
4. `api/app/services/chat_profile_service.py`
5. `api/app/services/lingvist_difficulty_service.py`
6. `frontend/src/components/useChatCoachSession.ts`
7. `frontend/src/components/AnalysisPanel.tsx`
8. `frontend/src/components/LearningContextPanel.tsx`
9. `tests/e2e/tests/study-session.spec.ts`
10. `tests/e2e/tests/lingvist-session.spec.ts`

## Status funcional real

O núcleo pedagógico atual já está implementado localmente:

- `Chat Coach` com memória longitudinal, `pedagogical_state`, `lesson_frame` adaptativo e `teacher_analysis` enriquecido
- `Spec4` e `Lingvist` consumindo `learning_context` compartilhado
- `Lingvist` com lookahead ponderado por frequência e dificuldade calibrada por sinais reais
- branding novo `WordBridge Coach` refletido em UI, docs, metadata das apps e GitHub

## Baseline validado para retomada

Comandos que passaram na rodada mais recente:

```bash
docker compose config --quiet
./scripts/frontend_tooling.sh check
cd api && TMPDIR=/home/edann/projects/wordbridge-coach/.tmp_pytest PYTHONPATH=. TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test .venv/bin/python -m pytest -s -q tests/test_chat_profile_service.py tests/test_chat_text_service.py tests/test_lingvist_difficulty_service.py tests/test_card_spec4_service.py tests/test_lingvist_payload_service.py tests/integration/test_chat_websocket_flow.py
cd api && TEST_DATABASE_URL=postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test ./test-runner.sh --spec4
cd tests/e2e && PATH="$HOME/.local/bin:$PATH" CI=1 BASE_URL=http://127.0.0.1:3007 npx playwright test tests/smoke.spec.ts tests/user-profile.spec.ts tests/study-session.spec.ts tests/lingvist-session.spec.ts --project=chromium
```

Resultados mais recentes:

- backend focal: `26 passed`
- runner Spec4: `10 passed`
- Playwright focal: `26 passed`

## Observações operacionais

- as suítes de backend que compartilham o mesmo banco de teste devem rodar em série, não em paralelo
- ainda existem identificadores internos legados `filltheword_*` em banco, compose e containers; isso é esperado por compatibilidade
- o worktree local contém mudanças não commitadas em backend, frontend, testes, docs e rename; revisar antes de qualquer commit ou PR

## Próximo passo recomendado

Ao retomar, não comece por refatoração estrutural genérica. O melhor uso da próxima sessão é:

1. revisar o worktree atual e separar o que já está pronto para commit do que ainda é WIP
2. confirmar se a próxima fatia será calibração pedagógica, mais cobertura E2E ou consolidação do rename
3. só depois expandir feature ou abrir PR
