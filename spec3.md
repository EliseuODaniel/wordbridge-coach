itens a serem abordados:

1. Pequenas melhorias visuais (sem mudar o fluxo).
2. Novos componentes de informação por palavra (frequência + classe gramatical).
3. Novos gráficos de desempenho/temas do usuário.
4. Layout: onde tudo entra na tela.

---

## 1. Melhorias visuais na tela atual de estudo

### 1.1. Componente “StudyScreen” – ajustes de layout

**Objetivo:** manter o foco total na frase + input, mas polir a hierarquia visual.

**Especificação:**

* **Zona principal centralizada** continua sendo:

  * título `FillTheWord`;
  * subtítulo pequeno (`Learn vocabulary with smart spaced repetition`);
  * indicador de progresso (bolinhas) do card;
  * frase com lacuna;
  * tradução;
  * botão de dica (`Use the correct word`);
  * botões de áudio `Word` e `Sentence`.

* Ajustes finos:

  * **Tipografia**:

    * Título com tamanho levemente maior e peso mais forte;
    * Subtítulo com cor mais clara (cinza-azulado) e tamanho menor para não disputar com a frase;
    * Frase principal com tamanho maior que o input; tradução em itálico e menor que a frase.
  * **Card da frase**:

    * Envolver frase + lacuna + tradução + botões num “card” com fundo ligeiramente mais claro e bordas arredondadas, sombra suave.
    * Deixar a lacuna com **underline em destaque** (como já está) mas evitar o glow muito forte para não distrair.
  * **Área de input**:

    * Alinhar input + botão `Check` visualmente com o card central (mesma largura do card ou 60–70% da tela).
    * `Press Enter to submit` em cinza bem discreto, sem ocupar tanta atenção.
  * **Toasts de feedback (verde / vermelho)**:

    * Manter no canto inferior direito, mas garantir:

      * ícone consistente (check em círculo / X em círculo);
      * título em negrito, texto explicativo um pouco menor;
      * cores acessíveis (contraste suficiente).

Isso é tudo “UI spec”, não mexe em domínio.

---

## 2. Informação extra por palavra: frequência e gramática

### 2.1. Componente “WordFrequencyInsight”

**Objetivo:** mostrar **quão comum** é a palavra que o usuário está praticando, em relação às 10.000 palavras do app, com um gráfico tipo curva de vocabulário (como o print do Lingvist). Curvas de cobertura vs. frequência são padrão em estudos de vocabulário e seguem algo próximo à lei de Zipf: poucas palavras cobrem grande parte dos tokens.

#### Dados necessários

Já temos no spec:

* `WordFrequency` com `word`, `rank`, `frequency_score`.

**Extender**:

* adicionar campo `coverage_pct` (0–100), que representa a cobertura cumulativa até aquela palavra na lista (ex.: rank 1 cobre 5%, rank 100 cobre 50%, etc.).

Isso é calculado no pipeline de import de frequência:

```text
coverage_pct(rank k) = 100 * (soma freq_score[1..k] / soma freq_score[1..10000])
```

#### UI – comportamento

Nova seção embaixo do card principal (ver layout na seção 4):

**Card: “How common is this word?”**

* Gráfico de linha / área:

  * Eixo X: rank de 1 a 10.000 (preferencialmente escala log10 para caber bem: 1, 10, 100, 1k, 10k).
  * Eixo Y: cobertura cumulativa (%) de vocabulário.
  * Curva suave subindo rápido no início e achatando (forma esperada).
* Destaque da palavra atual:

  * Linha/agulha vertical no `rank` da palavra;
  * Bolinha sobre a curva com label:

    * `This word: rank #237 (top 3%)`
    * `Coverage up to here: 78% of word usage`
* Texto curto abaixo:

  * Ex.:
    `This word is among the 500 most frequent words in English.`
    ou
    `This word is in the less frequent half of your 10,000-word deck.`

Essa visualização é bem alinhada com a ideia de “coverage charts” usados em apps e estudos de vocabulário.

### 2.2. Componente “GrammarBadge”

**Objetivo:** trazer a classificação gramatical da palavra de forma compacta, como o “noun, plural” do Lingvist.

#### Dados

Já temos `grammar_hint` no domínio do `Card` (ex.: “noun, plural”, “verb, modal”).

#### UI – comportamento

* Abaixo da frase (logo acima da tradução), exibir um **badge**:

  * Estilo pill (fundo claro, texto escuro):

    * ex.: `verb, modal` ou `noun, plural`.
  * Quando o usuário ainda não respondeu:

    * opcional: permitir esconder/mostrar via pequeno ícone de “olho”, se você quiser transformar isso em configuração (para quem quer estudar sem dica).
* Se quiser ir além no futuro:

  * Ao clicar, poderia abrir um dropdown com explicação rápida (ex.: “modal verbs express ability, possibility, etc.”), mas isso pode ir para outra fase.

---

## 3. Painel de desempenho e temas (learning analytics light)

Agora a parte nerd de analytics 😎
Em vez de só mostrar acertos/erros, vamos criar uma área de **insights** com 3 gráficos:

1. **Desempenho recente em tempo quase real**;
2. **Mapa de temas (clusters de palavras)** mostrando onde o usuário mais erra/acerta;
3. **Evolução ao longo do tempo**.

Boa parte da literatura de learning analytics recomenda dashboards que combinem indicadores de desempenho, engajamento e evolução em gráficos simples, mas interpretáveis.

### 3.1. Dados de temas / clusters

Antes dos gráficos, a spec precisa de um conceito de “tema” para cada palavra.

#### Nova entidade: `WordTheme`

```markdown
### Entidade: WordTheme

- id: PK
- name: string (ex.: "Daily actions", "Travel", "Emotions", "Food", "Business")
- description: string (opcional)
```

#### Relação palavra–tema

```markdown
### Entidade: WordThemeMapping

- word_id: FK(Word)
- theme_id: FK(WordTheme)
- weight: float (0..1) (opcional, se quiser suportar temas múltiplos)
```

**Como preencher isso na prática:**

* MVP simples:

  * definir manualmente temas + mapping para um subconjunto de palavras prioritárias;
* Versão mais esperta:

  * usar embeddings / topic modeling (tipo LDA ou clustering de vetores) para agrupar palavras em temas sem supervisão, inspirando-se em técnicas de visualização de tópicos como LDAvis.

---

### 3.2. Gráfico 1 – “Desempenho recente”

**Nome de componente:** `RecentPerformanceChart`

**Objetivo:** dar feedback instantâneo se a sessão atual está indo bem ou não.

**Especificação:**

* Localização: na seção de insights, logo abaixo da dobra, em uma linha com no máximo dois gráficos lado-a-lado em desktop.
* Dados:

  * últimas N respostas do usuário (ex.: 30);
  * para cada resposta: timestamp, `was_correct`, `quality`, `response_time_ms`.
* Visual:

  * pequeno **gráfico de linha** ou **sparkline**:

    * eixo X: ordem das respostas (ou tempo);
    * eixo Y: taxa de acerto acumulada ou média móvel (por exemplo, janela de 10 respostas).
  * Alternativamente: gauge tipo “session accuracy” com valor percentual + tendência:

    * `Accuracy (last 30 cards): 76% ↑` (seta verde se melhor que média histórica, vermelha se pior).

---

### 3.3. Gráfico 2 – “Mapa de temas (clusters)”

**Nome de componente:** `ThemeClusterMap`

**Objetivo:** mostrar **em quais temas** o usuário está indo bem ou mal, de forma visual e intuitiva.

**Dados agregados por usuário e tema:**

Criar `UserThemeStats` (podendo ser view materializada ou tabela):

```markdown
### Entidade: UserThemeStats

- user_id: FK(User)
- theme_id: FK(WordTheme)
- attempts: int
- correct: int
- accuracy: float (= correct / attempts)
- avg_response_time_ms: float
- last_practiced_at: datetime
```

**Visualização sugerida:**

* Tipo: **bubble chart / scatter plot** (cluster visual simples):

  * Cada **bolha** = um tema (`WordTheme`).
  * **Posição**:

    * Eixo X: `accuracy` (0–100%).
    * Eixo Y: opcionalmente `avg_response_time_ms` (ou deixar Y fixo e usar grade).
  * **Tamanho da bolha**: número de `attempts` (quanto maior o círculo, mais praticado).
  * **Cor**:

    * gradiente de vermelho → amarelo → verde conforme a accuracy;
    * temas problemáticos: grandes e vermelhos (muitos erros).
* Ao passar o mouse / tocar:

  * mostrar tooltip com:

    * nome do tema;
    * accuracy, número de tentativas;
    * top 3 palavras mais erradas naquele tema (listar).

Isso encaixa muito bem na ideia de “cluster visualization” de erros, que é recomendada em visual analytics para ajudar a diagnosticar padrões de dificuldade.

---

### 3.4. Gráfico 3 – “Evolução ao longo do tempo”

**Nome de componente:** `ProgressOverTimeChart`

**Objetivo:** mostrar **ganho de vocabulário** + melhoria de desempenho ao longo dos dias.

**Dados por usuário e dia:**

Criar (ou derivar de uma view) `UserDailyStats`:

```markdown
### Entidade: UserDailyStats

- user_id: FK(User)
- date: date
- cards_answered: int
- new_words_learned: int        # palavras que passaram certo limiar de mastery nesse dia
- reviews_done: int
- accuracy: float               # taxa de acerto naquele dia
- cumulative_mastered_words: int
```

**Visual:**

* Gráfico composto:

  * **Linha 1**: `cumulative_mastered_words` ao longo do tempo (eixo Y esquerda).
  * **Linha 2** ou barras: `accuracy` por dia (eixo Y direita ou escala secundária).
* Extras:

  * highlight em dias com muitas respostas (`cards_answered` muito alto);
  * eventual meta diária (“target 50 cards”) em linha horizontal.

Esse tipo de gráfico é bem típico de dashboards de learning analytics: mistura de tendência de desempenho com engajamento.

---

## 4. Layout: onde esses gráficos entram na tela

**Objetivo:** seguir seu pedido — insights **embaixo** da tela, sem atrapalhar o fluxo principal de responder cards.

### 4.1. Organização em seções

Na especificação de UI, defina a StudyScreen com **três blocos verticais**:

1. **Header e título**

   * Logo/“FillTheWord” + subtítulo.

2. **Zona de prática** (acima da dobra)

   * Progresso (bolinhas).
   * Card da frase + tradução + GrammarBadge + botão de dica + botões de áudio.
   * Input e botão `Check`.
   * Toasts de feedback à direita.

3. **Zona de Insights** (abaixo da frase e input, com scroll se necessário)

   * Subtítulo: `Insights for this word & your progress`.
   * Uma grade 2x2 (em desktop):

     * Linha 1:

       * `WordFrequencyInsight` (como comum é essa palavra);
       * `RecentPerformanceChart`.
     * Linha 2:

       * `ThemeClusterMap`;
       * `ProgressOverTimeChart`.
   * Em mobile:

     * os quatro gráficos empilhados verticalmente.

Opcional: permitir **esconder/mostrar** a zona de Insights com um pequeno caret (“Show insights ▾ / Hide insights ▴”). Isso mantém a tela super limpa pra quem só quer “modo treino”.

---

## 5. Como isso entra no OpenSpec

Resumindo o que você pode literalmente transformar em spec:

* Em `DOMAINS.md`:

  * adicionar `WordTheme`, `WordThemeMapping`, `UserThemeStats`, `UserDailyStats` (podem ser descritos como tabelas físicas ou views derivadas de `ReviewEvent` + `UserCardState`);
  * extender `WordFrequency` com `coverage_pct`.
* Em `SPEC.md`:

  * adicionar seção “Word insights (frequency & grammar)” com:

    * objetivo dos componentes `WordFrequencyInsight` e `GrammarBadge`.
  * adicionar seção “Learning analytics dashboards” com:

    * objetivos e descrição dos gráficos `RecentPerformanceChart`, `ThemeClusterMap`, `ProgressOverTimeChart`.
* Em `ARCH.md`:

  * anotar que os dados agregados (`UserThemeStats`, `UserDailyStats`) podem ser recalculados:

    * on-the-fly via queries,
    * ou via jobs periódicos (ex.: job diário que atualiza stats agregados).
* Em `API.md`:

  * endpoints tipo:

    * `GET /api/insights/word/{word_id}` → dados de frequência, cobertura, grammar_hint;
    * `GET /api/insights/user/{user_id}/themes`;
    * `GET /api/insights/user/{user_id}/daily`.









## implementação dos gráficos:




1. Que dados serão coletados (base para todos os analytics)
2. Como calcular cada gráfico “simples” (sem ML)
3. Modelo de ML p/ **clusters de temas** (mapa de erros por tema)
4. Modelo de ML p/ **dificuldade / probabilidade de acerto**
5. Como isso fica implementado na arquitetura (pastas, containers, jobs)

---

## 1. Base de dados para analytics

Tudo nasce de um **log de tentativas**.
Você já tem algo tipo `ReviewEvent`; vamos detalhar o mínimo que precisa:

### 1.1. Tabela `review_events`

Cada tentativa de preencher a lacuna gera uma linha:

* `id`
* `user_id`
* `card_id`
* `word_id` (palavra alvo)
* `theme_id` (ou `cluster_id` – ver seção 3)
* `created_at` (timestamp)
* `answer_text`
* `was_correct` (bool)
* `quality` (0–5, vindo do SRS)
* `response_time_ms`
* `session_id` (id da sessão de estudo, opcional)

Essa tabela é **o único “ground truth”** para todos os analytics.

### 1.2. Tabela `word_frequency`

Pega a lista das 10k palavras mais frequentes do inglês:

* Pode usar o repositório `google-10000-english`, que traz 10.000 palavras em ordem de frequência, baseado no Google Trillion Word Corpus.
* Ou uma lista exportada da biblioteca **wordfreq**, que dá frequências estimadas para ~400k palavras em dezenas de idiomas.

Estrutura:

* `word_id` (FK para `words`)
* `rank` (1..10000)
* `raw_freq` (float – vindo do wordfreq ou similar)
* `coverage_pct` (vamos calcular na preparação dos dados)

---

## 2. Analytics “clássicos”: como calcular, sem ML

### 2.1. Gráfico “frequência/cobertura da palavra” (WordFrequencyInsight)

**Ideia:** mostrar quão cedo aquela palavra aparece em uma lista ordenada de frequência e qual % de “cobertura de uso” ela representa.

**Pré-processamento (rodado 1x num script ETL offline):**

1. Carrega a lista de frequências (por exemplo, JSON do `wordfreq-en-25000` ou a lista de 10k palavras).

2. Ordena por `raw_freq` decrescente (ou usa a ordem já dada).

3. Normaliza os pesos:

   [
   p_i = \frac{f_i}{\sum_{j=1}^{N} f_j}
   ]

4. Calcula a cobertura acumulada:

   [
   coverage_pct_i = 100 \times \sum_{j=1}^{i} p_j
   ]

5. Salva na tabela `word_frequency` os campos `rank=i`, `raw_freq=f_i`, `coverage_pct_i`.

**Na hora do gráfico:**

* X: rank (1 a 10k, em escala log se quiser);
* Y: `coverage_pct`.
* Para a palavra atual (`word_id`), pega `rank` e `coverage_pct` e desenha o marcador.

Nada de ML aqui, só estatística básica.

---

### 2.2. Gráfico “desempenho recente” (RecentPerformanceChart)

**Objetivo:** mostrar se a sessão atual está boa ou ruim.

**Cálculo:**

Para um usuário `u`:

1. Pega as últimas `N` linhas de `review_events` (ex.: `N=50`, ordenado por `created_at DESC`).

2. Define uma **janela móvel** de tamanho `k` (ex.: 10 tentativas):

   * Para cada posição `t` na sequência, calcula:

     [
     accuracy_t = \frac{\text{nº de acertos na janela }[t-k+1, t]}{k}
     ]

3. Opcional: calcula um **EMA** (média móvel exponencial) de acurácia para suavizar:

   * `ema_t = α * was_correct_t + (1-α) * ema_{t-1}`, com `α` ~ 0.1.

O gráfico pode ser:

* uma linha `accuracy_t` ou `ema_t` ao longo dos últimos N cards;
* ou um único número agregado:

  [
  accuracy_{recent} = \frac{\sum was_correct}{N}
  ]

Ainda sem ML: é só agregação de eventos.

---

### 2.3. Gráfico “evolução ao longo do tempo” (ProgressOverTimeChart)

**Objetivo:** acompanhar crescimento de vocabulário e acurácia diária.

**Batch diário (job de agregação):**

Cria/atualiza `user_daily_stats` com:

```sql
INSERT INTO user_daily_stats (user_id, date, cards_answered, new_words_learned,
                              reviews_done, accuracy, cumulative_mastered_words)
SELECT
  user_id,
  DATE(created_at) as date,
  COUNT(*) as cards_answered,
  SUM(CASE WHEN became_mastered_here THEN 1 ELSE 0 END) as new_words_learned,
  COUNT(*) as reviews_done,
  AVG(CASE WHEN was_correct THEN 1.0 ELSE 0.0 END) as accuracy,
  -- cumulative_mastered_words pode ser mantido num campo separado e atualizado via job incremental
FROM review_events
WHERE created_at BETWEEN :start AND :end
GROUP BY user_id, DATE(created_at);
```

A flag `became_mastered_here` vem do SRS: é verdadeira quando o `mastery_score` (ou status NEW→MATURE) cruza o limiar pela 1ª vez naquele dia.

Gráfico:

* Linha 1: `cumulative_mastered_words` vs `date`.
* Linha 2/barras: `accuracy` vs `date`.

De novo, só agregação.

---

## 3. ML para agrupar temas (clusters) e alimentar o “ThemeClusterMap”

Aqui entra ML de verdade.

### 3.1. Vetores de palavras (embeddings)

Para transformar cada palavra em um vetor de significado, use um embedding de palavra pré-treinado, por exemplo **fastText**:

* fastText distribui vetores para inglês e mais 157 línguas, treinados em Common Crawl + Wikipedia; cada palavra vira um vetor de 300 dimensões.

**Pré-processamento:**

1. Baixar os vetores de inglês (`cc.en.300.bin` ou `.vec`) no build do container de analytics.
2. Carregar o modelo no script de treino:

   * Para cada palavra da sua lista de 10k, pegar o vetor `e_w` (300d).
   * Se uma palavra não existir, usar subword do fastText (ele suporta isso), ou pular.

### 3.2. Redução de dimensionalidade: UMAP

300 dimensões é muito para clusterização direta; reduzimos:

* Usar **UMAP** (`umap-learn`), que é bem usado para clustering de texto: preserva estrutura local/global melhor que PCA em embeddings de alta dimensão.

Pipeline:

```python
umap = UMAP(n_components=10, n_neighbors=15, min_dist=0.1)
E_10d = umap.fit_transform(E_300d)  # E_300d é matriz [num_words x 300]
```

Armazena o modelo UMAP treinado para poder projetar novas palavras se precisar.

### 3.3. Clustering: HDBSCAN

Para achar “temas” automaticamente:

* Usar **HDBSCAN**, um algoritmo de clusterização por densidade, robusto a clusters de tamanhos diferentes e ruído. Ele é recomendado em pipelines modernos de text clustering e é parte central de soluções como BERTopic.

Pipeline:

```python
clusterer = HDBSCAN(
    min_cluster_size=20,
    min_samples=5,
    metric="euclidean"
)
labels = clusterer.fit_predict(E_10d)
```

* Cada palavra recebe um `cluster_id` (`labels[i]`).
* Palavras com `cluster_id = -1` são ruído; você pode:

  * jogar num cluster “Miscellaneous”,
  * ou deixá-las sem tema.

### 3.4. Transformando clusters em “temas”

A partir dos clusters:

* Para cada `cluster_id`:

  * pegar top ~20 palavras mais centrais (menor distância ao centróide);
  * usar essas palavras para:

    * gerar automaticamente um nome de tema via LLM **offline** (ou manualmente),
    * ou manter nomes genéricos (“Cluster 1”, “Cluster 2”) no MVP.

Esses clusters viram registros em `word_theme`:

* `theme_id = cluster_id`
* `name` = rótulo (“Daily actions”, “Travel”, etc.)
* `description` opcional.

E `word_theme_mapping` vira basicamente `word_id -> theme_id`.

### 3.5. Atualizando estatísticas por tema

Sempre que uma tentativa é salva em `review_events`:

* olhar `theme_id` da palavra;
* atualizar (ou recomputar por batch) `user_theme_stats`:

```sql
INSERT INTO user_theme_stats (user_id, theme_id, attempts, correct, accuracy, avg_response_time_ms)
VALUES (...)
ON CONFLICT (user_id, theme_id) DO UPDATE SET
  attempts = user_theme_stats.attempts + 1,
  correct  = user_theme_stats.correct + (CASE WHEN was_correct THEN 1 ELSE 0 END),
  accuracy = correct / attempts,
  avg_response_time_ms = -- média incremental
    (user_theme_stats.avg_response_time_ms * (attempts - 1) + new_response_time_ms) / attempts;
```

O gráfico `ThemeClusterMap` usa só esses agregados; o “ML pesado” já aconteceu antes na etapa de clustering.

---

## 4. ML para dificuldade / probabilidade de acerto

Isso é um luxo, mas deixa o app nível artigo de Learning Analytics 😄

### 4.1. Por que um modelo preditivo?

Estudos de dashboards de learning analytics mostram que a maioria só usa **métricas descritivas**, mas que dashboards mais avançados começam a usar **modelos preditivos** (regressão, ensembles, redes) para estimar risco/dificuldade e gerar insights acionáveis.

Aqui a ideia é: dado um card e um usuário, estimar:

> ( P(\text{acertar na próxima tentativa}) )

e usar isso para:

* colorir cards/temas (“Hard / Medium / Easy”);
* enriquecer gráficos (ex.: comparação performance real vs esperada).

### 4.2. Modelo sugerido

Para rodar **localmente** sem GPU e ser interpretável, a escolha natural é:

* **Regressão logística** (binária) usando `scikit-learn`.

Ela é padrão em LA justamente por ser simples, previsível e explicável.

Alvo:

* `y = was_correct` (0 ou 1) na próxima tentativa.

Features (exemplos):

1. **Da palavra:**

   * `log_rank` (log do rank de frequência),
   * `zipf_freq` ou `log(raw_freq)`,
   * one-hot de `part_of_speech`,
   * `cluster_id` / `theme_id` (one-hot ou embedding categorico),
   * comprimento da palavra (número de caracteres).

2. **Do usuário + palavra (estado de SRS):**

   * `repetitions`, `easiness_factor`, `interval_days`,
   * `days_since_last_review`,
   * `mastery_score`.

3. **Histórico recente:**

   * acurácia das últimas `k` tentativas daquela palavra,
   * tempo médio de resposta nas últimas `k` tentativas.

4. **Perfil do usuário:**

   * total de palavras dominadas,
   * acurácia global,
   * tempo médio de resposta global.

### 4.3. Treino

Script `train_difficulty_model.py`:

1. Consulta o banco para obter um dataset com milhares de `review_events` históricos, juntando as features acima.
2. Divide em treino/validação (ex.: 80/20).
3. Treina:

   ```python
   model = LogisticRegression(
       max_iter=1000,
       class_weight="balanced"
   )
   model.fit(X_train, y_train)
   ```
4. Avalia com AUC/ROC, log-loss, etc.
5. Salva pesos e metadados:

   * `models/difficulty_model.pkl`
   * `models/difficulty_features.json` (ordem das features, normalizações).

Esse script roda em um container (ou comando manual) quando você quiser atualizar o modelo.

### 4.4. Inferência online

Na API:

1. Ao buscar um card para mostrar, a API também monta o vetor de features `x` para aquele `(user, card)`.

2. Chama:

   ```python
   p_correct = model.predict_proba([x])[0, 1]
   ```

3. Devolve no payload do card algo como:

   ```json
   {
     "expected_success_prob": 0.78,
     "difficulty_bucket": "medium"
   }
   ```

4. Os gráficos podem usar isso, por exemplo:

   * `ThemeClusterMap`: cor baseada na diferença entre acurácia real por tema e acurácia prevista (onde você está indo pior ou melhor que o esperado).
   * `ProgressOverTimeChart`: linha adicional com “acurácia prevista média” vs “acurácia real”.

---

## 5. Onde tudo mora na arquitetura (containers / código)

### 5.1. Novo container ou módulo de “analytics”

Você pode fazer de dois jeitos:

1. **Módulo dentro da API** (mais simples):

   * Pasta `backend/analytics/` com:

     * `features.py` (monta features a partir do DB),
     * `train_word_clusters.py`,
     * `train_difficulty_model.py`,
     * `online_metrics.py` (funções para RecentPerformanceChart, etc.).
   * A API expõe endpoints:

     * `GET /api/insights/word/{word_id}`
     * `GET /api/insights/user/{user_id}/themes`
     * `GET /api/insights/user/{user_id}/daily`

2. **Worker separado** (mais limpo, mas mais infra):

   * Container `analytics-worker` que roda scripts de ETL e treino;
   * API só lê as tabelas agregadas e modelos prontos.

Para o MVP, módulo dentro da API é suficiente.

### 5.2. Dependências de ML no container

No `Dockerfile` do backend, garantir libs:

* `numpy`, `pandas`
* `scikit-learn`
* `umap-learn`
* `hdbscan`
* `wordfreq`
* `fasttext` (ou `gensim` para carregar `.vec`)

Todas são CPU-friendly para o tamanho do problema (10k palavras, alguns milhares de eventos).

---

## 6. Resumão “de engenheiro”

Em termos de especificação:

* **Dados:**

  * `review_events` é o log central, de onde sai tudo.
  * `word_frequency` dá rank + freq + coverage.
  * `word_theme_mapping` vem de **fastText → UMAP → HDBSCAN**.
  * `user_theme_stats` e `user_daily_stats` são tabelas agregadas.

* **Analytics sem ML:**

  * frequência/cobertura da palavra (curva de cobertura);
  * desempenho recente (janela móvel / EMA de acertos);
  * evolução no tempo (agregação diária).

* **Analytics com ML:**

  * **Clusters de temas**:

    * fastText embeddings → UMAP (10d) → HDBSCAN → `theme_id por palavra`.
  * **Modelo de dificuldade**:

    * regressão logística usando features de frequência + SRS + usuário;
    * previsão de `P(correct)` por card.

* **Implementação:**

  * scripts de ETL/treino em `backend/analytics/`;
  * modelos salvos em `backend/models/*.pkl`;
  * API expose endpoints `/api/insights/...`;
  * frontend consome esses dados para desenhar os três gráficos lá embaixo, em tempo quase real.

C