
* meta de **10.000 palavras mais frequentes** do inglês;
* fonte sugerida de frequência;
* estratégia **inteligente** de seleção de palavra (frequência + desempenho do usuário + SRS);
* **perfis de usuário** tipo Netflix, com persistência mesmo derrubando o container;
* sem a frase “preencha com a palavra correta”.

---

## 1. Fonte de dados: 10.000 palavras mais frequentes

### 1.1. Decisão de produto

**Objetivo didático** do FillTheWord:

> Praticar as **10.000 palavras mais frequentes da língua inglesa**, priorizando as mais comuns e mais úteis no início do aprendizado, e progressivamente introduzindo palavras menos frequentes conforme o usuário demonstra domínio.

### 1.2. Especificação da lista de frequência

**Requisito de dados:**

* O sistema deve possuir um **dicionário de frequência** contendo pelo menos as **10.000 palavras mais frequentes em inglês**, ordenadas por frequência (da mais comum para a menos comum).
* Cada entrada deve conter:

  * `word` – forma canônica (lowercase, sem pontuação);
  * `rank` – inteiro de 1 a 10.000 (1 = mais frequente);
  * opcional: `frequency_score` (frequência relativa ou log-frequência).

**Fonte sugerida (implementação):**

* Utilizar a lista **google-10000-english**, disponível em repositório open-source, que traz as 10.000 palavras mais comuns em inglês, ordenadas por frequência a partir do Google Trillion Word Corpus.
* Alternativamente, pode-se derivar a lista das bibliotecas de frequência como `wordfreq`, que expõem listas de palavras com frequências baseadas em corpora grandes e modernos.

No spec você pode registrar algo assim em `DOMAINS.md`:

```markdown
### Entidade: WordFrequency

- word: string (chave primária lógica, minúscula)
- rank: int (1..10000)
- frequency_score: float (opcional, score normalizado/logarítmico)
```

---

## 2. Estratégia inteligente de seleção de palavras

### 2.1. Objetivo

O algoritmo de seleção de cards deve:

1. **Priorizar palavras de alta frequência** (ranks mais baixos) nos estágios iniciais;
2. **Introduzir gradualmente palavras menos frequentes** conforme o usuário demonstra domínio das mais frequentes;
3. **Aumentar a probabilidade de palavras que o usuário erra**;
4. **Reduzir a probabilidade de palavras que o usuário domina**, mantendo-as apenas conforme o SRS exigir revisões;
5. Trabalhar **em conjunto** com o motor de SRS (SM-2) já definido.

### 2.2. Bandas de frequência

Definir “bandas” de frequência (configuráveis) para controlar a progressão:

* **Banda 1**: ranks 1–1000 (palavras mais frequentes)
* **Banda 2**: ranks 1001–3000
* **Banda 3**: ranks 3001–6000
* **Banda 4**: ranks 6001–10000

Esses valores são parâmetros; podem ser ajustados no futuro, mas o comportamento base é:

* O usuário **inicia** tendo acesso apenas à **Banda 1** como fonte de palavras novas.
* Conforme atinge **marcos de domínio** (ex.: 70% das palavras da banda com status “MATURE”), a próxima banda é parcialmente “aberta”.

### 2.3. Estado por usuário e palavra

Adicionar uma entidade de estatísticas por usuário e palavra (pode ser junto ou separada de `UserCardState`):

```markdown
### Entidade: UserWordStats

- user_id: FK(User)
- word_id: FK(Word)
- total_attempts: int
- correct_attempts: int
- last_result: enum {CORRECT, INCORRECT}
- mastery_score: float (0.0 — 1.0)
  - derivado de taxa de acerto + tempo de resposta + qualidade do SRS
```

**Regra de atualização (simplificada):**

* A cada resposta:

  * `total_attempts += 1`
  * se correto: `correct_attempts += 1`
* `mastery_score` calculado como, por exemplo:

> `mastery_score = min(1.0, max(0.0, correct_attempts / total_attempts * ajuste_SRS))`

onde `ajuste_SRS` pode ser um fator baseado no intervalo de revisão (palavras com espaçamentos longos tendem a ser mais dominadas).

### 2.4. Algoritmo de seleção (especificação conceitual)

Quando o backend precisa decidir **qual card mostrar a seguir**:

1. **Montar conjunto de candidatos**

   * Todos os cards **em revisão** cujo `next_review_at <= now()` (SRS).
   * Um número limitado de cards **novos** (ex.: até N novos por sessão), escolhidos dentro das bandas já desbloqueadas.

2. **Definir pesos de prioridade por card**

Para cada card candidato, calcular um **score de prioridade** que combina:

* **Urgência de revisão (SRS)**
  Quanto mais atrasado em relação a `next_review_at`, maior o peso.
* **Importância por frequência**
  Palavras com `rank` mais baixo (mais frequentes) têm peso base maior.
* **Dificuldade individual**
  Palavras com `mastery_score` baixo ou muitos erros recentes ganham peso extra.
* **Novidade controlada**
  Palavras completamente novas ganham um peso inicial, limitado pelo “cap” de palavras novas na sessão.

Em spec (pseudocódigo conceitual):

```text
priority(card) =
  w_srs   * f_srs(overdue_time) +
  w_freq  * f_freq(rank) +
  w_diff  * f_diff(mastery_score) +
  w_new   * f_new(is_new_card)
```

Onde:

* `f_freq(rank)` deve decrescer com o rank (ex.: `1 / rank^alpha`).
* `f_diff(mastery_score)` deve ser maior para scores próximos de 0 (palavras problemáticas).
* `f_new(is_new_card)` é >0 apenas para cards novos, respeitando limite diário.

3. **Amostragem estocástica**

* Em vez de sempre pegar o maior score, o sistema faz uma **amostra ponderada**:

  * normaliza os `priority(card)` em uma distribuição de probabilidade,
  * sorteia 1 card com base nessa distribuição.
* Isso garante que:

  * cards prioritários aparecem mais,
  * mas ainda há variabilidade (não vira “lista fixa”).

### 2.5. Abertura progressiva das bandas

Regra por usuário:

* Cada banda `Bi` tem critérios de desbloqueio (por ex.: % de `Word`s da banda anterior com `mastery_score ≥ threshold`).
* Enquanto uma banda não estiver desbloqueada:

  * **não** são criados novos cards daquelas palavras para aquele usuário.
* Depois de desbloqueada, o algoritmo de seleção passa a considerar palavras daquela banda como **candidatas a serem introduzidas como novas**, respeitando um **limite de palavras novas por sessão**.

---

## 3. Usuários, perfis e persistência local

### 3.1. Objetivo

* Permitir que **vários usuários** utilizem o FillTheWord na mesma máquina:

  * ao iniciar o app, o usuário escolhe um perfil existente ou cria um novo (experiência tipo “Netflix”).
* Todo o histórico de:

  * cards vistos,
  * respostas,
  * progresso de SRS,
  * estatísticas de banda,

  é **persistido** em banco de dados local e **não é perdido** mesmo que os containers sejam derrubados e inicializados novamente.

### 3.2. Entidade User (revisada)

```markdown
### Entidade: User

- id: PK
- display_name: string (nome que aparece na tela inicial)
- created_at: datetime
- native_language_id: FK(Language) (ex.: pt-BR)
- target_language_id: FK(Language) (ex.: en)
- settings_json: json (preferências: volume, auto-play de áudio, limite diário de novos cards etc.)
```

### 3.3. Fluxo de seleção/criação de usuário

Novo requisito funcional (RF-0X):

* Ao abrir o FillTheWord:

  * Se **não existirem usuários**:

    * mostrar tela de **criação de perfil** (nome + idiomas).
  * Se já existirem usuários:

    * mostrar uma tela com “cartões de perfil” (lista de `display_name`),
    * permitir:

      * clicar em um usuário existente para entrar,
      * ou clicar em “Adicionar novo usuário” para criar outro perfil.

Depois da seleção do usuário, **toda a sessão** (cards, SRS, seleção de palavras) é atrelada ao `user_id` escolhido.

### 3.4. Persistência entre reinícios de container

Atualizar `ARCH.md` com o seguinte requisito:

* O serviço de banco de dados (`db`) deve usar um **volume persistente** mapeado para o host, por exemplo:

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: filltheword
      POSTGRES_USER: filltheword
      POSTGRES_PASSWORD: change_me
    volumes:
      - ./data/db:/var/lib/postgresql/data
```

* As tabelas de:

  * `users`
  * `words`, `word_frequency`
  * `sentences`, `cards`
  * `user_card_state`, `user_word_stats`, `reviews`

  devem estar todas nesse banco, garantindo que:

> Derrubar e subir o `docker compose` **não apaga** o progresso dos usuários.

---

## 4. Ajuste na UI: remoção de texto específico

Você pediu para **remover a frase** `"preencha com a palavra correta"`.

Na especificação de UI (onde você descreve o layout do card), ajuste para algo mais neutro, por exemplo:

* Antes (remover):

  > Texto em destaque “preencha com a palavra correta” acima do campo.

* Depois (exemplo opcional):

  > Campo de input logo abaixo da frase com lacuna, sem texto instrucional fixo.
  > Placeholder simples como `"type the missing word..."` (ou deixar sem placeholder).

Na spec (UI/UX), apenas certifique-se de que não existe mais a literal `"preencha com a palavra correta"`.

---

## 5. Bloco de SPEC pronto para colar (resumido)

Abaixo um bloco que você pode colocar em `SPEC.md` como nova seção:

```markdown
## Objetivo de vocabulário

FillTheWord tem como objetivo principal praticar as **10.000 palavras mais frequentes da língua inglesa**, priorizando o domínio progressivo das palavras de maior frequência antes de introduzir palavras menos frequentes.

Para isso, o sistema mantém um dicionário de frequência (`WordFrequency`) contendo pelo menos 10.000 entradas, cada uma com:

- `word`: forma canônica (lowercase)
- `rank`: inteiro de 1..10000 (1 = palavra mais frequente)
- `frequency_score`: opcional, score de frequência normalizado

A fonte de dados pode ser qualquer lista open-source que contenha as 10.000 palavras mais frequentes do inglês, ordenadas por frequência (por exemplo, listas derivadas de grandes corpora como o Google Trillion Word Corpus).

## Seleção de palavras e cards

A seleção de cards para estudo é guiada por três princípios:

1. **Revisão espaçada (SRS)**: cards com `next_review_at <= now()` têm prioridade.
2. **Importância por frequência**: palavras com rank mais baixo (mais comuns) são priorizadas.
3. **Adaptação ao usuário**: palavras difíceis para o usuário aparecem com mais frequência.

O vocabulário é dividido em bandas de frequência:

- Banda 1: ranks 1–1000
- Banda 2: ranks 1001–3000
- Banda 3: ranks 3001–6000
- Banda 4: ranks 6001–10000

O usuário inicia com acesso a novas palavras somente na Banda 1. Bandas posteriores são desbloqueadas quando o usuário atinge um limiar de domínio (por exemplo, X% das palavras da banda anterior com `mastery_score` acima de um threshold).

Para cada usuário e palavra, o sistema mantém estatísticas (`UserWordStats`):

- `total_attempts`, `correct_attempts`
- `last_result`
- `mastery_score` em [0.0, 1.0]

A cada resposta, `UserWordStats` é atualizado.

Ao decidir o próximo card, o backend:

1. Monta um conjunto de candidatos:
   - cards em revisão (`next_review_at <= now()`);
   - cards novos elegíveis, dentro das bandas já desbloqueadas, respeitando um limite de novos por sessão/dia.
2. Calcula um score de prioridade para cada card combinando:
   - urgência do SRS,
   - importância de frequência (rank),
   - dificuldade (mastery_score baixo ou muitos erros recentes),
   - fator de novidade.
3. Seleciona o próximo card por amostragem ponderada com base nesses scores.

Como resultado:

- palavras mais frequentes e ainda não dominadas aparecem com maior probabilidade;
- palavras que o usuário já domina aparecem apenas quando o SRS pede revisão;
- palavras frequentemente erradas aparecem mais vezes até que a dificuldade caia.

## Perfis de usuário e persistência

FillTheWord suporta múltiplos usuários locais. Na inicialização:

- se não existirem usuários, o app exibe a tela de criação de perfil;
- se existirem usuários, o app exibe a tela de seleção de perfil (lista de usuários existentes + opção de criar novo).

Todas as estruturas de dados (users, cards, estados de SRS, estatísticas) são persistidas em um banco de dados relacional (ex.: Postgres) armazenado em volume Docker montado no host. Derrubar e reiniciar os containers não deve apagar o progresso dos usuários.

A tela de estudo do card exibe:

- frase com lacuna,
- tradução,
- dica gramatical,
- campo de input para digitar a palavra,
- botões de áudio (palavra e frase).

Não há texto fixo “preencha com a palavra correta” na UI.
```
