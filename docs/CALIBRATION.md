# Calibration

## Objetivo

Esta fase transforma uso real em ajustes pequenos e auditáveis para:

- `retention_band`
- `review_pressure`
- `recommended_pace`
- `recommended_mode`

O projeto ainda não deve ajustar esses limiares por impressão isolada. Cada ajuste precisa ter uma sessão observada, um export de sinais e uma hipótese curta.

## Protocolo de sessão real

Para cada perfil usado na calibração:

1. Rode uma sessão curta em Spec4, Lingvist e Chat Coach, quando fizer sentido para o nível do aluno.
2. Anote o que pareceu desalinhado:
   - suporte demais ou de menos
   - troca de modo recomendada fora de hora
   - ritmo acelerado quando havia muitos reviews
   - Lingvist muito fácil ou muito difícil
3. Exporte os sinais logo depois da sessão.
4. Compare o export com a percepção real antes de mudar código.

Comando recomendado no stack local:

```bash
WORDBRIDGE_DB_PORT=55432 docker compose exec -T api python scripts/export_pedagogy_calibration.py --username demo
```

Para salvar um snapshot local:

```bash
WORDBRIDGE_DB_PORT=55432 docker compose exec -T api python scripts/export_pedagogy_calibration.py --username demo --output /tmp/demo-calibration.json
```

## Critérios para mudar limiares

Um ajuste de heurística só deve entrar quando pelo menos uma destas condições for verdadeira:

- duas ou mais sessões reais repetem o mesmo desalinhamento
- um export mostra `review_pressure=high` enquanto a UX ainda acelera introdução ou conversa
- `recommended_mode` diverge do modo em que o aluno consegue progredir com menos atrito
- `retention_band` não acompanha acerto/erro observável depois de revisão real

## Critérios para endpoint de analytics

Analytics pedagógico deve continuar como projeção interna enquanto:

- a UI só precisa do `learning_context` atual
- os exports locais bastam para revisar calibração
- não existe consumidor externo ou dashboard longitudinal

Reavaliar um endpoint dedicado quando houver:

- necessidade de histórico por período
- comparação entre múltiplos perfis
- dashboard de calibração
- integração externa ao frontend atual
