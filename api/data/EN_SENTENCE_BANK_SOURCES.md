# English Sentence Bank Sources

This file lists the sources used to generate `en_sentence_bank.txt`.

## Sources

1. **Pride and Prejudice** (1813) by Jane Austen
   - Project Gutenberg ID: 1342
   - URL: https://www.gutenberg.org/files/1342/1342-0.txt
   - License: Public Domain (published before 1929)
   - Sentences contributed: ~2,522

2. **Alice's Adventures in Wonderland** (1865) by Lewis Carroll
   - Project Gutenberg ID: 11
   - URL: https://www.gutenberg.org/files/11/11-0.txt
   - License: Public Domain (published before 1929)
   - Sentences contributed: ~122

3. **The Adventures of Sherlock Holmes** (1892) by Arthur Conan Doyle
   - Project Gutenberg ID: 1661
   - URL: https://www.gutenberg.org/files/1661/1661-0.txt
   - License: Public Domain (published before 1929)
   - Sentences contributed: ~1,819

4. **Dracula** (1897) by Bram Stoker
   - Project Gutenberg ID: 345
   - URL: https://www.gutenberg.org/files/345/345-0.txt
   - License: Public Domain (published before 1929)
   - Sentences contributed: ~3,891

## Total Sentences
8,348 unique sentences (after deduplication and filtering)

## Generation Method
1. Download from Project Gutenberg (public domain)
2. Remove Gutenberg headers/footers
3. Extract sentences using regex `[.!?]+\s+`
4. Filter by length (20-140 characters) and word count (3+ words)
5. Remove non-ASCII sentences
6. Deduplicate using SHA256 hash
7. Shuffle randomly

## Usage in Seed
The sentence bank is used by `api/scripts/seed_data.py:create_10k_vocabulary()` to create
natural, contextually appropriate sentences for the top 10,000 English words.

## Legal Notice
All source materials are in the **public domain** (published before 1929 in the United States).
Used for educational purposes (language learning).
Complies with Project Gutenberg terms of use.

---

Generated: 2025-12-23
Script: api/scripts/build_en_sentence_bank.py
