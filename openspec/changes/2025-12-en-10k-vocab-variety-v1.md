# Change: EN 10k Vocabulary - Real Dataset + Variety + Anti-Repetition

**Date**: 2025-12-23
**Status**: 📋 Proposed
**Version**: v1.0
**Type**: Feature + Data Expansion
**Scope**: Backend (seed, WordFrequency, Word, Sentence, Card), Data (offline dataset), OpenSpec (SPEC.md)

---

## Overview

Expande o vocabulário inglês de ~73 palavras (seed atual) para **10.000 palavras reais** com ranks corretos, baseado em corpus de frequência. Implementa variedade real dentro da janela Spec4 (top 1000-2000 com múltiplas frases) e adiciona anti-repetição para evitar exaustão do pool.

**Motivação**: Usuário estudando repetidamente as mesmas 10-20 palavras, sem progresso real. Precisamos de conteúdo "estudável" suficiente para manter variedade mesmo dentro da janela de 100 palavras inicial.

## Problem Statement

### Estado Atual

1. **Seed limitado**: Apenas 73 palavras EN no seed_data.py, todas com ranks fictícios ou incompletos
2. **Scripts dummy**: `populate_10k_frequency.py` gera palavras `word1234` (não são reais)
3. **Repetição excessiva**: Com pool pequeno, usuário vê as mesmas palavras frases repetidamente
4. **Sem múltiplas frases**: Cada palavra tem 1 frase apenas → 1 card → repetição visual imediata
5. **Anti-repetição ausente**: Algoritmo não evita últimas N palavras vistas quando há alternativas disponíveis

### Impacto no Usuário

- Usuário estudando há 1 semana ainda vê as mesmas ~20 palavras
- Sensação de "não estou progredindo"
- Exaustão do conteúdo estudável em poucas sessões
- Variedade insuficiente para manter engagement

## Proposed Changes

### 1. Dataset Offline Real (EN 10k)

**Fonte**: [Word Frequency Data](https://github.com/hermitdave/FrequencyWords/raw/master/content/2016/en/en_50k.txt)
- **Licença**: MIT (livre para uso comercial)
- **Formato**: 50.000 palavras inglesas com frequência do corpus
- **Colunas**: `rank  word  frequency  part_of_speech`
- **Exemplo**:
  ```
  1  the  56271872  DET
  2  be  50834382  VERB
  3  to  46914481  PRT
  ...
  10000  gelatin  1312  NOUN
  ```

**Arquivo**: `api/data/en_top_10000.txt` (10k linhas, top 10.000 palavras)

**Rationale**:
- Corpus real de livros, artigos, Wikipedia (representatividade)
- MIT License (sem restrições)
- Já curado e ordenado por frequência (não precisamos calcular)
- 10k palavras = ~98% de cobertura de textos em inglês

### 2. Seed "Estudável" Expandido

#### 2.1. WordFrequency (10k entradas)

**Arquivo**: `api/data/en_top_10000.txt`

**Script**: `api/scripts/import_en_10k_frequency.py`

```python
def import_word_frequencies(db: Session, filepath: str = "/app/data/en_top_10000.txt"):
    """Importa top 10.000 palavras EN com ranks reais"""
    with open(filepath) as f:
        for line in f:
            rank, word, frequency, pos = line.strip().split()
            wf = WordFrequency(
                word=word.lower(),
                language_code='en',
                rank=int(rank),
                band=WordFrequency.get_band_from_rank(int(rank)),
                is_active=True
            )
            db.add(wf)
    db.commit()
```

**Resultado**:
- 10.000 entradas em `word_frequencies`
- Ranks 1-10.000 preenchidos corretamente
- Bands calculadas: 1-100, 101-500, 501-1500, etc.

#### 2.2. Words (10k palavras)

**Script**: `api/scripts/seed_data.py` (expandido modo `--full`)

```python
def create_10k_words(db: Session, en_lang_id: str):
    """Cria 10k Words EN a partir de WordFrequency"""
    freqs = db.query(WordFrequency).filter(
        WordFrequency.language_code == 'en',
        WordFrequency.rank <= 10000
    ).all()

    for wf in freqs:
        word = Word(
            lemma=wf.word,
            text=wf.word,  # lemma = text (sem flexões no seed inicial)
            part_of_speech=wf.part_of_speech,
            frequency_rank=wf.rank,
            language_id=en_lang_id
        )
        db.add(word)
    db.commit()
```

**Resultado**:
- 10.000 Words EN criadas
- `frequency_rank` preenchido corretamente (1-10.000)
- `language_id` aponta para EN language

#### 2.3. Sentences + Cards (Top 1000+)

**Meta**: Múltiplas frases por palavra para top 1000, fallback para top 2000+

**Categorias**:
1. **Top 100**: 5-10 frases cada (alta frequência = prioridade)
2. **101-500**: 3-5 frases cada
3. **501-1000**: 2-3 frases cada
4. **1001-2000**: 1-2 frases cada
5. **2001-10000**: 1 frase placeholder ou gap "___" (expansão futura)

**Script**: `api/scripts/seed_varied_sentences.py` (expandido)

```python
SENTENCES_PER_WORD = {
    (1, 100): 10,
    (101, 500): 5,
    (501, 1000): 3,
    (1001, 2000): 2,
    (2001, 10000): 1
}

def create_varied_sentences(db: Session):
    """Cria múltiplas frases por palavra baseado em rank"""
    freqs = db.query(WordFrequency).filter(
        WordFrequency.language_code == 'en',
        WordFrequency.rank <= 10000
    ).all()

    for wf in freqs:
        word = get_word_by_lemma(wf.word)
        if not word:
            continue

        # Determinar quantidade de frases
        count = get_sentence_count(wf.rank)

        # Buscar/criar frases para essa palavra
        for i in range(count):
            sentence = create_or_fetch_sentence(word, index=i)
            create_card(sentence)
```

**Resultado Estimado**:
- Top 100: 100 × 10 = 1.000 frases
- 101-500: 400 × 5 = 2.000 frases
- 501-1000: 500 × 3 = 1.500 frases
- 1001-2000: 1000 × 2 = 2.000 frases
- 2001-10000: 8000 × 1 = 8.000 frases
- **Total: ~14.500 frases/cards criados**

**Nota**: Inicialmente, frases beyond top 2000 podem ser placeholders com gap "___". Expansão futura pode popular com conteúdo real via crowdsourcing ou dataset adicional.

### 3. Anti-Repetição Melhorada

**Problema Atual**: Algoritmo seleciona aleatoriamente dentro da janela, mas não rastreia o que foi visto recentemente.

**Solução**: Adicionar "exclusão suave" das últimas N palavras/sentenças vistas.

#### 3.1. Rastreamento de Recência

**Tabela**: `ReviewEvent` (já existe, vamos usar mais)

```sql
-- Consulta últimas N palavras distintas vistas pelo usuário
SELECT DISTINCT sentence.word_id
FROM review_event
JOIN card ON review_event.card_id = card.id
JOIN sentence ON card.sentence_id = sentence.id
WHERE review_event.user_id = :user_id
  AND review_event.created_at >= NOW() - INTERVAL '7 days'
ORDER BY review_event.created_at DESC
LIMIT 50
```

#### 3.2. Seleção com Preferência por Variedade

**Modificação**: `api/app/services/card_selection.py`

```python
def get_next_card_spec4(user_id: str, exclude_card_id: str = None):
    """Seleciona card com variedade maximizada"""

    # 1. Obter pool inicial dentro da janela
    window_ranks = get_eligible_ranks(user_id)  # ex: ranks 1-100
    candidates = get_cards_in_ranks(window_ranks)

    # 2. Excluir card atual (hard exclude)
    if exclude_card_id:
        candidates = [c for c in candidates if c.card_id != exclude_card_id]

    # 3. Excluir últimas 50 palavras vistas (soft exclude)
    recent_word_ids = get_recent_words(user_id, limit=50)
    preferred = [c for c in candidates if c.word_id not in recent_word_ids]

    # 4. Se há alternativas suficientes, usar pool "preferido"
    if len(preferred) >= 10:  # threshold mínimo
        return random.choice(preferred)

    # 5. Fallback: usar pool completo (com repetição)
    return random.choice(candidates)
```

**Rationale**:
- **Soft exclude**: Prefere palavras não vistas recentemente, mas não proíbe
- **Threshold 10**: Só usa pool preferido se tivermos alternativas suficientes
- **Fallback**: Se pool é pequeno (<10), permite repetição (melhor que 404)
- **50 palavras**: Janela móvel de 7 dias (ajustável por parâmetro)

### 4. Arquivo Offline (Download Único)

**Local**: `api/data/en_top_10000.txt`

**Download Pré-Seed**:
```bash
# Durante docker build ou setup inicial
curl -o api/data/en_top_10000.txt \
  https://github.com/hermitdave/FrequencyWords/raw/master/content/2016/en/en_50k.txt \
  | head -10000 > api/data/en_top_10000.txt
```

**Dockerfile**: Adicionar ao build context

```dockerfile
# No Dockerfile da API
COPY api/data/en_top_10000.txt /app/data/en_top_10000.txt
```

## Data Source Details

### Dataset: FrequencyWords (English 50k)

- **URL**: https://github.com/hermitdave/FrequencyWords
- **Arquivo**: `content/2016/en/en_50k.txt`
- **Tamanho**: 50.000 linhas, ~1.5MB
- **Licença**: MIT License (Copyright (c) 2016 Hermit Dave)
- **Descrição**: Frequência de palavras extraídas de corpus OpenSubtitles 2016
- **License File**: https://github.com/hermitdave/FrequencyWords/blob/master/LICENSE

### Corpus Fonte: OpenSubtitles 2016

- **Autores**: P. Lison and J. Tiedemann (2016)
- **Papel**: "OpenSubtitles2016: Extracting Large Parallel Corpora from Movie and TV Subtitles"
- **Filmes + TV legendados**: 481.865 subtitles (2016)
- **Representatividade**: Inglês falado contemporâneo
- **Vocabulário**: 50k palavras mais frequentes
- **Cobertura**: ~99% de diálogos em filmes/séries

### Licença e Atribuição

**FrequencyWords (MIT License)**:
```
Copyright (c) 2016 Hermit Dave

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

**OpenSubtitles2016 (Atribuição Acadêmica)**:
```
@inproceedings{opus2016,
  title = {OpenSubtitles2016: Extracting Large Parallel Corpora from Movie and TV Subtitles},
  author = {Lison, Pierre and Tiedemann, J{\"o}rg},
  booktitle = {Proceedings of the 10th International Conference on Language Resources and Evaluation (LREC 2016)},
  year = {2016},
  pages = {923--931},
  url = {http://www.lrec-conf.org/proceedings/lrec2016/pdf/854_Paper.pdf}
}
```

### Arquivos de Licença no Projeto

**Local**: `api/data/`

**Arquivos**:
1. `en_top_10000.txt` - Dados (10.000 linhas)
2. `FREQUENCYWORDS_LICENSE.txt` - Licença MIT do FrequencyWords
3. `OPENSUBTITLES_ATTRIBUTION.txt` - Atribuição acadêmica OpenSubtitles2016

### Por que OpenSubtitles?

1. **Inglês falado**: Mais relevante para learners que inglês acadêmico
2. **Contemporâneo**: Linguagem atual (não textos de 1900)
3. **Balanceado**: Diálogos informais + formais (dramas, noticiários, etc)
4. **Disponível**: Download livre, formato limpo, licença MIT para uso comercial

## Performance Impact

### Database Size

**Antes** (seed atual):
- `words`: 73 rows
- `sentences`: 100 rows
- `cards`: 100 rows
- `word_frequencies`: ~20 rows
- **Total DB**: ~5MB

**Depois** (10k seed):
- `words`: 10.000 rows
- `sentences`: ~14.500 rows
- `cards`: ~14.500 rows
- `word_frequencies`: 10.000 rows
- **Total DB estimado**: ~150-200MB

**Implicações**:
- ✅ Ainda pequeno para PostgreSQL (sem problemas de memória)
- ✅ Queries por índice (rank, word, language_id) permanecem O(log n)
- ✅ `docker volume` persiste entre restarts (usuário não rebaixa toda vez)
- ⚠️ Seed time aumenta: ~2 minutos (ao invés de 10 segundos)

### Query Performance

**Queries Principais**:

1. **Seleção de card Spec4** (O(log n) com índice):
```sql
SELECT card.*, sentence.*, word.*
FROM card
JOIN sentence ON card.sentence_id = sentence.id
JOIN word ON sentence.word_id = word.id
WHERE word.frequency_rank BETWEEN 1 AND 100  -- janela
LIMIT 1000  -- pool suficiente
```
- **Tempo estimado**: 5-15ms (índice em `word.frequency_rank`)

2. **Últimas 50 palavras vistas** (O(1) com índice composto):
```sql
SELECT DISTINCT sentence.word_id
FROM review_event
JOIN card ON review_event.card_id = card.id
JOIN sentence ON card.sentence_id = sentence.id
WHERE review_event.user_id = ?
  AND review_event.created_at >= NOW() - INTERVAL '7 days'
ORDER BY review_event.created_at DESC
LIMIT 50
```
- **Tempo estimado**: 10-20ms (índice em `(user_id, created_at)`)

3. **WordFrequency por rank** (O(log n)):
```sql
SELECT * FROM word_frequency
WHERE language_code = 'en' AND rank = ?
```
- **Tempo estimado**: <1ms (índice único)

**Conclusão**: Performance permanece excelente mesmo com 10k palavras.

### API Latency

**Antes** (73 palavras):
- `GET /cards/next-spec4`: 50-150ms

**Depois** (10k palavras):
- `GET /cards/next-spec4`: 60-200ms (aumento de ~10-50ms)
- **Ainda aceitável** para UX (sub-second)

## Implementation Plan

### Phase 1: Dataset + Seed (Scripts)

1. **Download dataset**
   ```bash
   mkdir -p api/data
   curl -o api/data/en_top_10000.txt \
     https://github.com/hermitdave/FrequencyWords/raw/master/content/2016/en/en_50k.txt \
     | head -10000 > api/data/en_top_10000.txt
   ```

2. **Criar script de importação**
   - `api/scripts/import_en_10k_frequency.py`
   - Lê `en_top_10000.txt`
   - Popula `word_frequencies` (10k rows)

3. **Expadir `seed_data.py`**
   - Modo `--full` para popular 10k words
   - Criar sentences variadas (top 1000-2000)
   - Criar cards para todas as sentences

4. **Expadir `seed_varied_sentences.py`**
   - Múltiplas frases por palavra
   - Prioridade: top 100 > top 500 > top 1000 > top 2000

### Phase 2: Anti-Repetition (Algorithm)

5. **Modificar `card_selection.py`**
   - Adicionar `get_recent_words(user_id, limit=50)`
   - Modificar `get_next_card_spec4()` para usar soft exclude
   - Threshold mínimo de 10 alternativas antes de permitir repetição

6. **Testes**
   - **Smoke Test 1 (Janela 100)**: Criar user com goal=100, rodar 100x calls, medir variedade
   - **Smoke Test 2 (Janela 2000)**: Simular progressão até 2000, rodar 200x calls, medir anti-repetição
   - Medir `unique_words` / `unique_sentences` em ambos os testes
   - Verificar zero 404 errors

### Phase 3: Validation

7. **Validação em DB limpo**
   - `docker compose down`
   - `docker volume rm filltheword_postgres_data`
   - `docker compose up -d`
   - `alembic upgrade head`
   - `python scripts/import_en_10k_frequency.py`
   - `python scripts/seed_data.py --full`
   - **Smoke Test 1**: 100x calls com user goal=100 (>= 80 unique words)
   - **Smoke Test 2**: 200x calls com user window=2000 (>= 400 unique words)

## Acceptance Criteria

### Dados (Must Have)

- [ ] `word_frequencies` tem exatamente **10.000 rows** para `language_code='en'`
- [ ] `words` tem exatamente **10.000 rows** para `language_id=en` (1:1 com WordFrequency)
- [ ] Todas as words têm `frequency_rank` preenchido (1-10.000)
- [ ] Ranks são únicos (sem duplicatas: rank 100 aparece 1 vez apenas)

### Cards (Must Have)

- [ ] Top 1000 palavras têm **>= 3 cards** cada (múltiplas frases)
- [ ] Top 100 palavras têm **>= 5 cards** cada (prioridade alta)
- [ ] Total cards **>= 5.000** (cobertura adequada)
- [ ] Nenhum card tem sentence com placeholder "___" para top 2000

### Variedade (Must Have)

**Nota**: Como a janela inicial Spec4 começa em 100 (Opção A) e expande gradualmente, o smoke test deve medir variedade de forma compatível.

- [ ] **Smoke Test 1: Janela Inicial (100 palavras)**
  - Criar usuário com `word_goal_rank=100` (janela fixa em 100)
  - Executar 100x calls to `/next-spec4`
  - `unique_words >= 80` (80% da janela inicial)
  - `unique_sentences >= 90` (90% devido múltiplas frases)
  - Zero 404 errors

- [ ] **Smoke Test 2: Janela Expandida (2000 palavras)**
  - Criar usuário e simular progressão até `current_window_end_rank=2000`
  - Executar 200x calls to `/next-spec4`
  - `unique_words >= 400` (20% da janela expandida, anti-repetição ativo)
  - `unique_sentences >= 450` (múltiplas frases por palavra)
  - Zero 404 errors

- [ ] **Últimas 50 palavras vistas são excluídas** (soft exclude)
- [ ] **Repetição só ocorre quando pool < 10 alternativas**

### Performance (Must Have)

- [ ] `GET /cards/next-spec4` < 200ms (P95)
- [ ] Seed time < 3 minutos (import 10k + create cards)
- [ ] DB size < 500MB (após seed completo)

### Bugs (Must NOT Have)

- [ ] Sem 404 "No cards available" durante smoke test
- [ ] Sem crashes por memória durante seed
- [ ] Sem ranks duplicados ou gaps (1, 2, 3...10000)
- [ ] Sem palavras `word1234` ou similares (todas devem ser reais)

## Migration Strategy

### Usuários Existentes (Production)

- ✅ **Zero downtime**: Migration é aditiva (só adiciona dados)
- ✅ **Non-breaking**: API não muda assinaturas
- ✅ **Backwards compatible**: Users com goal=100 continuam funcionando
- ⚠️ **Opt-in**: Usuário precisa aumentar `word_goal_rank` para ver novas palavras

### Novos Usuários

- ✅ **Default seed**: 10k palavras disponíveis imediatamente
- ✅ **Default goal**: 500 (janela inicial) → expande conforme progresso
- ✅ **Experiência**: Variedade real desde a primeira sessão

## Rollback Plan

Se encontrar problemas críticos:

1. **Reverter código**: `git revert <commit-hash>`
2. **Limpar DB**: `DELETE FROM word_frequencies WHERE rank > 73`
3. **Manter seed atual**: 73 palavras funcionando

**Nota**: Rollback é seguro pois não removemos dados existentes, só adicionamos.

## Open Questions

1. **Frases placeholder vs reais**: Para ranks 2001-10000, devemos:
   - (A) Criar frases placeholder "This is ___." (simples, mas sem contexto)
   - (B) Deixar sem cards initially (expansão futura via dataset)
   - **Recomendação**: A (placeholders) para garantir cards sempre disponíveis

2. **Crowdsourcing frases**: Futuramente, permitir usuários contribuírem frases?
   - **Fora do escopo** desta change, mas pode ser v2.0

3. **Outras línguas**: FR, PT, ES terão 10k também?
   - **Fora do escopo**, mas estrutura é a mesma
   - Dataset FrequencyWords tem FR/ES/PT também

## Success Metrics

### Imediatos (pós-seed)

- WordFrequency.count = 10.000 ✅
- Words.count = 10.000 ✅
- Cards.count >= 5.000 ✅
- Smoke test 200x: 0 errors ✅

### Médio Prazo (1-2 semanas)

- Usuários reportam "nunca vejo a mesma palavra duas no mesmo dia"
- Retenção aumenta > 20% (mais conteúdo = mais engagement)
- Support tickets sobre "repetição" diminuem para zero

### Longo Prazo (1-2 meses)

- Usuários com goal=5000 dominando efetivamente 5k palavras
- Tempo para alcançar goal=10k: ~6-12 meses (com estudo diário)
- Zero churn por "falta de conteúdo"

## References

- [OpenSpec SPEC.md](../../SPEC.md) (Seção Spec4)
- [FrequencyWords GitHub](https://github.com/hermitdave/FrequencyWords)
- [Word Frequency Data](https://github.com/hermitdave/FrequencyWords/blob/master/README.md)
- [API.md](../../API.md) (Endpoint `/cards/next-spec4`)
- [Change: Spec4 Study Session](./2025-12-spec4-study-session-random-focus-v1.md)

---

**Co-Authored-By**: Claude <noreply@anthropic.com>
