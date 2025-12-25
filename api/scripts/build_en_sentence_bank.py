#!/usr/bin/env python3
"""
Build English Sentence Bank from Project Gutenberg books.

Downloads public domain books, extracts sentences, filters and deduplicates,
saves to api/data/en_sentence_bank.txt for use in seed_data.py.

Usage:
    python scripts/build_en_sentence_bank.py

Output:
    - api/data/en_sentence_bank.txt (30k-80k sentences)
    - api/data/EN_SENTENCE_BANK_SOURCES.md (attribution)
"""

import sys
import os
import re
import hashlib
from pathlib import Path
from typing import List, Set, Tuple
import random

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Project Gutenberg books (public domain, pre-1929)
GUTENBERG_BOOKS = [
    # GOTHIC/HORROR (2)
    {
        "id": "84",
        "title": "Frankenstein",
        "author": "Mary Shelley",
        "year": 1818,
        "url": "https://www.gutenberg.org/files/84/84-0.txt"
    },
    {
        "id": "174",
        "title": "The Picture of Dorian Gray",
        "author": "Oscar Wilde",
        "year": 1890,
        "url": "https://www.gutenberg.org/files/174/174-0.txt"
    },

    # VICTORIAN CLASSICS (8)
    {
        "id": "1400",
        "title": "Great Expectations",
        "author": "Charles Dickens",
        "year": 1861,
        "url": "https://www.gutenberg.org/files/1400/1400-0.txt"
    },
    {
        "id": "1260",
        "title": "Jane Eyre",
        "author": "Charlotte Brontë",
        "year": 1847,
        "url": "https://www.gutenberg.org/files/1260/1260-0.txt"
    },
    {
        "id": "768",
        "title": "Wuthering Heights",
        "author": "Emily Brontë",
        "year": 1847,
        "url": "https://www.gutenberg.org/files/768/768-0.txt"
    },
    {
        "id": "1184",
        "title": "The Count of Monte Cristo",
        "author": "Alexandre Dumas",
        "year": 1844,
        "url": "https://www.gutenberg.org/files/1184/1184-0.txt"
    },
    {
        "id": "98",
        "title": "A Tale of Two Cities",
        "author": "Charles Dickens",
        "year": 1859,
        "url": "https://www.gutenberg.org/files/98/98-0.txt"
    },
    {
        "id": "580",
        "title": "The Mystery of Edwin Drood",
        "author": "Charles Dickens",
        "year": 1870,
        "url": "https://www.gutenberg.org/files/580/580-0.txt"
    },
    {
        "id": "766",
        "title": "The Woman in White",
        "author": "Wilkie Collins",
        "year": 1860,
        "url": "https://www.gutenberg.org/files/766/766-0.txt"
    },
    {
        "id": "1374",
        "title": "North and South",
        "author": "Elizabeth Gaskell",
        "year": 1855,
        "url": "https://www.gutenberg.org/files/1374/1374-0.txt"
    },

    # ADVENTURE (5)
    {
        "id": "120",
        "title": "Treasure Island",
        "author": "Robert Louis Stevenson",
        "year": 1883,
        "url": "https://www.gutenberg.org/files/120/120-0.txt"
    },
    {
        "id": "1257",
        "title": "The Three Musketeers",
        "author": "Alexandre Dumas",
        "year": 1844,
        "url": "https://www.gutenberg.org/files/1257/1257-0.txt"
    },
    {
        "id": "844",
        "title": "The Man in the Iron Mask",
        "author": "Alexandre Dumas",
        "year": 1850,
        "url": "https://www.gutenberg.org/files/844/844-0.txt"
    },
    {
        "id": "520",
        "title": "Ivanhoe",
        "author": "Walter Scott",
        "year": 1820,
        "url": "https://www.gutenberg.org/files/520/520-0.txt"
    },
    {
        "id": "2044",
        "title": "The Sea-Hawk",
        "author": "Rafael Sabatini",
        "year": 1915,
        "url": "https://www.gutenberg.org/files/2044/2044-0.txt"
    },

    # AMERICAN CLASSICS (6)
    {
        "id": "2701",
        "title": "Moby-Dick",
        "author": "Herman Melville",
        "year": 1851,
        "url": "https://www.gutenberg.org/files/2701/2701-0.txt"
    },
    {
        "id": "76",
        "title": "Adventures of Huckleberry Finn",
        "author": "Mark Twain",
        "year": 1884,
        "url": "https://www.gutenberg.org/files/76/76-0.txt"
    },
    {
        "id": "74",
        "title": "The Adventures of Tom Sawyer",
        "author": "Mark Twain",
        "year": 1876,
        "url": "https://www.gutenberg.org/files/74/74-0.txt"
    },
    {
        "id": "215",
        "title": "The Call of the Wild",
        "author": "Jack London",
        "year": 1903,
        "url": "https://www.gutenberg.org/files/215/215-0.txt"
    },
    {
        "id": "603",
        "title": "The Last of the Mohicans",
        "author": "James Fenimore Cooper",
        "year": 1826,
        "url": "https://www.gutenberg.org/files/603/603-0.txt"
    },
    {
        "id": "36",
        "title": "The War of the Worlds",
        "author": "H.G. Wells",
        "year": 1898,
        "url": "https://www.gutenberg.org/files/36/36-0.txt"
    },

    # FANTASY/CHILDREN (6)
    {
        "id": "11",
        "title": "Alice's Adventures in Wonderland",
        "author": "Lewis Carroll",
        "year": 1865,
        "url": "https://www.gutenberg.org/files/11/11-0.txt"
    },
    {
        "id": "55",
        "title": "The Wonderful Wizard of Oz",
        "author": "L. Frank Baum",
        "year": 1900,
        "url": "https://www.gutenberg.org/files/55/55-0.txt"
    },
    {
        "id": "16",
        "title": "Peter Pan",
        "author": "J.M. Barrie",
        "year": 1911,
        "url": "https://www.gutenberg.org/files/16/16-0.txt"
    },
    {
        "id": "91",
        "title": "The Wind in the Willows",
        "author": "Kenneth Grahame",
        "year": 1908,
        "url": "https://www.gutenberg.org/files/91/91-0.txt"
    },
    {
        "id": "113",
        "title": "The Secret Garden",
        "author": "Frances Hodgson Burnett",
        "year": 1911,
        "url": "https://www.gutenberg.org/files/113/113-0.txt"
    },
    {
        "id": "7321",
        "title": "The Princess and the Goblin",
        "author": "George MacDonald",
        "year": 1872,
        "url": "https://www.gutenberg.org/files/7321/7321-0.txt"
    },

    # SCIENCE FICTION (3)
    {
        "id": "35",
        "title": "The Time Machine",
        "author": "H.G. Wells",
        "year": 1895,
        "url": "https://www.gutenberg.org/files/35/35-0.txt"
    },
    {
        "id": "345",
        "title": "The Invisible Man",
        "author": "H.G. Wells",
        "year": 1897,
        "url": "https://www.gutenberg.org/files/345/345-0.txt"
    },
    {
        "id": "1200",
        "title": "From the Earth to the Moon",
        "author": "Jules Verne",
        "year": 1870,
        "url": "https://www.gutenberg.org/files/1200/1200-0.txt"
    },

    # ROMANCE (6)
    {
        "id": "1342",
        "title": "Pride and Prejudice",
        "author": "Jane Austen",
        "year": 1813,
        "url": "https://www.gutenberg.org/files/1342/1342-0.txt"
    },
    {
        "id": "141",
        "title": "Sense and Sensibility",
        "author": "Jane Austen",
        "year": 1811,
        "url": "https://www.gutenberg.org/files/141/141-0.txt"
    },
    {
        "id": "161",
        "title": "Emma",
        "author": "Jane Austen",
        "year": 1815,
        "url": "https://www.gutenberg.org/files/161/161-0.txt"
    },
    {
        "id": "3751",
        "title": "Vanity Fair",
        "author": "William Makepeace Thackeray",
        "year": 1848,
        "url": "https://www.gutenberg.org/files/3751/3751-0.txt"
    },
    {
        "id": "1416",
        "title": "My Man Jeeves",
        "author": "P.G. Wodehouse",
        "year": 1919,
        "url": "https://www.gutenberg.org/files/1416/1416-0.txt"
    },
    {
        "id": "3020",
        "title": "The Ball and the Cross",
        "author": "G.K. Chesterton",
        "year": 1910,
        "url": "https://www.gutenberg.org/files/3020/3020-0.txt"
    },

    # MYSTERY/DETECTIVE (2)
    {
        "id": "1661",
        "title": "The Adventures of Sherlock Holmes",
        "author": "Arthur Conan Doyle",
        "year": 1892,
        "url": "https://www.gutenberg.org/files/1661/1661-0.txt"
    },
    {
        "id": "2097",
        "title": "The Mystery of the Yellow Room",
        "author": "Gaston Leroux",
        "year": 1908,
        "url": "https://www.gutenberg.org/files/2097/2097-0.txt"
    },

    # ORIGINAL FROM CURRENT SENTENCE BANK (2)
    {
        "id": "345",
        "title": "Dracula",
        "author": "Bram Stoker",
        "year": 1897,
        "url": "https://www.gutenberg.org/files/345/345-0.txt"
    },
]

# Filtragem
MIN_SENTENCE_LENGTH = 20  # Caracteres
MAX_SENTENCE_LENGTH = 140  # Caracteres
MIN_WORDS = 3  # Palavras mínimas
MAX_SENTENCES_PER_BOOK = 8000  # Limite para não explodir (balanceado)

# Diretórios
DATA_DIR = Path(__file__).parent.parent / "data"
SENTENCE_BANK_PATH = DATA_DIR / "en_sentence_bank.txt"
SENTENCE_BANK_TSV_PATH = DATA_DIR / "en_sentence_bank.tsv"
SOURCES_PATH = DATA_DIR / "EN_SENTENCE_BANK_SOURCES.md"


def download_book(url: str) -> str:
    """Download book from Project Gutenberg"""
    import urllib.request

    print(f"  Downloading from {url}...")
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            text = response.read().decode('utf-8')
        return text
    except Exception as e:
        print(f"  ❌ Error downloading: {e}")
        return ""


def remove_gutenberg_headers(text: str) -> str:
    """Remove Project Gutenberg header/footer"""
    # Find start marker
    start_markers = [
        "*** START OF THIS PROJECT GUTENBERG EBOOK",
        "***START OF THE PROJECT GUTENBERG EBOOK",
    ]

    start_idx = -1
    for marker in start_markers:
        idx = text.find(marker)
        if idx != -1:
            start_idx = idx + len(marker)
            break

    if start_idx == -1:
        # No marker found, return as-is
        return text

    # Find end marker
    end_markers = [
        "*** END OF THIS PROJECT GUTENBERG EBOOK",
        "*** END OF THE PROJECT GUTENBERG EBOOK",
    ]

    end_idx = -1
    for marker in end_markers:
        idx = text.find(marker, start_idx)
        if idx != -1:
            end_idx = idx
            break

    if end_idx == -1:
        # No end marker, use everything after start
        return text[start_idx:]

    return text[start_idx:end_idx]


def extract_sentences(text: str) -> List[str]:
    """
    Extract sentences from text using regex.

    Simple sentence boundary detection: [.!?]+\\s+
    """
    # Split by sentence boundaries
    sentences = re.split(r'[.!?]+\s+', text)

    # Filter and clean
    filtered = []
    for sent in sentences:
        # Normalize whitespace (remove newlines/tabs within sentence)
        sent = re.sub(r'\s+', ' ', sent).strip()

        # Skip empty
        if not sent:
            continue

        # Skip too short/long
        if len(sent) < MIN_SENTENCE_LENGTH or len(sent) > MAX_SENTENCE_LENGTH:
            continue

        # Skip if contains non-ASCII (accents, etc)
        if not sent.isascii():
            continue

        # Skip if not enough words
        words = sent.split()
        if len(words) < MIN_WORDS:
            continue

        # Skip if starts with digit or special char
        if sent and sent[0] in '0123456789*"\'(':
            continue

        # Remove quotes at start/end
        sent = sent.strip('"\'“”‘’')

        filtered.append(sent)

    return filtered


def deduplicate_sentences(all_sentences: List[str]) -> List[str]:
    """Remove duplicate sentences using SHA256 hash"""
    seen_hashes = set()
    unique = []

    for sent in all_sentences:
        # Hash for deduplication
        sent_hash = hashlib.sha256(sent.lower().encode()).hexdigest()

        if sent_hash not in seen_hashes:
            seen_hashes.add(sent_hash)
            unique.append(sent)

    return unique


def shuffle_sentences(sentences_with_sources: List[dict]) -> List[dict]:
    """Shuffle sentences for randomness"""
    random.shuffle(sentences_with_sources)
    return sentences_with_sources


def save_sentence_bank(sentences: List[str], sources_info: List[dict]):
    """Save sentence bank and sources file"""
    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Save sentences
    print(f"\n💾 Saving {len(sentences)} sentences to {SENTENCE_BANK_PATH}...")
    with open(SENTENCE_BANK_PATH, 'w', encoding='utf-8') as f:
        for sent in sentences:
            f.write(sent + '\n')

    print(f"✅ Saved {len(sentences)} sentences")

    # Save sources info
    sources_md = generate_sources_markdown(sources_info, len(sentences))
    with open(SOURCES_PATH, 'w', encoding='utf-8') as f:
        f.write(sources_md)

    print(f"✅ Saved sources to {SOURCES_PATH}")


def generate_sources_markdown(sources_info: List[dict], total_sentences: int) -> str:
    """Generate EN_SENTENCE_BANK_SOURCES.md content"""
    md = """# English Sentence Bank Sources

This file lists the sources used to generate `en_sentence_bank.txt`.

## Sources

"""
    for info in sources_info:
        md += f"""{info['index']}. **{info['title']}** ({info['year']}) by {info['author']}
   - Project Gutenberg ID: {info['id']}
   - URL: {info['url']}
   - License: Public Domain (published before 1929)
   - Sentences contributed: ~{info['sentence_count']:,}

"""

    md += f"""## Total Sentences
{total_sentences:,} unique sentences (after deduplication and filtering)

## Generation Method
1. Download from Project Gutenberg (public domain)
2. Remove Gutenberg headers/footers
3. Extract sentences using regex `[.!?]+\\s+`
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

Generated: {info['date']}
Script: api/scripts/build_en_sentence_bank.py
"""
    return md


def save_sentence_bank_with_sources(sentences_with_sources: List[dict], sources_info: List[dict]):
    """Save sentence bank (TXT + TSV) and sources file"""
    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Extract sentences for TXT (backward compatibility)
    sentences = [s['text'] for s in sentences_with_sources]

    # Save TXT (backward compatible)
    print(f"\n💾 Saving {len(sentences)} sentences to {SENTENCE_BANK_PATH}...")
    with open(SENTENCE_BANK_PATH, 'w', encoding='utf-8') as f:
        for sent in sentences:
            f.write(sent + '\n')

    print(f"✅ Saved {len(sentences)} sentences to TXT")

    # Save TSV (new format with source metadata)
    print(f"\n💾 Saving {len(sentences_with_sources)} sentences to {SENTENCE_BANK_TSV_PATH}...")
    with open(SENTENCE_BANK_TSV_PATH, 'w', encoding='utf-8') as f:
        # Header
        f.write('gutenberg_id\ttitle\tauthor\tsentence\n')

        # Rows
        for entry in sentences_with_sources:
            # Escape tabs in sentence
            sentence = entry['text'].replace('\t', '    ')  # Replace tabs with spaces
            f.write(f"{entry['gutenberg_id']}\t{entry['title']}\t{entry['author']}\t{sentence}\n")

    print(f"✅ Saved {len(sentences_with_sources)} sentences to TSV")

    # Save sources info
    sources_md = generate_sources_markdown(sources_info, len(sentences_with_sources))
    with open(SOURCES_PATH, 'w', encoding='utf-8') as f:
        f.write(sources_md)

    print(f"✅ Saved sources to {SOURCES_PATH}")


def main():
    """Main function"""
    print("=" * 60)
    print("📚 Building English Sentence Bank from Project Gutenberg")
    print("=" * 60)
    print()

    all_sentences_with_sources = []  # List of dict with text + source metadata
    sources_info = []

    for idx, book in enumerate(GUTENBERG_BOOKS, 1):
        print(f"\n📖 [{idx}/{len(GUTENBERG_BOOKS)}] {book['title']}")
        print(f"   Author: {book['author']} ({book['year']})")
        print(f"   ID: {book['id']}")

        # Download
        text = download_book(book['url'])
        if not text:
            print(f"   ⚠️  Skipping (download failed)")
            continue

        # Remove headers/footers
        text = remove_gutenberg_headers(text)
        print(f"   Text length: {len(text):,} characters")

        # Extract sentences
        sentences = extract_sentences(text)
        print(f"   Extracted: {len(sentences):,} sentences")

        # Balanceamento: shuffle antes de fatiar (amostra representativa)
        random.shuffle(sentences)
        print(f"   🔀 Shuffled for balanced sampling")

        # Limit to avoid explosion
        if len(sentences) > MAX_SENTENCES_PER_BOOK:
            sentences = sentences[:MAX_SENTENCES_PER_BOOK]
            print(f"   Limited to: {len(sentences):,} sentences")

        # Add source metadata
        for sent in sentences:
            all_sentences_with_sources.append({
                'text': sent,
                'gutenberg_id': book['id'],
                'title': book['title'],
                'author': book['author']
            })

        # Track source info
        sources_info.append({
            "index": idx,
            "title": book['title'],
            "author": book['author'],
            "year": book['year'],
            "id": book['id'],
            "url": book['url'],
            "sentence_count": len(sentences),
            "date": None  # Will be set at the end
        })

    print(f"\n📊 Total sentences extracted: {len(all_sentences_with_sources):,}")

    # Deduplicate (by text, case-insensitive)
    print("🔍 Deduplicating...")
    seen_hashes = set()
    unique_with_sources = []

    for entry in all_sentences_with_sources:
        sent_hash = hashlib.sha256(entry['text'].lower().encode()).hexdigest()
        if sent_hash not in seen_hashes:
            seen_hashes.add(sent_hash)
            unique_with_sources.append(entry)

    print(f"   Unique: {len(unique_with_sources):,} sentences")
    print(f"   Removed: {len(all_sentences_with_sources) - len(unique_with_sources):,} duplicates")

    # Shuffle
    print("🔀 Shuffling...")
    shuffled_with_sources = shuffle_sentences(unique_with_sources)

    # Save
    from datetime import datetime
    date_str = datetime.now().strftime("%Y-%m-%d")
    for info in sources_info:
        info['date'] = date_str

    save_sentence_bank_with_sources(shuffled_with_sources, sources_info)

    print()
    print("=" * 60)
    print("✅ Sentence bank built successfully!")
    print(f"📦 Location TXT: {SENTENCE_BANK_PATH}")
    print(f"📦 Location TSV: {SENTENCE_BANK_TSV_PATH}")
    print(f"📊 Size: {len(shuffled_with_sources):,} sentences")
    print(f"💾 Disk size TXT: {SENTENCE_BANK_PATH.stat().st_size / 1024 / 1024:.1f} MB")
    print(f"💾 Disk size TSV: {SENTENCE_BANK_TSV_PATH.stat().st_size / 1024 / 1024:.1f} MB")
    print("=" * 60)


if __name__ == "__main__":
    main()
