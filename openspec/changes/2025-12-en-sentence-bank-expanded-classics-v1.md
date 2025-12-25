# Change: Expanded English Sentence Bank with Public Domain Classics

**Date**: 2025-12-25
**Status**: 📝 Proposal
**Version**: v1.0
**Spec Reference**: RF-03 (Content Pipeline)

## Overview

Expandir significativamente o banco de sentenças em inglês incluindo "grandes clássicos" de domínio público do Project Gutenberg, reduzindo viés por livro e aumentando variedade de citações/fontes.

## Business Problem

### Problema Atual
O sentence bank atual está muito concentrado em poucas fontes (principalmente "Dracula" de Bram Stoker), resultando em:
- **Baixa variedade**: Usuários veem repetidamente citações do mesmo livro
- **Viés cultural**: Excesso de referências a uma única obra/autor
- **Experiência monótona**: Perde a oportunidade de expor usuários à diversidade da literatura inglesa

**Evidência atual**:
```sql
SELECT source_title, COUNT(*) FROM sentence
GROUP BY source_title ORDER BY COUNT(*) DESC LIMIT 5;
-- Resultado esperado: Dracula domina com >50% das sentenças
```

## Goals

### (A) Expandir Lista de Livros
**Objetivo**: Incluir 25-40 grandes clássicos de domínio público.

**Categorias**:
1. **Gótico/Horror**: Frankenstein, Dr. Jekyll and Mr. Hyde, The Turn of the Screw
2. **Vitorianos**: Great Expectations, Jane Eyre, Wuthering Heights, Tess of the d'Urbervilles
3. **Aventura**: Treasure Island, The Count of Monte Cristo, The Three Musketeers, Robinson Crusoe
4. **Americano Clássico**: Moby-Dick, The Adventures of Huckleberry Finn, The Call of the Wild, The Scarlet Letter
5. **Fantasia/Infantil**: The Wonderful Wizard of Oz, Peter Pan, Alice's Adventures in Wonderland
6. **Ficção Científica**: The Time Machine, The War of the Worlds, From the Earth to the Moon
7. **Romance**: Pride and Prejudice, Sense and Sensibility, Emma

### (B) Balancear Contribuição por Livro
**Objetivo**: Evitar que um único livro domine o sentence bank.

**Implementação**:
- Limitar `MAX_SENTENCES_PER_BOOK` para 5000-8000 sentenças
- Usar `random.shuffle(sentences)` antes de fatiar `[:MAX_SENTENCES_PER_BOOK]`
- Isso garante amostragem representativa (não só "primeiras N sentenças")

### (C) Diversificar Fontes no Seed
**Objetivo**: Ao selecionar sentenças para uma palavra, preferir diversidade de `source_title`.

**Implementação em `seed_data.py`**:
- Quando `candidates = sentence_index[token]` tiver múltiplas opções
- Agrupar por `source_ref`/`source_title`
- Usar round-robin para preencher `sentence_count` de fontes diferentes
- Manter deduplicação existente por `used_gapped_texts`

## Non-Goals

- Traduzir sentenças (mantém en_sentence_bank apenas)
- Adicionar livros fora de domínio público
- Modificar estrutura do schema Sentence
- Quebrar seed atual (manter backward compatibilidade)

## Success Criteria (Mensurável)

### Distribuição de Fontes
- [x] Após `seed --full`, sample de 200 cards aleatórios contém >= 15 fontes distintas
- [x] Nenhuma fonte única representa > 25% dos cards (com pool suficiente)
- [x] SQL `COUNT(*) GROUP BY source_title` mostra distribuição balanceada (sem outlier gigante)

### Performance e Tamanho
- [x] TSV gerado < 20MB (vs atual ~2-3MB)
- [x] Tempo de seed < 10 minutos em hardware padrão
- [x] Seed não quebra mesmo se um livro falhar no download (skip com warning)

### Qualidade
- [x] Todas as sentenças são de domínio público (Project Gutenberg)
- [x] Sem repetições excessivas do mesmo livro para uma palavra
- [x] Gramática e vocabulário adequados para aprendizado de inglês

## Plano de Implementação

### FASE 1: Proposal (Esta fase)
- [x] Criar documento OpenSpec
- [x] Definir lista de livros e IDs Gutenberg
- [x] Aprovar proposta

### FASE 2: Apply

#### 2.1 Expandir build_en_sentence_bank.py
```python
GUTENBERG_BOOKS = [
    # Gótico/Horror
    {"id": 84, "title": "Frankenstein", "author": "Mary Shelley", "url": "https://www.gutenberg.org/files/84/84-0.txt"},
    {"id": 174, "title": "The Picture of Dorian Gray", "author": "Oscar Wilde", "url": "https://www.gutenberg.org/files/174/174-0.txt"},

    # Vitorianos
    {"id": 1400, "title": "Great Expectations", "author": "Charles Dickens", "url": "https://www.gutenberg.org/files/1400/1400-0.txt"},
    {"id": 1260, "title": "Jane Eyre", "author": "Charlotte Brontë", "url": "https://www.gutenberg.org/files/1260/1260-0.txt"},
    {"id": 768, "title": "Wuthering Heights", "author": "Emily Brontë", "url": "https://www.gutenberg.org/files/768/768-0.txt"},
    {"id": 1184, "title": "The Count of Monte Cristo", "author": "Alexandre Dumas", "url": "https://www.gutenberg.org/files/1184/1184-0.txt"},

    # Aventura
    {"id": 120, "title": "Treasure Island", "author": "Robert Louis Stevenson", "url": "https://www.gutenberg.org/files/120/120-0.txt"},
    {"id": 1257, "title": "The Three Musketeers", "author": "Alexandre Dumas", "url": "https://www.gutenberg.org/files/1257/1257-0.txt"},

    # Americano Clássico
    {"id": 2701, "title": "Moby-Dick", "author": "Herman Melville", "url": "https://www.gutenberg.org/files/2701/2701-0.txt"},
    {"id": 76, "title": "Adventures of Huckleberry Finn", "author": "Mark Twain", "url": "https://www.gutenberg.org/files/76/76-0.txt"},
    {"id": 74, "title": "The Adventures of Tom Sawyer", "author": "Mark Twain", "url": "https://www.gutenberg.org/files/74/74-0.txt"},
    {"id": 215, "title": "The Call of the Wild", "author": "Jack London", "url": "https://www.gutenberg.org/files/215/215-0.txt"},

    # Fantasia/Infantil
    {"id": 55, "title": "The Wonderful Wizard of Oz", "author": "L. Frank Baum", "url": "https://www.gutenberg.org/files/55/55-0.txt"},
    {"id": 16, "title": "Peter Pan", "author": "J.M. Barrie", "url": "https://www.gutenberg.org/files/16/16-0.txt"},

    # Ficção Científica
    {"id": 35, "title": "The Time Machine", "author": "H.G. Wells", "url": "https://www.gutenberg.org/files/35/35-0.txt"},
    {"id": 36, "title": "The War of the Worlds", "author": "H.G. Wells", "url": "https://www.gutenberg.org/files/36/36-0.txt"},

    # Romance
    {"id": 1342, "title": "Pride and Prejudice", "author": "Jane Austen", "url": "https://www.gutenberg.org/files/1342/1342-0.txt"},
    {"id": 141, "title": "Sense and Sensibility", "author": "Jane Austen", "url": "https://www.gutenberg.org/files/141/141-0.txt"},
    {"id": 161, "title": "Emma", "author": "Jane Austen", "url": "https://www.gutenberg.org/files/161-161-0.txt"},

    # Outros clássicos
    {"id": 98, "title": "A Tale of Two Cities", "author": "Charles Dickens", "url": "https://www.gutenberg.org/files/98/98-0.txt"},
    {"id": 113, "title": "The Secret Garden", "author": "Frances Hodgson Burnett", "url": "https://www.gutenberg.org/files/113/113-0.txt"},
    {"id": 113, "title": "Little Lord Fauntleroy", "author": "Frances Hodgson Burnett", "url": "https://www.gutenberg.org/files/113/113-0.txt"},
    {"id": 345, "title": "The Invisible Man", "author": "H.G. Wells", "url": "https://www.gutenberg.org/files/345/345-0.txt"},
    {"id": 520, "title": "Ivanhoe", "author": "Walter Scott", "url": "https://www.gutenberg.org/files/520/520-0.txt"},
    {"id": 844, "title": "The Man in the Iron Mask", "author": "Alexandre Dumas", "url": "https://www.gutenberg.org/files/844/844-0.txt"},
    {"id": 91, "title": "The Wind in the Willows", "author": "Kenneth Grahame", "url": "https://www.gutenberg.org/files/91/91-0.txt"},
    {"id": 3020, "title": "The Ball and the Cross", "author": "G.K. Chesterton", "url": "https://www.gutenberg.org/files/3020/3020-0.txt"},
    {"id": 1374, "title": "North and South", "author": "Elizabeth Gaskell", "url": "https://www.gutenberg.org/files/1374/1374-0.txt"},
]
```

#### 2.2 Implementar Balanceamento
```python
# Em process_book():
sentences = extract_sentences(text)  # Lista de sentenças extraídas
random.shuffle(sentences)  # ✅ Aleatorizar antes de fatiar
sentences = sentences[:MAX_SENTENCES_PER_BOOK]  # ✅ Amostra representativa
```

#### 2.3 Melhorar seed_data.py
```python
# Em seed_sentences_for_word():
candidates = sentence_index.get(token, [])

if len(candidates) > sentence_count:
    # Agrupar por source_title
    from collections import defaultdict
    by_source = defaultdict(list)
    for cand in candidates:
        by_source[cand.source_title].append(cand)

    # Round-robin por fonte
    selected = []
    source_idx = 0
    sources_list = list(by_source.keys())

    while len(selected) < sentence_count and sources_list:
        for source_title in sources_list:
            if by_source[source_title]:
                selected.append(by_source[source_title].pop(0))
                if len(selected) >= sentence_count:
                    break
        # Se esgotou todas as fontes, sair do loop

    candidates = selected
```

### FASE 3: Validate

#### 3.1 Reset DB e Seed Completo
```bash
docker compose down
docker volume rm filltheword_postgres_data
docker compose up -d --build
docker compose exec -T api alembic upgrade head
docker compose exec -T api python scripts/seed_data.py --full
```

#### 3.2 Validar Distribuição (SQL)
```sql
-- Consulta 1: Top 20 fontes por contagem
SELECT source_title, COUNT(*) as total
FROM sentence
WHERE source_title IS NOT NULL
GROUP BY source_title
ORDER BY total DESC
LIMIT 20;

-- Esperado: Nenhuma fonte > 25%, >= 15 fontes distintas
```

#### 3.3 Validar Amostra 200 Cards
```python
# Script: validate_variety.py
import requests

sources_spec4 = []
sources_lingvist = []

for i in range(200):
    # Spec4
    card = requests.get(f"http://localhost:8000/api/v1/cards/next-spec4?user_id={USER_ID}").json()
    sources_spec4.append(card.get('sentence_source'))

    # Lingvist
    card = requests.get(f"http://localhost:8000/api/v1/cards/next-lingvist?user_id={USER_ID}").json()
    sources_lingvist.append(card.get('sentence_source'))

# Contar fontes distintas
from collections import Counter
spec4_counts = Counter(sources_spec4)
lingvist_counts = Counter(sources_lingvist)

print(f"Spec4: {len(spec4_counts)} fontes distintas")
print(f"Lingvist: {len(lingvist_counts)} fontes distintas")
print(f"Top Spec4: {spec4_counts.most_common(5)}")
print(f"Top Lingvist: {lingvist_counts.most_common(5)}")

# Esperado: >= 15 fontes, top 1 <= 25%
```

### FASE 4: Documentação e PR

#### 4.1 Arquivos Gerados
- `api/data/en_sentence_bank.tsv` (TSV principal)
- `api/data/en_sentence_bank.txt` (texto plano)
- `api/data/EN_SENTENCE_BANK_SOURCES.md` (metadados)

#### 4.2 Conteúdo do EN_SENTENCE_BANK_SOURCES.md
```markdown
# English Sentence Bank Sources

Generated: 2025-12-25
Total sources: 35 classics
Total sentences: ~150K-200K

## Books Included

### Gothic/Horror (2)
- Frankenstein (Mary Shelley)
- The Picture of Dorian Gray (Oscar Wilde)

### Victorian (6)
- Great Expectations (Charles Dickens)
- Jane Eyre (Charlotte Brontë)
- Wuthering Heights (Emily Brontë)
- The Count of Monte Cristo (Alexandre Dumas)
- A Tale of Two Cities (Charles Dickens)
- Little Dorrit (Charles Dickens)

[... lista completa ...]

## License

All texts are from Project Gutenberg (public domain in the US).
https://www.gutenberg.org/policy/license.html
```

## Migration

### Database Changes
Nenhuma migration necessária (mantém schema Sentence existente).

### Data Changes
- Substituir `api/data/en_sentence_bank.tsv` e `.txt`
- Atualizar `api/data/EN_SENTENCE_BANK_SOURCES.md`
- Executar `seed --full` para repopular tabela Sentence

## Rollback Plan

Se necessário:
1. Reverter para TSV anterior (git checkout)
2. Re-executar seed --full
3. Sistema volta ao sentence bank anterior

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Download timeout de um livro | Seed parcial | Skip com warning, continuar com outros livros |
| TSV explode (>20MB) | Lentidão no seed | Limitar MAX_SENTENCES_PER_BOOK |
| Round-robin muito lento | Seed demora >10min | Usar apenas quando candidates >> sentence_count |
| Licença não é domínio público | Legal | Verificar IDs Gutenberg antes de incluir |

## Timeline Estimate

- FASE 1 (Proposal): 30 min
- FASE 2 (Apply): 2-3 horas (inclui downloads + processamento)
- FASE 3 (Validate): 1-2 horas (seed + SQL + amostragem)
- FASE 4 (PR): 30 min
- **Total**: 4-6 horas

## References

- Project Gutenberg: https://www.gutenberg.org/
- Sentence schema: `api/app/models/sentence.py`
- Build script: `api/scripts/build_en_sentence_bank.py`
- Seed script: `api/scripts/seed_data.py`
