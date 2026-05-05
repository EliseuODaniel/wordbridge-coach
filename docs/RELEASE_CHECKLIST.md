# Release Checklist

Use este checklist antes de tirar um PR de release local do modo draft.

## Antes dos checks

- [ ] Confirmar `git status --short --branch`.
- [ ] Confirmar se a stack local existente deve ficar ativa para teste manual.
- [ ] Gerar backup se houver dados locais importantes.

## Runtime padrão

- [ ] `WORDBRIDGE_DB_PORT=55432 docker compose config --quiet`
- [ ] `./scripts/smoke_local.sh`
- [ ] `curl -fsS http://127.0.0.1:8000/health`
- [ ] `curl -fsS http://127.0.0.1:3007 >/dev/null`

## Backend e frontend

- [ ] Backend focal proporcional ao escopo tocado.
- [ ] `./scripts/frontend_tooling.sh check` quando UI, tipos ou serviços frontend mudarem.
- [ ] `bash -n scripts/db_backup.sh scripts/db_restore.sh` quando scripts operacionais forem tocados.

## E2E crítico

- [ ] `cd tests/e2e && BASE_URL=http://127.0.0.1:3007 npm run test:ci`
- [ ] `cd tests/e2e && PATH="$HOME/.local/bin:$PATH" CI=1 BASE_URL=http://127.0.0.1:3007 npx playwright test --config=playwright.ci.config.ts tests/chat-coach.spec.ts tests/mode-switch.spec.ts --project=chromium`

## Perfis opcionais

- [ ] `WORDBRIDGE_DB_PORT=55432 docker compose --profile audio config --quiet`
- [ ] `WORDBRIDGE_DB_PORT=55432 docker compose --profile ai config --quiet`
- [ ] `docker run --rm wordbridge-coach-tts piper --help >/dev/null`
- [ ] Validar runtime completo de `audio` somente com `8001` livre.
- [ ] Validar runtime completo de `ai` somente com modelos GGUF, GPU/CUDA e portas `8080`, `8081`, `8082`, `8010` livres.

## Calibração

- [ ] Exportar sinais pedagógicos depois de uma sessão real:

```bash
WORDBRIDGE_DB_PORT=55432 docker compose exec -T api python scripts/export_pedagogy_calibration.py --username demo
```

- [ ] Registrar se os sinais batem com a experiência real da sessão.

## Fechamento

- [ ] `git diff --check`
- [ ] Atualizar `docs/PROJECT_STATUS.md` com validações novas e limitações.
- [ ] Atualizar `docs/ROADMAP.md` se algum item da fase mudou de status.
- [ ] Pushar branch e atualizar PR.
