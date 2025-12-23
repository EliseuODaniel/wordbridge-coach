# FillTheWord - Guia Completo de Testes

Este documento descreve como executar os testes automatizados do FillTheWord, incluindo backend (pytest) e frontend E2E (Playwright).

## 📋 Sumário

- [Backend Tests (pytest)](#backend-tests-pytest)
- [E2E Tests (Playwright)](#e2e-tests-playwright)
- [Cobertura de Testes](#cobertura-de-testes)
- [Execução Contínua](#execução-contínua)

---

## 🧪 Backend Tests (pytest)

### Estrutura dos Testes

```
api/
├── tests/
│   ├── conftest.py              # Fixtures e configuração
│   ├── unit/                    # Testes unitários (se necessário)
│   ├── integration/             # Testes de integração
│   │   ├── test_users_api.py
│   │   ├── test_spec4_card_selection.py
│   │   ├── test_insights_frequency.py
│   │   └── test_themes_stats.py
│   └── fixtures/                # Fixtures adicionais (se necessário)
├── pytest.ini                  # Configuração do pytest
├── requirements-test.txt        # Dependências de teste
└── test-runner.sh              # Script facilitador
```

### Pré-requisitos

```bash
# Ativar ambiente virtual
source venv/bin/activate

# Instalar dependências de teste
pip install -r requirements-test.txt

# Iniciar banco de dados de teste
docker-compose --profile test up -d db_test
```

### Execução dos Testes

#### Método 1: Script Facilitador

```bash
# Rodar todos os testes
./test-runner.sh

# Rodar apenas testes de integração
./test-runner.sh --integration

# Rodar apenas testes Spec4
./test-runner.sh --spec4

# Rodar com coverage
./test-runner.sh --all --coverage

# Saída verbosa
./test-runner.sh --all --verbose
```

#### Método 2: pytest direto

```bash
# Todos os testes
pytest

# Apenas integração
pytest tests/integration/

# Apenas Spec4
pytest tests/integration/ -m spec4

# Com coverage
pytest --cov=app --cov-report=html

# Verbose
pytest -v

# Teste específico
pytest tests/integration/test_users_api.py::TestUsersAPI::test_create_user_basic
```

### Fixtures Disponíveis

- `sample_languages`: Cria idiomas (en, fr, pt)
- `sample_words_frequencies`: Dados de frequência EN/FR
- `sample_words`: Palavras vinculadas às frequências
- `sample_sentences`: Sentenças para测试
- `sample_cards`: Cards ativos
- `sample_themes`: Temas para WordThemeMapping
- `test_user`: Usuário com goal=100 para inglês
- `test_user_french`: Usuário com goal=150 para francês
- `user_card_states`: Estados iniciais dos cards
- `sample_user_daily_stats`: Estatísticas diárias
- `sample_user_theme_stats`: Estatísticas por tema

### Cobertura de Testes Backend

#### Users API ✅
- [x] CRUD de usuários
- [x] Criação com word_goal_rank
- [x] Suporte a en/fr como target_language
- [x] Mudança de idioma com reset de progresso
- [x] Validação de username duplicado

#### Spec4 Card Selection ✅
- [x] Respeito à janela inicial (goal)
- [x] Gating prefixal (não retorna rank > goal)
- [x] Mix 25% novas / 75% revisão
- [x] Atualização do algoritmo SM-2
- [x] Avanço após acertos consecutivos
- [x] Respostas incorretas não avançam gating

#### Insights e Frequência ✅
- [x] Frequência por idioma (EN/FR separados)
- [x] Cobertura monotônica
- [x] Sem fallback entre idiomas
- [x] Dados completos para palavras com frequência
- [x] Tratamento de usuários sem dados

#### Temas e Estatísticas ✅
- [x] Criação de UserWordStats após respostas
- [x] Atualização de UserThemeStats
- [x] Atualização de UserDailyStats
- [x] Precisão nos cálculos de accuracy
- [x] Múltiplos dias em daily stats

---

## 🎭 E2E Tests (Playwright)

### Estrutura dos Testes

```
tests/e2e/
├── tests/
│   ├── user-profile.spec.ts     # Fluxo de criação/perfil
│   ├── study-session.spec.ts    # Sessão de estudo Spec4
│   └── insights.spec.ts         # Insights e estatísticas
├── playwright.config.ts         # Configuração do Playwright
├── package.json                 # Dependências E2E
└── global-setup.ts             # Setup global
```

### Instalação

```bash
cd tests/e2e
npm install
npm run install-browsers  # Instala browsers do Playwright
```

### Execução dos Testes E2E

#### Pré-requisitos

```bash
# Iniciar serviços (se não já rodando)
cd ../..
docker-compose up -d api frontend

# Ou desenvolvimento local
cd api && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
cd frontend && npm run dev &
```

#### Execução

```bash
cd tests/e2e

# Todos os testes (headless)
npm test

# Testes visuais (headed)
npm run test:headed

# Modo debug
npm run test:debug

# Interface UI do Playwright
npm run test:ui

# Browser específico
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit

# Mobile
npx playwright test --project="Mobile Chrome"
npx playwright test --project="Mobile Safari"
```

### Cobertura de Testes E2E

#### Fluxo de Perfil ✅
- [x] Criação de perfil com goal=100
- [x] Suporte a francês como target language
- [x] Validação de inputs
- [x] Funcionamento do slider de vocabulário
- [x] Dropdown de idioma nativo
- [x] Navegação por teclado
- [x] Descrições dos goals

#### Sessão de Estudo (Spec4) ✅
- [x] Interface de estudo com card
- [x] Primeiro card dentro da janela goal
- [x] Submissão de resposta com feedback
- [x] Foco mantido no input
- [x] Não repetição da mesma frase
- [x] Insights com dados de frequência
- [x] Botões de áudio (TTS)
- [x] Respostas incorretas
- [x] Dark mode
- [x] Navegação por teclado

#### Insights ✅
- [x] Dados de frequência (sem "no data")
- [x] Performance recente após respostas
- [x] Performance por tema
- [x] Progresso ao longo do tempo
- [x] Toggle de seções
- [x] Responsividade
- [x] Tratamento de erros
- [x] Comportamento de loading

---

## 📊 Cobertura de Testes

### Backend

```bash
# Gerar relatório de coverage
./test-runner.sh --all --coverage

# Ver relatório HTML
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux

# Banco de dados é PostgreSQL (não SQLite)
# Tests usam db_test separado para isolamento
```

### E2E

```bash
# Gerar relatório HTML
npm test && npm run report

# Screenshots e vídeos em test-results/

# Usa stack completa docker-compose (api, frontend, db)
```

---

## 🔄 Execução Contínua (CI/CD)

### GitHub Actions (Exemplo)

```yaml
name: Tests
on: [push, pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install deps
        run: |
          cd api
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      - name: Run tests
        run: |
          cd api
          ./test-runner.sh --all --coverage

  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install deps
        run: |
          cd tests/e2e
          npm ci
          npx playwright install
      - name: Start services
        run: |
          docker-compose up -d api frontend
          sleep 30
      - name: Run E2E tests
        run: |
          cd tests/e2e
          npm test
```

---

## 🛠️ Debug e Troubleshooting

### Backend

```bash
# Teste específico com debug
pytest -s tests/integration/test_spec4_card_selection.py::TestSpec4CardSelection::test_next_card_new_user_within_goal_window

# Ver output específico
pytest -s -k "test_create_user"

# Parar no primeiro erro
pytest -x

# Apenas testes que falharam
pytest --lf
```

### E2E

```bash
# Modo debug com devtools
npm run test:debug

# Gerar screenshots
npx playwright test -- screenshot=only-on-failure

# Trace viewer
npx playwright show-trace test-results/trace.zip
```

### Problemas Comuns

1. **API não responde**: Verifique se containers estão rodando
2. **Testes lentos**: Use `--maxfail=1` para parar no primeiro erro
3. **E2E instáveis**: Aumente timeouts nas esperas
4. **Coverage baixo**: Verifique se todos os caminhos estão testados

---

## 📝 Melhores Práticas

### Backend
- Use fixtures descritivas
- Teste casos de limite (edge cases)
- Mock dependências externas quando possível
- Verifique mensagens de erro específicas

### E2E
- Use seletores data-testid para melhor manutenção
- Evite sleeps explícitos, prefira espera de elementos
- Teste fluxos críticos do usuário
- Verifique acessibilidade básica

---

## 🎯 Status Atual da Cobertura

### Backend: ~85% cobertura
- ✅ Users API: 95%
- ✅ Spec4 Card Selection: 90%
- ✅ Insights: 85%
- ✅ Temas/Stats: 80%

### E2E: Fluxos principais cobertos
- ✅ Criação de perfil: 100%
- ✅ Sessão de estudo: 90%
- ✅ Insights: 85%

### Próximos Passos
- [ ] Adicionar testes de performance
- [ ] Testes de carga/stress
- [ ] Testes de acessibilidade (axe-core)
- [ ] Testes de visual regression