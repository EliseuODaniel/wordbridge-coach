---

## Prompt final para Claude – FillTheWord (versão corrigida)

Você é um dev sênior (backend + frontend) trabalhando no app **FillTheWord**, um clone local do Lingvist.

### Contexto do projeto

* App: **FillTheWord**.
* Stack: frontend em **React + TypeScript + Tailwind**, backend em **Python/FastAPI** (ou análogo) com banco relacional.
* Já existem:

  * lista de ~10.000 palavras em inglês, ordenadas por frequência (rank 1 = mais comum);
  * SRS simples (SM-2) por card/palavra;
  * tela de estudo com:

    * frase com lacuna,
    * tradução,
    * input de resposta,
    * botões de áudio para palavra e frase,
    * card “How common is this word?” com curva de cobertura cumulativa (Zipf-like);
  * tela de seleção de usuário (profiles).

Quero que você implemente **três grandes blocos de funcionalidade**:

1. **Variedade de frases por palavra** (sempre frases novas ou pouco repetidas).
2. **Progressão de palavras em ordem de frequência**, com janela dinâmica (100 → 200 → 300…) e mistura inteligente de novas/revisões, no estilo Lingvist.
3. **Configuração de objetivo de vocabulário por usuário + ajustes de UI** na tela de estudo.

---

## 1. Variedade de frases por palavra (sempre novas)

### 1.1. Objetivo

* A **mesma palavra** deve aparecer em **muitas frases diferentes** ao longo do tempo:

  * frases curtas, expressões comuns, frases de livros, citações simples, etc.;
  * frases podem vir de corpus ou ser geradas, mas sempre coerentes.
* O ideal é que, para o usuário, **cada tentativa traga uma frase nova** (ou pelo menos não repetida recentemente).
* As **palavras** podem se repetir (por causa do SRS), mas **as frases devem variar**.

### 1.2. Modelo de domínio

Se ainda não existir, crie as seguintes entidades (adapte ao ORM):

```ts
// tabela de frases
Sentence {
  id: string;
  languageCode: string;        // "en"
  text: string;                // "She can stand very well."
  translation: string | null;  // "Ela pode ficar de pé muito bem."
  grammarHint: string | null;  // "verb, base form", etc.
  sourceType: "corpus" | "generated" | "manual";
  difficulty: number;          // 1..5, opcional
  createdAt: Date;
}

// vínculo palavra–frase
WordSentence {
  id: string;
  wordId: string;              // FK Word
  sentenceId: string;          // FK Sentence
  isPrimary: boolean;          // se quiser marcar 1 exemplo "principal"
}
```

No log de estudo, garantir que `sentenceId` é salvo:

```ts
ReviewEvent {
  id: string;
  userId: string;
  wordId: string;
  sentenceId: string;          // NOVO: qual frase foi usada
  createdAt: Date;
  wasCorrect: boolean;
  quality: number;             // 0..5
  responseTimeMs: number;
}
```

### 1.3. Seleção de frase para uma palavra

Implementar uma função:

```ts
getSentenceForWord(userId: string, wordId: string): Sentence
```

Regra:

1. Buscar todas as `Sentence` ligadas à `wordId` via `WordSentence`.
2. Buscar, para esse `userId + wordId`, as últimas `K` (`K` configurável, ex.: 10) revisões e extrair os `sentenceId` usados recentemente.
3. Escolha:

   * se existir alguma frase **nunca vista** para essa palavra por esse usuário → sortear entre essas;
   * senão, pegar a **menos usada / menos recente**:

     * ordenar por `lastUsedAt` ascendente (ou por contagem total) e pegar a mais antiga.
4. Fallback:

   * se não houver frase cadastrada para a palavra, usar uma frase padrão gerada (mas a meta é sempre ter >=1).

---

## 2. Progressão de palavras em ordem de frequência (janela dinâmica estilo Lingvist)

### 2.1. Conceito: “janela de vocabulário ativo”

Cada usuário terá um estado de progresso:

```ts
UserFrequencyProgress {
  userId: string;

  // até qual rank esse usuário quer chegar (100, 500, 1500, 3000, 5000, 10000)
  wordGoalRank: number;

  // fim da janela atual de vocabulário ativo (palavras elegíveis como "novas")
  currentWindowEndRank: number;          // ex.: começa em 100

  // maior rank tal que TODAS as palavras de 1..rank tiveram pelo menos 1 acerto
  maxContiguousMasteredRank: number;     // ex.: 73 (1..73 já acertadas ≥1 vez)
}
```

Regras iniciais:

* Todos os usuários sempre começam **do rank 1**.
* Na criação do perfil, o usuário escolhe um **objetivo de vocabulário** (`wordGoalRank`).
* No início:

  * `wordGoalRank = valor_do_slider` (100, 500, 1500, …)
  * `currentWindowEndRank = min(100, wordGoalRank)`
    (primeira janela com até 100 palavras).
  * `maxContiguousMasteredRank = 0`.

### 2.2. Atualização de `maxContiguousMasteredRank`

Sempre que o usuário acerta uma palavra pela **primeira vez**:

1. Descobrir o `rank` dessa palavra via `WordFrequency`.
2. Atualizar:

```ts
if (rank == maxContiguousMasteredRank + 1) {
  // tenta avançar o prefixo contínuo
  while existsWordWithRank(maxContiguousMasteredRank + 1) &&
        userHasAtLeastOneCorrectForThatRank(userId, maxContiguousMasteredRank + 1) {
    maxContiguousMasteredRank++
  }
}
```

Se `rank > maxContiguousMasteredRank + 1`, apenas marca o acerto, sem mexer no prefixo (porque ainda há buracos antes).

Isso implementa:

> Para chegar na palavra N+1, todas as palavras 1..N têm que ter pelo menos 1 acerto.

### 2.3. Expansão automática da janela (100 → 200 → 300…)

Parâmetro global:

```ts
const WINDOW_STEP = 100; // tamanho de cada expansão
```

Regra:

* Sempre que `maxContiguousMasteredRank >= currentWindowEndRank`
  **e** `currentWindowEndRank < wordGoalRank`:

```ts
currentWindowEndRank = Math.min(
  currentWindowEndRank + WINDOW_STEP,
  wordGoalRank
)
```

Exemplo:

* `wordGoalRank = 1500`
* Começa com `currentWindowEndRank = 100`
* Quando o usuário já acertou pelo menos 1 vez **todos** os ranks 1..100:

  * `maxContiguousMasteredRank = 100` → janela expande para 200
* Quando dominar 1..200 → janela passa a 300, e assim por diante.

### 2.4. Próxima palavra **nova** (rank N+1)

Função:

```ts
getNextNewWordRank(userId: string, progress: UserFrequencyProgress): number | null
```

Regras:

1. Se o usuário nunca viu nenhuma palavra:

   * `nextRank = 1`
2. Senão:

   * `nextRank = maxContiguousMasteredRank + 1`
3. Se `nextRank > currentWindowEndRank`:

   * não introduzir palavra nova agora.
4. Se `nextRank > wordGoalRank`:

   * não há mais novas palavras para esse usuário → retornar `null`.

Caso contrário, `nextRank` é a próxima palavra nova elegível.

---

## 2.5. Mistura entre palavras novas e revisões (SRS + reforço de erros)

Queremos:

* novas palavras em ordem de rank (1, 2, 3, …) respeitando a janela;
* sempre **mesclando**:

  * algumas palavras **novas** (101, 102, …) e
  * várias palavras já praticadas (4, 84, 23, …);
* reforçar mais as palavras que o usuário erra.

### 2.5.1. Estatísticas de sessão

Para cada usuário e dia:

```ts
UserSessionStats {
  userId: string;
  date: string;            // "YYYY-MM-DD"
  cardsShown: number;
  newCardsShown: number;
}
```

Parâmetro:

```ts
const TARGET_NEW_SHARE = 0.25; // ~25% das cartas do dia serem novas
```

### 2.5.2. Seleção do próximo card

Função principal (pseudocódigo):

```ts
getNextCardForUser(userId: string): CardContext {
  const progress = getUserFrequencyProgress(userId)
  const sessionStats = getUserSessionStatsForToday(userId)

  const newShare = sessionStats.cardsShown === 0
    ? 0
    : sessionStats.newCardsShown / sessionStats.cardsShown

  const reviewCandidates = getDueReviewWords(userId, progress.currentWindowEndRank)
  const canIntroduceNew =
    newShare < TARGET_NEW_SHARE &&
    getNextNewWordRank(userId, progress) !== null

  if (canIntroduceNew) {
    const rank = getNextNewWordRank(userId, progress)!
    const word = getWordByRank(rank)
    const sentence = getSentenceForWord(userId, word.id)
    return buildCardContext(word, sentence, { isNew: true })
  }

  // caso contrário, escolher palavra de revisão
  const word = pickBestReviewWord(userId, reviewCandidates)
  const sentence = getSentenceForWord(userId, word.id)
  return buildCardContext(word, sentence, { isNew: false })
}
```

### 2.5.3. Reforço de palavras com mais erros

Implementar `pickBestReviewWord` favorecendo as palavras mais problemáticas.

Sugestão de score:

```ts
overdueDays     = max(0, daysBetween(today, nextReviewAt))
accuracy        = correctAttempts / max(1, repetitions)
wrongStreak     = numberOfConsecutiveWrongs(userId, wordId)
errorBonus      = 1 - accuracy

score = 0.6 * overdueDays +
        0.3 * errorBonus +
        0.1 * wrongStreak
```

* Ordenar candidatos por `score` desc e pegar o primeiro
  **ou** fazer sorteio ponderado por esse score.

---

## 3. Configuração de objetivo de vocabulário no cadastro de usuário

Na criação/edição de perfil:

```ts
UserProfile {
  id: string;
  name: string;
  targetLanguage: string;       // "en"
  nativeLanguage: string;       // "pt-BR"
  wordGoalRank: number;         // 100, 500, 1500, 3000, 5000, 10000
  createdAt: Date;
}
```

* Adicionar um **slider ou botões** com as opções de objetivo de vocabulário (100 / 500 / 1500 / 3000 / 5000 / 10000).
* Ao criar um perfil:

  * `wordGoalRank` = valor do slider.
  * Criar `UserFrequencyProgress` inicial:

    * `wordGoalRank = slider`
    * `currentWindowEndRank = min(100, wordGoalRank)`
    * `maxContiguousMasteredRank = 0`

Não usar mais `startFromRank` / `maxRankLimit` — o controle é sempre por `wordGoalRank` + janela dinâmica.

---

## 4. Ajustes de UI na tela de estudo

1. **Remover**:

   * botão/label `💡 Use the correct word` (tanto embaixo da frase quanto nos toasts);
   * texto auxiliar fixo `Press Enter to submit`.
2. **Adicionar informação gramatical** da palavra-alvo:

   * cada card deve receber `grammarHint` (ex.: `"verb, base form"`, `"noun, plural"`).
   * exibir como **badge** próximo à lacuna, por exemplo logo abaixo da frase, antes da tradução:

     * pill com `rounded-full`, fundo um pouco mais claro, texto pequeno.
3. Garantir que o endpoint de “próximo card” retorne algo como:

```json
{
  "wordId": "w_123",
  "sentence": "She can ___ very well.",
  "sentenceTranslation": "Ela pode ___ muito bem.",
  "grammarHint": "verb, base form",
  "isNew": true,
  ...
}
```

---

## 5. Entregáveis esperados

Na sua resposta, traga:

1. **Atualização de modelos**:

   * Tipos / schemas para `Sentence`, `WordSentence`, `ReviewEvent` com `sentenceId`, `UserFrequencyProgress`, `UserSessionStats`, ajustes em `UserProfile` e `UserWordStats`.
2. **Algoritmos** concretos (pseudocódigo ou código real) para:

   * `getSentenceForWord(userId, wordId)`;
   * atualização de `maxContiguousMasteredRank` e `currentWindowEndRank`;
   * `getNextNewWordRank(userId, progress)`;
   * `pickBestReviewWord(...)` com score;
   * `getNextCardForUser(userId)`.
3. **Ajustes de UI** em React/TS:

   * como renderizar a nova badge de gramática;
   * remoção de `Use the correct word` e `Press Enter to submit`;
   * exemplo de uso do endpoint de “próximo card” integrando frase, badge e os componentes que já existem.

Foque em manter a lógica clara, incremental e fácil de testar (funções puras quando possível) e em encaixar essas mudanças na arquitetura já existente do FillTheWord, sem reescrever o app inteiro.

---