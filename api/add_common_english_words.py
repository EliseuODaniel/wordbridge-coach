#!/usr/bin/env python3
"""
Script to add common English words that might be missing from WordFrequency
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

def add_common_english_words():
    """Add common English words that might be used in cards"""

    db = SessionLocal()
    try:
        # Common English words with approximate frequency rankings
        common_words = [
            # Very common words (rank 1-1000)
            ("milk", 1200, 92.6),
            ("water", 150, 69.5),
            ("bread", 800, 74.0),
            ("house", 300, 71.5),
            ("good", 100, 65.0),
            ("bad", 274, 68.2),
            ("big", 400, 72.5),
            ("small", 450, 73.0),
            ("new", 250, 70.0),
            ("old", 350, 72.0),
            ("nice", 600, 76.0),
            ("very", 50, 57.5),
            ("book", 500, 74.5),
            ("school", 700, 75.5),
            ("work", 180, 70.0),
            ("time", 80, 64.0),
            ("day", 90, 64.5),
            ("man", 200, 70.5),
            ("woman", 280, 70.8),
            ("child", 320, 71.0),
            ("food", 550, 75.0),
            ("eat", 380, 71.8),
            ("drink", 650, 75.8),
            ("sleep", 750, 76.5),
            ("play", 420, 73.2),
            ("read", 480, 74.0),
            ("write", 620, 76.2),
            ("walk", 580, 75.6),
            ("run", 520, 74.8),
            ("see", 160, 69.8),
            ("look", 240, 70.2),
            ("listen", 890, 77.7),
            ("talk", 680, 76.8),
            ("friend", 720, 76.2),
            ("family", 950, 78.2),
            ("home", 170, 70.2),
            ("car", 360, 71.5),
            ("city", 460, 73.5),
            ("country", 540, 75.2),
            ("world", 290, 70.6),
        ]

        added_count = 0
        updated_count = 0

        for word, rank, target_coverage in common_words:
            # Check if word already exists
            existing = db.query(WordFrequency).filter(
                WordFrequency.word == word,
                WordFrequency.language_code == 'en'
            ).first()

            if existing:
                # Update existing to ensure it has good coverage_pct
                existing.coverage_pct = target_coverage
                existing.frequency_score = max(0.1, 1.0 - (math.log(existing.rank) / math.log(10000)))
                updated_count += 1
            else:
                # Create new record
                word_freq = WordFrequency(
                    word=word,
                    language_code='en',
                    rank=rank,
                    coverage_pct=target_coverage,
                    frequency_score=max(0.1, 1.0 - (math.log(rank) / math.log(10000))),
                    band=1 if rank <= 1000 else 2 if rank <= 3000 else 3 if rank <= 6000 else 4,
                    is_active=True
                )
                db.add(word_freq)
                added_count += 1

        db.commit()

        print(f"Successfully added {added_count} new English words")
        print(f"Successfully updated {updated_count} existing English words")

        # Verify milk specifically
        milk_data = db.query(WordFrequency).filter(
            WordFrequency.word == 'milk',
            WordFrequency.language_code == 'en'
        ).first()

        if milk_data:
            print(f"\nMilk data updated: rank={milk_data.rank}, coverage_pct={milk_data.coverage_pct:.1f}%")
        else:
            print("\nERROR: Milk data not found after update!")

        return True

    except Exception as e:
        print(f"Error adding common English words: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = add_common_english_words()
    if success:
        print("Common English words added successfully!")
    else:
        print("Failed to add common English words")