#!/usr/bin/env python3
"""
Script to populate coverage_pct for English WordFrequency data
"""

from app.core.database import SessionLocal
from app.models import WordFrequency
import math

def calculate_coverage_pct(rank: int) -> float:
    """Calculate cumulative coverage percentage based on Zipf's law"""
    if rank <= 1:
        return 5.0
    elif rank <= 10:
        return 15.0 + (rank - 1) * 2.0  # 15-33%
    elif rank <= 100:
        return 33.0 + (rank - 10) * 0.35  # 33-65%
    elif rank <= 1000:
        return 65.0 + (rank - 100) * 0.03  # 65-92%
    elif rank <= 5000:
        return 92.0 + (rank - 1000) * 0.002  # 92-95%
    else:
        return 95.0 + min(4.0, (rank - 5000) * 0.0002)  # 95-99%

def update_en_coverage_pct():
    """Update coverage_pct for all English words"""

    db = SessionLocal()
    try:
        # Get all English words without coverage_pct
        en_words = db.query(WordFrequency).filter(
            WordFrequency.language_code == 'en',
            WordFrequency.coverage_pct.is_(None)
        ).all()

        print(f"Found {len(en_words)} English words without coverage_pct")

        updated_count = 0
        for word_freq in en_words:
            word_freq.coverage_pct = calculate_coverage_pct(word_freq.rank)
            word_freq.frequency_score = max(0.1, 1.0 - (math.log(word_freq.rank) / math.log(10000)))
            updated_count += 1

            # Show progress every 1000 words
            if updated_count % 1000 == 0:
                print(f"Updated {updated_count}/{len(en_words)} words...")

        db.commit()
        print(f"Successfully updated coverage_pct for {updated_count} English words")

        # Verify a few examples
        examples = db.query(WordFrequency).filter(
            WordFrequency.language_code == 'en'
        ).order_by(WordFrequency.rank).limit(10).all()

        print("\nExample updates:")
        for ex in examples:
            print(f"  {ex.word}: rank={ex.rank}, coverage_pct={ex.coverage_pct:.1f}%, score={ex.frequency_score:.3f}")

        return True

    except Exception as e:
        print(f"Error updating English coverage_pct: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = update_en_coverage_pct()
    if success:
        print("English coverage_pct update completed successfully!")
    else:
        print("Failed to update English coverage_pct")