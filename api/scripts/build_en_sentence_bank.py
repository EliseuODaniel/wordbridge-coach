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
    {
        "id": "1342",
        "title": "Pride and Prejudice",
        "author": "Jane Austen",
        "year": 1813,
        "url": "https://www.gutenberg.org/files/1342/1342-0.txt"
    },
    {
        "id": "11",
        "title": "Alice's Adventures in Wonderland",
        "author": "Lewis Carroll",
        "year": 1865,
        "url": "https://www.gutenberg.org/files/11/11-0.txt"
    },
    {
        "id": "1661",
        "title": "The Adventures of Sherlock Holmes",
        "author": "Arthur Conan Doyle",
        "year": 1892,
        "url": "https://www.gutenberg.org/files/1661/1661-0.txt"
    },
    {
        "id": "345",
        "title": "Dracula",
        "author": "Bram Stoker",
        "year": 1897,
        "url": "https://www.gutenberg.org/files/345/345-0.txt"
    }
]

# Filtragem
MIN_SENTENCE_LENGTH = 20  # Caracteres
MAX_SENTENCE_LENGTH = 140  # Caracteres
MIN_WORDS = 3  # Palavras mínimas
MAX_SENTENCES_PER_BOOK = 25000  # Limite para não explodir

# Diretórios
DATA_DIR = Path(__file__).parent.parent / "data"
SENTENCE_BANK_PATH = DATA_DIR / "en_sentence_bank.txt"
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
        sent = sent.strip()

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


def shuffle_sentences(sentences: List[str]) -> List[str]:
    """Shuffle sentences for randomness"""
    random.shuffle(sentences)
    return sentences


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


def main():
    """Main function"""
    print("=" * 60)
    print("📚 Building English Sentence Bank from Project Gutenberg")
    print("=" * 60)
    print()

    all_sentences = []
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

        # Limit to avoid explosion
        if len(sentences) > MAX_SENTENCES_PER_BOOK:
            sentences = sentences[:MAX_SENTENCES_PER_BOOK]
            print(f"   Limited to: {len(sentences):,} sentences")

        all_sentences.extend(sentences)

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

    print(f"\n📊 Total sentences extracted: {len(all_sentences):,}")

    # Deduplicate
    print("🔍 Deduplicating...")
    unique_sentences = deduplicate_sentences(all_sentences)
    print(f"   Unique: {len(unique_sentences):,} sentences")
    print(f"   Removed: {len(all_sentences) - len(unique_sentences):,} duplicates")

    # Shuffle
    print("🔀 Shuffling...")
    shuffled_sentences = shuffle_sentences(unique_sentences)

    # Save
    from datetime import datetime
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    for info in sources_info:
        info['date'] = date_str

    save_sentence_bank(shuffled_sentences, sources_info)

    print()
    print("=" * 60)
    print("✅ Sentence bank built successfully!")
    print(f"📦 Location: {SENTENCE_BANK_PATH}")
    print(f"📊 Size: {len(shuffled_sentences):,} sentences")
    print(f"💾 Disk size: {SENTENCE_BANK_PATH.stat().st_size / 1024 / 1024:.1f} MB")
    print("=" * 60)


if __name__ == "__main__":
    main()
