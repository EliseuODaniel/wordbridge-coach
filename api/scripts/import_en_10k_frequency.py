#!/usr/bin/env python3
"""
Import top 10.000 English words from OpenSubtitles2016 frequency data.

This script reads api/data/en_top_10000.txt (generated from FrequencyWords project)
and populates the word_frequencies table with real English word frequency data.

Dataset: OpenSubtitles2016 (via FrequencyWords by Hermit Dave)
License: MIT (FrequencyWords) + Academic attribution (OpenSubtitles2016)
Format: rank word frequency part_of_speech
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.models.word_frequency import WordFrequency
from app.models.language import Language
from app.core.database import SessionLocal


def import_word_frequencies(
    db: Session,
    filepath: str = "/app/data/en_top_10000.txt",
    language_code: str = "en"
):
    """
    Import top 10.000 word frequencies from OpenSubtitles2016 dataset.

    Args:
        db: Database session
        filepath: Path to en_top_10000.txt
        language_code: Language code (default: 'en')
    """
    print(f"📥 Importing word frequencies from {filepath}")

    # Check if file exists
    if not os.path.exists(filepath):
        print(f"❌ Error: File not found: {filepath}")
        print(f"   Current working directory: {os.getcwd()}")
        print(f"   Please run the download command first:")
        print(f"   curl -L -o /tmp/en_50k.txt 'https://github.com/hermitdave/FrequencyWords/raw/master/content/2016/en/en_50k.txt'")
        print(f"   head -n 10000 /tmp/en_50k.txt | awk '{{print NR, $1, $2, \"UNK\"}}' > api/data/en_top_10000.txt")
        return 0

    # Get or verify language exists
    language = db.query(Language).filter(Language.code == language_code).first()
    if not language:
        print(f"❌ Error: Language '{language_code}' not found in database")
        print(f"   Please ensure languages are seeded first (run seed_data.py)")
        return 0

    print(f"✅ Language found: {language.name} ({language_code})")

    # Read and parse file
    imported_count = 0
    skipped_count = 0
    errors = []

    with open(filepath, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            try:
                # Parse: rank word frequency part_of_speech
                # Note: part_of_speech is ignored (not stored in WordFrequency model)
                parts = line.split()
                if len(parts) < 3:
                    errors.append(f"Line {line_num}: Invalid format (expected at least 3 fields, got {len(parts)})")
                    skipped_count += 1
                    continue

                rank = int(parts[0])
                word = parts[1].lower()
                frequency_score = float(parts[2])  # Raw frequency from corpus
                # parts[3] would be part_of_speech (UNK), but model doesn't store it

                # Validate rank range
                if rank < 1 or rank > 10000:
                    errors.append(f"Line {line_num}: Rank {rank} out of range (1-10000)")
                    skipped_count += 1
                    continue

                # Check if already exists
                existing = db.query(WordFrequency).filter(
                    WordFrequency.word == word,
                    WordFrequency.language_code == language_code
                ).first()

                if existing:
                    # Update if rank is different
                    if existing.rank != rank:
                        existing.rank = rank
                        existing.frequency_score = frequency_score
                        existing.band = WordFrequency.get_band_from_rank(rank)
                        db.flush()
                        imported_count += 1
                    else:
                        skipped_count += 1
                else:
                    # Create new entry
                    wf = WordFrequency(
                        word=word,
                        language_code=language_code,
                        rank=rank,
                        frequency_score=frequency_score,
                        band=WordFrequency.get_band_from_rank(rank),
                        is_active=True
                    )
                    db.add(wf)
                    imported_count += 1

                # Progress indicator every 1000 words
                if imported_count % 1000 == 0:
                    print(f"   Processed {imported_count} words...")

            except Exception as e:
                errors.append(f"Line {line_num}: {str(e)}")
                skipped_count += 1
                continue

    # Commit all changes
    db.commit()

    # Summary
    print(f"\n✅ Import completed!")
    print(f"📊 Summary:")
    print(f"   Imported/Updated: {imported_count}")
    print(f"   Skipped (already exists): {skipped_count}")
    print(f"   Errors: {len(errors)}")

    if errors:
        print(f"\n⚠️  First 10 errors:")
        for error in errors[:10]:
            print(f"   - {error}")

    # Verify count
    total_count = db.query(WordFrequency).filter(
        WordFrequency.language_code == language_code,
        WordFrequency.rank <= 10000
    ).count()

    print(f"\n📈 Verification:")
    print(f"   Total word_frequencies for {language_code} (rank <= 10000): {total_count}")

    if total_count == 10000:
        print(f"   ✅ SUCCESS: All 10.000 words imported!")
    else:
        print(f"   ⚠️  WARNING: Expected 10.000, got {total_count}")

    return imported_count


def main():
    """Main function"""
    db = SessionLocal()

    try:
        import_word_frequencies(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
