# E2E AGENTS.md

Instruções específicas para testes Playwright.

## Escopo

Aplica-se a tudo dentro de `tests/e2e/`.

## Objetivo

- cobrir fluxos críticos reais, não reproduzir toda a lógica unitária do app
- manter specs curtas, legíveis e com foco em regressão de produto

## Regras de mudança

- prefira um teste por fluxo observável
- evite cenários frágeis dependentes de timing quando houver alternativa
- não commite relatórios ou artefatos de debug

## Validação padrão

```bash
cd tests/e2e
npm test
```
