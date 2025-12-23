#!/usr/bin/env python3
"""
Script to seed French word frequency data
"""

from app.core.database import SessionLocal
from app.models import WordFrequency, Language
import uuid

def seed_french_frequencies():
    """Seed French word frequency data for common words"""

    db = SessionLocal()
    try:
        # Get French language
        french_lang = db.query(Language).filter(Language.code == 'fr').first()
        if not french_lang:
            print("Error: French language not found")
            return False

        # Common French words with approximate frequency rankings
        # Based on linguistic frequency studies for French
        french_words_data = [
            # Function words (most frequent)
            ("le", 1, 85.0, 1),
            ("être", 2, 88.0, 1),
            ("et", 3, 90.0, 1),
            ("à", 4, 91.5, 1),
            ("les", 5, 92.5, 1),

            # Common verbs
            ("avoir", 10, 94.0, 1),
            ("faire", 15, 95.0, 1),
            ("dire", 20, 95.5, 1),
            ("pouvoir", 25, 96.0, 1),
            ("aller", 30, 96.3, 1),
            ("voir", 35, 96.5, 1),
            ("savoir", 40, 96.7, 1),
            ("venir", 45, 96.8, 1),
            ("vouloir", 50, 96.9, 1),
            ("passer", 60, 97.0, 1),
            ("mettre", 70, 97.1, 1),
            ("porter", 80, 97.2, 1),
            ("rendre", 90, 97.3, 1),
            ("devoir", 100, 97.4, 1),

            # Common nouns
            ("eau", 150, 97.6, 2),
            ("maison", 200, 97.8, 2),
            ("livre", 250, 98.0, 2),
            ("temps", 300, 98.1, 2),
            ("homme", 350, 98.2, 2),
            ("femme", 400, 98.3, 2),
            ("enfant", 450, 98.4, 2),
            ("main", 500, 98.5, 2),
            ("jour", 550, 98.6, 2),
            ("vie", 600, 98.7, 2),

            # Common adjectives
            ("grand", 800, 99.0, 3),
            ("petit", 850, 99.1, 3),
            ("bon", 900, 99.2, 3),
            ("nouveau", 950, 99.3, 3),
            ("premier", 1000, 99.4, 3),
        ]

        # Add frequency data
        added_count = 0
        updated_count = 0

        for word, rank, coverage_pct, band in french_words_data:
            # Check if word frequency already exists for French
            existing = db.query(WordFrequency).filter(
                WordFrequency.word == word,
                WordFrequency.language_code == 'fr'
            ).first()

            if existing:
                # Update existing record
                existing.rank = rank
                existing.coverage_pct = coverage_pct
                existing.frequency_score = 1.0 - (rank / 10000)  # Simple score calculation
                existing.band = band
                updated_count += 1
            else:
                # Create new record
                word_freq = WordFrequency(
                    word=word,
                    language_code='fr',
                    rank=rank,
                    coverage_pct=coverage_pct,
                    frequency_score=1.0 - (rank / 10000),  # Simple score calculation
                    band=band,
                    is_active=True
                )
                db.add(word_freq)
                added_count += 1

        # Commit changes
        db.commit()

        print(f"Successfully added {added_count} new French word frequencies")
        print(f"Successfully updated {updated_count} existing French word frequencies")

        return True

    except Exception as e:
        print(f"Error seeding French frequencies: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = seed_french_frequencies()
    if success:
        print("French frequency data seeded successfully!")
    else:
        print("Failed to seed French frequency data")