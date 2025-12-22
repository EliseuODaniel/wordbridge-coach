Beleza, vamos “versão 2.0” disso, agora pensando:

* nome do projeto: **FillTheWord**
* desenvolvimento **100% guiado por OpenSpec (SDD)**
* tudo rodando em **containers**, portátil e offline

Vou reescrever como um documento de especificação + arquitetura.

---

# 0. Visão geral do FillTheWord

**Objetivo:** app local de aprendizado de idiomas que imita a experiência do Lingvist:

* frase com **lacuna**: `We drove to the ____ in spite of the bad weather.`
* usuário **DIGITA** a palavra (como no print).
* mostra tradução da frase inteira.
* mostra dica gramatical (“substantivo, singular”).
* botão para **ouvir a pronúncia** da palavra e/ou da frase.
* motor de **repetição espaçada** para escolher o próximo card.
* tudo rodando localmente via Docker/Podman.

---

# 1. Desenvolvimento guiado por OpenSpec

## 1.1. Papel do OpenSpec no projeto

OpenSpec é um framework de **spec-driven development (SDD)**: você escreve a especificação primeiro, e tanto humanos quanto as AIs de coding seguem aquilo como fonte de verdade, em vez de “vibe coding” no chat.

Ele é um CLI open source, instalado via npm (`npm install -g @fission-ai/openspec`) e inicializado com `openspec init`, que cria a pasta/configuração de specs e instruções para as AIs.

Principais ideias que vamos usar:

* **Spec como “single source of truth”**: um spec topo descreve domínio, fluxos, APIs, arquitetura e containers.
* **Proposals e diffs de spec**: mudanças começam sempre num “spec proposal” (novo fluxo, novo endpoint etc.) antes de gerar código.
* Integra com qualquer AI (Claude, Gemini, etc.), sem exigir API keys.

## 1.2. Estrutura de specs para o FillTheWord

Sugestão de estrutura no repositório:

```text
filltheword/
  openspec/
    PROJECT.md          # contexto, princípios, stack (documento “guia” geral)
    SPEC.md             # spec raiz, fonte de verdade
    DOMAINS.md          # modelo de domínio (Card, Sentence, Word, User...)
    API.md              # contratos HTTP/REST
    ARCH.md             # arquitetura e containers
    TASKS/              # specs de mudanças específicas (proposals)
```

Fluxo de trabalho (alto nível):

1. **Definir/atualizar** `SPEC.md` e arquivos auxiliares.
2. Usar comandos/atalhos do OpenSpec (ou slash commands) para gerar:

   * esqueleto de código (backend, frontend, tts-service),
   * testes de unidade/integração,
   * arquivos de infra (Dockerfile, docker-compose).
3. Implementar/refinar código **sempre alinhando** com o spec – qualquer divergência vira uma nova mudança de spec.

---

# 2. Escopo funcional do MVP (o que o app precisa fazer)

Tudo abaixo vira seções dentro de `SPEC.md` + `API.md` (em formato que o OpenSpec recomenda).

## 2.1. Fluxo principal: card tipo Lingvist

**RF-01 – Exibir frase com lacuna**

* Selecionar um **Card** agendado pelo motor de SRS.
* Renderizar frase na língua alvo (L2) com uma única lacuna:

  * exemplo: `We drove to the ____ in spite of the bad weather.`
* Exibir:

  * tradução da frase inteira (L1),
  * dica gramatical da palavra faltante (“substantivo, singular”),
  * indicador de “nível de memória” (0–4 bolinhas).

**RF-02 – Usuário digita a resposta**

* Campo de input de texto.
* Enter ou botão “Confirmar” envia a resposta para o backend.

**RF-03 – Correção da resposta**

* Comparação tolerante:

  * case-insensitive,
  * normalizando acentos/pontuação,
  * aceitando variações configuradas (sinônimos, plural/singular se marcado no card).
* Se **correto**:

  * feedback visual verde,
  * exibir frase completa com a palavra preenchida,
  * atualizar estatísticas de SRS.
* Se **incorreto**:

  * marcar tentativa como errada,
  * dar opção de dica (primeira letra, contagem de letras),
  * permitir nova tentativa ou mostrar resposta correta.

**RF-04 – Áudio de pronúncia**

* Botão “🔊 palavra”: TTS fala a palavra alvo.
* Botão “🔊 frase”: TTS fala a frase completa.
* Áudio gerado via serviço de TTS local (ver seção 5), com **cache** em disco.

**RF-05 – Sessão de estudo**

* Barra/contador “Card 12/50”.
* Após responder (certo ou errado), botão “Próximo card”.
* Configuração diária:

  * limite de cards **novos** por dia,
  * quantidade máxima de cards em revisão.

**RF-06 – Estatísticas básicas**

* Palavras: novas / em aprendizado / consolidadas.
* Cards vistos no dia, taxa de acerto.
* Número de revisões futuras por dia (próximos 7–30 dias).

---

# 3. Modelo de domínio (para DOMAINS.md)

### 3.1. Entidades principais

* **Language**

  * `id`, `code` (en, pt-BR), nome.
* **Word**

  * `id`
  * `language_id`
  * `text` (string literal)
  * `lemma`
  * `part_of_speech` (noun, verb, etc.)
  * `features` (JSON: gênero, número, tempo, etc.).
* **Sentence**

  * `id`
  * `language_id` (L2)
  * `text` (frase em L2)
  * `translation` (frase em L1).
* **Card**

  * `id`
  * `sentence_id`
  * `word_id` (palavra alvo)
  * `gap_start_index`, `gap_end_index` (em caracteres ou tokens)
  * `grammar_hint` (“substantivo, singular”)
  * `deck_id` (para decks temáticos/customizados).
* **User**

  * `id`, nome, idioma nativo, idioma alvo.
* **UserCardState**

  * `user_id`, `card_id`
  * `repetitions`
  * `easiness_factor`
  * `interval_days`
  * `next_review_at`
  * `status` (NEW | LEARNING | MATURE).
* **ReviewEvent**

  * `id`
  * `user_id`, `card_id`
  * `timestamp`
  * `answer_text`
  * `quality` (0–5)
  * `was_correct` (bool)
  * `response_time_ms`.

Esse modelo vai ser descrito em formato bem declarativo dentro do OpenSpec (classes, campos, invariantes).

---

# 4. Motor de repetição espaçada (SRS) – especificação

O spec define um algoritmo inspirado no SM-2:

* Para cada resposta, calculamos `quality` de 0 a 5:

  * 5: acerto rápido, sem hesitação;
  * 3–4: acerto com alguma hesitação/dica;
  * 0–2: erro.

* Atualização do card:

  * Se `quality < 3`:

    * `repetitions = 0`
    * `interval_days = 1`
  * Senão:

    * primeira vez → `interval_days = 1`
    * segunda vez → `interval_days = 6`
    * demais → `interval_days = interval_days * easiness_factor`
  * `easiness_factor` ajustado pela fórmula clássica SM-2, limitado a mínimo 1.3.

* `next_review_at = today + interval_days`.

No OpenSpec:

* `DOMAINS.md` descreve os campos e as regras.
* `SPEC.md` inclui cenários:

  * “quando usuário erra 2 vezes seguidas…”
  * “quando acerta 5 vezes com qualidade ≥4…”
* `API.md` define endpoints para:

  * buscar próximo card (`GET /cards/next`),
  * registrar resposta (`POST /cards/{id}/answer`).

---

# 5. Áudio e TTS local

## 5.1. Requisitos de produto

* **Obrigatório**:

  * funcionar **offline**;
  * suportar pelo menos EN/ES/FR/PT nas frases e palavras;
  * gerar áudio on-demand e cachear em disco.
* **Nice to have**:

  * vozes diferentes por idioma;
  * controle de velocidade.

## 5.2. Opções de TTS

Três opções open source adequadas:

* **Coqui TTS** – toolkit robusto com modelos pré-treinados em muitas línguas (incluindo pt-BR), com server HTTP e imagem Docker oficial.
* **Piper** – TTS neural rápido, pensado para rodar localmente (até em hardware limitado), com modelos leves para diversos idiomas.
* **MeloTTS** – TTS multilíngue de alta qualidade, com licença permissiva (MIT) e foco em uso local.

**Decisão sugerida no spec:**

* MVP: usar **Coqui TTS** em um container próprio, usando o server HTTP deles.
* `ARCH.md` descreve o contrato:

  * `POST /tts` com `{ text, lang, voice_type, kind: "word"|"sentence" }`
  * resposta: binário de áudio ou URL local (`/audio/...`).

## 5.3. Cache de áudio

Regra de cache definida na spec:

* Caminho padrão: `audio/<lang>/<type>/<slug>.wav`.
* Antes de chamar TTS, o backend verifica se o arquivo já existe.
* Se não existir, chama TTS, salva arquivo e retorna a URL ao frontend.

---

# 6. Dados linguísticos (corpora)

Você não vai copiar conteúdo do Lingvist; vai usar corpora abertos:

* **Tatoeba** – grande coleção colaborativa de frases com traduções; download de sentenças por idioma em formato tabular.
* **ParaCrawl** – paralelo web-scale, várias línguas, focado em MT; pode ser usado como fonte complementar.
* **OpenSubtitles** via OPUS – legendas de filmes multi-idioma, com versões paralelas em dezenas de línguas.

No spec você define um **pipeline offline** para:

1. Importar frases paralelas (L2–L1).
2. Filtrar por:

   * tamanho razoável (5–15 tokens),
   * evitar frases ofensivas/NSFW.
3. Escolher palavra-alvo para cada frase com base em frequência.
4. Criar objetos `Sentence`, `Word` e `Card`.

Esse pipeline pode virar uma seção separada em `SPEC.md` (“Corpus Importer”) com tasks específicas.

---

# 7. Arquitetura técnica + containers

Tudo rodando via `docker compose` (ou equivalente). O spec de arquitetura (`ARCH.md`) descreve os serviços:

## 7.1. Serviços

1. **api** – backend (FastAPI, por exemplo)

   * expõe REST em `http://api:8000`.
   * faz:

     * seleção de cards (SRS),
     * correção das respostas,
     * persistência de estados no banco,
     * chamada ao serviço de TTS.
2. **frontend**

   * app web (React/Vite, Svelte, etc.) servindo UI do FillTheWord.
   * roda em `http://frontend:3000` (com reverse proxy opcional).
3. **tts-service**

   * container com Coqui TTS ou Piper.
   * expõe HTTP (ex.: `http://tts:5002/tts`).
4. **db**

   * Postgres em `postgres:16` (ou outro).
   * dados persistidos em volume local.

### 7.2. Esqueleto de `docker-compose.yml` (especificado conceitualmente)

No spec você não precisa escrever o YAML final, mas definir algo equivalente a esto:

```yaml
services:
  api:
    build: ./backend
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db
      - tts
    volumes:
      - ./data/audio:/app/audio   # cache de áudio

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - api

  tts:
    image: ghcr.io/coqui-ai/tts-cpu  # ou imagem própria
    command: ["python3", "TTS/server/server.py", "--model_name", "tts_models/en/vctk/vits"]
    ports:
      - "5002:5002"

  db:
    image: postgres:16
    environment:
      POSTGRES_DB: filltheword
      POSTGRES_USER: filltheword
      POSTGRES_PASSWORD: change_me
    volumes:
      - ./data/db:/var/lib/postgresql/data
```

O OpenSpec **não precisa gerar esse YAML literal**, mas `ARCH.md` descreve:

* serviços,
* portas,
* dependências,
* variáveis de ambiente críticas,
* volumes/persistência.

Depois você pede pra AI (seguindo OpenSpec) gerar o `docker-compose.yml` a partir dessa descrição.

---

# 8. Contratos de API principais (para API.md)

### 8.1. Buscar próximo card

`GET /api/cards/next`

Resposta:

```json
{
  "card_id": 123,
  "sentence": "We drove to the field in spite of the bad weather.",
  "gap": { "start": 15, "end": 20 },
  "sentence_translation": "Fomos de carro para o campo, apesar do mau tempo.",
  "grammar_hint": "substantivo, singular",
  "memory_stage": 2,
  "audio_word_url": "/audio/en/words/field.wav",
  "audio_sentence_url": "/audio/en/sentences/we_drove_to_the_field.wav"
}
```

### 8.2. Enviar resposta

`POST /api/cards/{id}/answer`

Body:

```json
{
  "answer": "field",
  "response_time_ms": 3200
}
```

Resposta:

```json
{
  "correct": true,
  "correct_answer": "field",
  "sentence_full": "We drove to the field in spite of the bad weather.",
  "quality": 4,
  "next_review_at": "2025-12-20T10:00:00Z"
}
```

Esses contratos entram em `API.md` com mais detalhes (erros, códigos HTTP, exemplos de edge cases).

---

# 9. Workflow de desenvolvimento com OpenSpec + containers

Em linguagem de “passos”, o spec pode descrever algo como:

1. **Bootstrap do projeto**

   * Criar repo `filltheword`.
   * `npm install -g @fission-ai/openspec@latest`.
   * `openspec init` para gerar estrutura `openspec/`.
2. **Primeiro spec**

   * Preencher `PROJECT.md` com contexto, stack (FastAPI + React + Coqui TTS + Postgres + Docker).
   * Escrever `SPEC.md` com:

     * objetivos do FillTheWord,
     * fluxos RF-01 a RF-06,
     * requisitos de TTS e offline.
   * Escrever `DOMAINS.md`, `API.md`, `ARCH.md`.
3. **Gerar código inicial**

   * Usar comandos/atalhos do OpenSpec para:

     * gerar skeleton do backend (modelos, endpoints),
     * gerar skeleton do frontend (screens `StudySession`, `CardView`),
     * gerar esqueleto do `docker-compose.yml` e Dockerfiles.
4. **Ciclo de mudança**

   * Cada nova feature → um novo arquivo em `openspec/TASKS/xxxx-filltheword-feature-x.md`.
   * AI implementa/atualiza código com base nesse spec.
   * Rodar testes dentro dos containers:

     * `docker compose run api pytest`
     * `docker compose run frontend npm test`.

---

# 10. Resumo final

**FillTheWord** fica definido como:

* um app tipo Lingvist, offline, em que o usuário **digita** a palavra faltante numa frase e pode **ouvir** a pronúncia da palavra/frase;
* toda a lógica de vocabulário em contexto + SRS está formalizada no spec (OpenSpec);
* dados vêm de corpora abertos como Tatoeba/ParaCrawl/OpenSubtitles;
* execução encapsulada em containers (api, frontend, tts, db), orquestrados via docker-compose;
* OpenSpec funciona como **cérebro do projeto**, garantindo que cada mudança passe por uma alteração de spec antes de mexer no código.

Com esse documento você já tem “o mapa do jogo”: próximo passo é começar o repo `filltheword`, rodar `openspec init` e começar a preencher SPEC/DOMAINS/API/ARCH conforme essas seções. A partir daí, é só usar as AIs como devs obedientes ao spec, em vez de feiticeiros improvisando.
