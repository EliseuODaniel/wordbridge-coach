# Change: EN Sentence Bank Quality - Natural Sentences from Real Sources

**Date**: 2025-12-23
**Status**: 📋 Proposed
**Version**: v1.0
**Type**: Quality Improvement + Data Enhancement
**Scope**: Backend (seed, Sentence matching), Data (offline sentence bank), OpenSpec (SPEC.md)

---

## Overview

Substitui o gerador de sentenças genéricas do seed 10k por um **sentence bank real** com frases naturais extraídas de livros de domínio público (Project Gutenberg), garantindo frases contextualmente apropriadas para palavras funcionais comuns (the, to, and, of...) em vez de templates genéricos como "This is ___."

**Motivação**: O seed atual gera frases sem sentido para palavras funcionais muito frequentes. Por exemplo, "The ___ is here." para a palavra "the" produz "The the is here.", que é linguisticamente incorreto. Precisamos de frases reais onde cada palavra aparece em contexto natural.

## Problem Statement

### Estado Atual

1. **Templates genéricos**: `create_10k_vocabulary()` usa 5 templates fixos que assumem substantivos:
   - "The ___ is here."
   - "I see a ___."
   - "This is my ___."
   - "Where is the ___?"
   - "A ___ is on the table."

2. **Problema para palavras funcionais**:
   - "the" → "The the is here." ❌ (gramaticalmente incorreto)
   - "to" → "I see a to." ❌ (sem sentido)
   - "and" → "This is my and." ❌ (nonsense)
   - "of" → "Where is the of?" ❌ (sem contexto)

3. **Placeholder ruim para ranks > 2000**: "This is ___."
   - Produz "This is [qualquer palavra]."
   - Sem contexto semanticamente significativo

4. **Sem tradução**: `translation` fica vazia ou com placeholder genérico

### Impacto no Usuário

- **Experiência de aprendizado pobre**: Frases artificiais não ensinam uso real
- **Confusão para palavras funcionais**: Usuário vê "The the is here." e pode pensar que está quebrado
- **Baixa retenção**: Frases sem contexto não ajudam na memorização
- **Falta de autenticidade**: Sentimento que o app é "robótico"

## Proposed Changes

### 1. Sentence Bank Offline (Fonte: Project Gutenberg)

**Fonte**: [Project Gutenberg](https://www.gutenberg.org/) (livros em domínio público)
- **Licença**: Domínio público nos EUA (obra publicada antes de 1929)
- **Formato**: Arquivo texto `api/data/en_sentence_bank.txt`
- **Tamanho**: 30.000 - 80.000 frases
- **Conteúdo**: 3-6 livros de ficção clássica em inglês

**Livros propostos** (domínio público confirmado):
1. *Pride and Prejudice* (Jane Austen, 1813) - ID: 1342
2. *Alice's Adventures in Wonderland* (Lewis Carroll, 1865) - ID: 11
3. *The Adventures of Sherlock Holmes* (Arthur Conan Doyle, 1892) - ID: 1661
4. *Dracula* (Bram Stoker, 1897) - ID: 345
5. *The Great Gatsby* (F. Scott Fitzgerald, 1925) - ID: 6430 (até 1923? verificar)
6. *Little Women* (Louisa May Alcott, 1868) - ID: 514

**Formato do arquivo**:
```
It is a truth universally acknowledged, that a single man in possession of a good fortune, must be in want of a wife.
Alice was beginning to get very tired of sitting by her sister on the bank, and of having nothing to do.
For a long time, however, I used to walk to the office every morning, no matter where I was staying.
```

Uma frase por linha, UTF-8, sem quebras de linha extras.

### 2. Script de Build: `build_en_sentence_bank.py`

**Local**: `api/scripts/build_en_sentence_bank.py`

**Funcionalidades**:
1. **Download** de livros do Project Gutenberg (URL estática ou API)
2. **Parsing**: Remover headers/footers Gutenberg ("START OF THIS PROJECT GUTENBERG EBOOK")
3. **Extração de sentenças**: Usar `nltk.sent_tokenize` ou regex `[.!?]+\s+`
4. **Filtragem**:
   - Tamanho: 20-140 caracteres (nem muito curta nem muito longa)
   - Deve conter pelo menos 1 palavra alfabética
   - Remover duplicatas (hash-based)
   - Remover sentenças com caracteres não-ASCII (acentos, etc.)
5. **Deduplicação** e **shuffle** (aleatorização)
6. **Persistência**: Salvar `api/data/en_sentence_bank.txt`

**Performance**:
- Tempo de execução: < 5 minutos (download + processamento)
- Memória: < 500MB (processamento stream-based)
- Output: 30k-80k sentenças únicas

**Atribuição**:
- Arquivo `api/data/EN_SENTENCE_BANK_SOURCES.md`
- Lista de livros, autores, anos, IDs Gutenberg
- Justificativa de domínio público (publicação < 1929)

### 3. Seed Integrado: Índice Invertido em Memória

**Modificação**: `api/scripts/seed_data.py:create_10k_vocabulary()`

**Algoritmo de matching** (word → frases):

```python
def build_sentence_index(sentence_bank_path: str) -> Dict[str, List[str]]:
    """
    Constrói índice invertido: token -> lista de frases

    Limita a N frases por token para controlar memória.
    """
    index = {}
    max_sentences_per_token = 200  # Limite para "the", "and", etc.

    with open(sentence_bank_path, 'r', encoding='utf-8') as f:
        for line in f:
            sentence = line.strip()
            if not sentence:
                continue

            # Tokenizar: lowercase + remover pontuação
            tokens = tokenize(sentence)

            for token in tokens:
                if token not in index:
                    index[token] = []

                # Limitar frases por token (para não explodir memória)
                if len(index[token]) < max_sentences_per_token:
                    index[token].append(sentence)

    return index

def get_sentences_for_word(word: str, index: Dict, count: int) -> List[str]:
    """Busca sentenças no índice, com fallback melhorado"""
    sentences = index.get(word.lower(), [])

    if len(sentences) >= count:
        return random.sample(sentences, count)

    # Fallback: templates word-type-aware
    return generate_smart_templates(word, count)
```

**Integração no seed**:
```python
def create_10k_vocabulary(db: Session, lang_ids: dict, decks: list, max_rank: int = 10000):
    # ... código existente ...

    # Carregar sentence bank (se existir)
    sentence_bank_path = "/app/data/en_sentence_bank.txt"
    sentence_index = None

    if os.path.exists(sentence_bank_path):
        print("📚 Loading sentence bank...")
        sentence_index = build_sentence_index(sentence_bank_path)
        print(f"✅ Loaded {len(sentence_index)} tokens in index")

    for wf in word_freqs:
        # ... criar Word ...

        sentence_count = get_sentence_count(wf.rank)

        for i in range(sentence_count):
            if sentence_index and wf.rank <= 2000:
                # Buscar sentença real no índice
                candidates = sentence_index.get(wf.word.lower(), [])

                if candidates:
                    # Selecionar sentença aleatória
                    sentence_text = random.choice(candidates)

                    # Criar gap: substituir primeira ocorrência da palavra
                    gap_sentence, gap_start, gap_end = create_gap_in_sentence(
                        sentence_text, wf.word
                    )
                else:
                    # Fallback: templates melhorados
                    gap_sentence, gap_start, gap_end = generate_smart_templates(
                        wf.word, part_of_speech='UNK'
                    )
            else:
                # Ranks > 2000 ou sem sentence bank: placeholders melhorados
                gap_sentence, gap_start, gap_end = generate_smart_templates(
                    wf.word, part_of_speech='UNK'
                )

            # Criar Sentence e Card com gap correto
            # ...
```

### 4. Gap Creation: Contextualmente Correto

**Função**: `create_gap_in_sentence(sentence_text: str, word: str) -> Tuple[str, int, int]`

**Lógica**:
1. Buscar primeira ocorrência de `word` (case-insensitive)
2. Substituir por "___" (3 underscores)
3. Calcular `gap_start` e `gap_end` (posição exata no texto)
4. Retornar tuple: `(gapped_sentence, gap_start, gap_end)`

**Exemplo**:
```python
sentence = "It is a truth universally acknowledged, that a single man..."
word = "truth"
# → "It is a ___ universally acknowledged, that a single man..."
# → gap_start = 8, gap_end = 11 (posso do "___")
```

**Fallback**: Templates word-type-aware

Se não achar sentença no índice, usar templates baseados em categoria gramatical:
- **Artigos** (the, a, an): "___ word was here." → "The word was here."
- **Preposições** (to, of, in, on): "I went ___ the house." → "I went to the house."
- **Pronomes** (he, she, it, they): "___ is here." → "He is here."
- **Conjunções** (and, but, or): "I like tea ___ coffee." → "I like tea and coffee."
- **Verbos** (be, have, do): "I ___ here." → "I am here."
- **Substantivos** (default): "The ___ is here."

### 5. Translation: Vazia em vez de Inventar

**Decisão**: `Sentence.translation = ""` (string vazia)

**Justificativa**:
- Melhor tradução ruim que engana usuário
- Frontend pode mostrar "No translation available" ou usar tradução automática (DeepL, Google Translate) em tempo real
- Futuramente: adicionar campo `auto_translation: bool` para distinguir manual vs automática

### 6. Performance Impact

**Tempo de seed**:
- Atualmente: ~2-3 minutos (10k words + 11.7k sentences)
- Com sentence bank: +1-2 minutos (loading do índice)
- **Total estimado**: 3-5 minutos

**Memória**:
- Índice invertido: ~50-100MB (30k-80k sentenças, 200 por token max)
- Seed process: pico de 200-300MB
- **Ainda aceitável** para máquina moderna

**Tamanho do dataset**:
- `en_sentence_bank.txt`: ~5-15MB (30k-80k sentenças, média 100 chars)
- `EN_SENTENCE_BANK_SOURCES.md`: ~5KB
- **Total**: < 20MB (aceitável para repositório)

## Data Source Details

### Project Gutenberg: Domínio Público

**Critérios de seleção**:
1. Publicado antes de 1929 (domínio público nos EUA)
2. Língua inglesa
3. Ficção/Literatura (frases naturais, não técnicas)
4. Atribuição clara (autor + ano)

**Livros selecionados**:

1. **Pride and Prejudice** (1813)
   - Autor: Jane Austen
   - ID: 1342
   - URL: https://www.gutenberg.org/files/1342/1342-0.txt
   - Frases estimadas: ~8.000

2. **Alice's Adventures in Wonderland** (1865)
   - Autor: Lewis Carroll
   - ID: 11
   - URL: https://www.gutenberg.org/files/11/11-0.txt
   - Frases estimadas: ~3.000

3. **The Adventures of Sherlock Holmes** (1892)
   - Autor: Arthur Conan Doyle
   - ID: 1661
   - URL: https://www.gutenberg.org/files/1661/1661-0.txt
   - Frases estimadas: ~5.000

4. **Dracula** (1897)
   - Autor: Bram Stoker
   - ID: 345
   - URL: https://www.gutenberg.org/files/345/345-0.txt
   - Frases estimadas: ~6.000

**Total estimado**: ~22.000 sentenças (pode chegar a 30k com mais livros)

### Licença: Domínio Público

**Justificativa legal**:
- Obras publicadas antes de 1929 são domínio público nos EUA (onde o servidor está hospedado)
- Project Gutenberg confirma status de domínio público
- Atribuição não é obrigatória legalmente, mas é prática comum
- Uso educacional (ensino de idiomas) é **fair use** mesmo sob copyright

### Atribuição

**Arquivo**: `api/data/EN_SENTENCE_BANK_SOURCES.md`

Conteúdo:
```markdown
# English Sentence Bank Sources

This file lists the sources used to generate `en_sentence_bank.txt`.

## Sources

1. Pride and Prejudice (1813) by Jane Austen
   - Project Gutenberg ID: 1342
   - URL: https://www.gutenberg.org/files/1342/1342-0.txt
   - License: Public Domain (published before 1929)
   - Sentences contributed: ~8,000

2. Alice's Adventures in Wonderland (1865) by Lewis Carroll
   - Project Gutenberg ID: 11
   - URL: https://www.gutenberg.org/files/11/11-0.txt
   - License: Public Domain
   - Sentences contributed: ~3,000

... (restante dos livros)

## Total Sentences
~30,000 unique sentences (after deduplication and filtering)

## Generation Date
YYYY-MM-DD

## Notes
- Sentences are extracted from public domain works
- Used for educational purposes (language learning)
- Complies with Fair Use and Project Gutenberg terms
```

## Implementation Plan

### Phase 1: OpenSpec + Build Script

1. Criar `openspec/changes/2025-12-en-sentence-bank-quality-v1.md` (este arquivo)
2. Implementar `api/scripts/build_en_sentence_bank.py`
   - Download de livros Gutenberg
   - Extração e filtragem de sentenças
   - Deduplicação e persistência
3. Rodar script manualmente para gerar `en_sentence_bank.txt`

### Phase 2: Seed Integration

4. Modificar `api/scripts/seed_data.py:create_10k_vocabulary()`
   - Adicionar `build_sentence_index()`
   - Adicionar `create_gap_in_sentence()`
   - Adicionar `generate_smart_templates()` (fallback)
5. Testar seed com sentence bank
6. Validar gap positioning (gap_start, gap_end corretos)

### Phase 3: Validation

7. DB limpo + `alembic upgrade head`
8. Rodar `python scripts/seed_data.py --full`
9. Smoke test 100x:
   - Verificar zero 404 errors
   - Verificar zero crashes
   - Amostrar 30 frases para inspeção manual
10. Validação manual top 50 words:
    - Frases devem ser naturais
    - Gap deve estar posicionado corretamente
    - Sem "The the is here."

## Acceptance Criteria

### Dataset (Must Have)

- [ ] `en_sentence_bank.txt` existe com 30k-80k sentenças
- [ ] `EN_SENTENCE_BANK_SOURCES.md` lista todas as fontes
- [ ] Todas as sentenças são < 140 caracteres
- [ ] Sem duplicatas (únicas por hash SHA256)
- [ ] UTF-8 encoding (sem caracteres inválidos)

### Seed (Must Have)

- [ ] `create_10k_vocabulary()` carrega sentence bank se existir
- [ ] Usa sentenças reais para ranks 1-2000
- [ ] Fallback para templates melhorados se não achar sentença
- [ ] Gap posicionado corretamente (gap_start, gap_end)
- [ ] `translation` fica vazio (não inventa tradução)

### Qualidade (Must Have)

- [ ] Top 50 words (rank <= 50) têm frases naturais
- [ ] Nenhuma frase começa com "This is ___." para ranks <= 2000
- [ ] Gap sempre substitui palavra correta (não primeira ocorrência aleatória)
- [ ] Case-insensitive matching: "Truth" encontra "truth"

### Performance (Must Have)

- [ ] Seed time < 5 minutos (incluindo loading do índice)
- [ ] Memória < 500MB durante seed
- [ ] Smoke test 100x: < 10s total

### Bugs (Must NOT Have)

- [ ] Sem "The the is here." ou similar
- [ ] Sem gap fora de posição (gap_start/gap_end incorretos)
- [ ] Sem crashes por memória durante seed
- [ ] Sem 404 errors durante smoke test

## Migration Strategy

### Usuários Existentes (Production)

- ✅ **Zero breaking changes**: Mantém Spec4, anti-repetição, POST /answer
- ✅ **Backwards compatible**: Se `en_sentence_bank.txt` não existir, usa templates
- ✅ **Non-breaking**: Seed pode ser rodado novamente para atualizar sentences

### Novos Usuários

- ✅ **Setup opcional**: `python scripts/build_en_sentence_bank.py` é opcional
- ✅ **Graceful degradation**: Funciona sem sentence bank (só com templates)
- ✅ **Better UX**: Com sentence bank = frases naturais desde o início

## Rollback Plan

Se encontrar problemas críticos:

1. Remover `en_sentence_bank.txt`
2. Seed volta a usar templates (fallback automático)
3. Reverter código de `create_10k_vocabulary()` se necessário

**Nota**: Rollback é seguro pois é aditivo (não remove funcionalidade).

## Open Questions

1. **Tatoeba vs Gutenberg**:
   - **Decisão**: Começar com Gutenberg (mais simples, domínio público claro)
   - **Futuro**: Tatoeba pode ser adicionado depois (CC BY 2.0, requer atribuição)

2. **Tradução automática**:
   - **Fora do escopo** inicial, mas pode ser v2.0
   - **Solução futura**: Usar DeepL API ou LibreTranslate durante seed

3. **Sentences per word**:
   - Atualmente: top 100 = 5, 101-500 = 3, 501-1000 = 2, 1001-2000 = 1
   - **Pergunta**: Devemos aumentar? Ex: top 100 = 10 sentences
   - **Recomendação**: Não agora (já é 5x melhor que atual)

4. **Índice persistente**:
   - Atualmente: reconstrói a cada seed (1-2 minutos)
   - **Pergunta**: Salvar índice em disk para reuso?
   - **Recomendação**: Não otimizar prematuramente (seed é raro)

## Success Metrics

### Imediatos (pós-seed)

- Sentence bank size = 30k-80k frases ✅
- Seed time < 5 minutos ✅
- Smoke test 100x: 0 errors ✅

### Curto Prazo (inspeção manual)

- Top 50 words: 100% frases naturais ✅
- Zero "The the is here." ✅
- Gap positioning: 95%+ correto ✅

### Médio Prazo (1-2 semanas)

- Usuários reportam "frases mais naturais"
- Retenção aumenta > 10% (melhor contexto)
- Support tickets sobre "frases quebradas" diminuem

### Longo Prazo (1-2 meses)

- Satisfação com conteúdo aumenta significativamente
- Usuários estudam mais tempo (menos frustração)
- Reviews positivos mencionam "frases reais"

## References

- [OpenSpec SPEC.md](../../SPEC.md) (Seção Spec4)
- [Project Gutenberg](https://www.gutenberg.org/)
- [Change: EN 10k Vocabulary](./2025-12-en-10k-vocab-variety-v1.md)
- [Change: Spec4 Study Session](./2025-12-spec4-study-session-random-focus-v1.md)

---

**Co-Authored-By**: Claude <noreply@anthropic.com>
