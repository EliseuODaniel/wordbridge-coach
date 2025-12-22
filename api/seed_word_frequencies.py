#!/usr/bin/env python3
"""
Seed WordFrequency data with high-frequency English words
Based on Google 10,000 English words list and wordfreq library
"""

from sqlalchemy.orm import sessionmaker
from app.core.database import engine, SessionLocal
from app.models import Word, WordFrequency
import uuid
import time

# High frequency English words (top 100) - subset for demo
# In production, this would be loaded from Google-10000 or wordfreq
HIGH_FREQUENCY_WORDS = [
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "I",
    "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
    "this", "but", "his", "by", "from", "they", "we", "say", "her", "she",
    "or", "an", "will", "my", "one", "all", "would", "there", "their", "what",
    "so", "up", "out", "if", "about", "who", "get", "which", "go", "me",
    "when", "make", "can", "like", "time", "no", "just", "him", "know", "take",
    "people", "into", "year", "your", "good", "some", "could", "them", "see", "other",
    "than", "then", "now", "look", "only", "come", "its", "over", "think", "also",
    "back", "after", "use", "two", "how", "our", "work", "first", "well", "way",
    "even", "new", "want", "because", "any", "these", "give", "day", "most", "us",
    "is", "was", "are", "been", "has", "had", "were", "said", "did", "having",
    "may", "am"
]

def create_word_frequency_data():
    """Create WordFrequency records with frequency bands"""
    db = SessionLocal()

    try:
        print("Creating WordFrequency data...")

        # Clear existing data
        db.query(WordFrequency).delete()
        db.commit()

        batch_data = []
        start_time = time.time()

        for i, word in enumerate(HIGH_FREQUENCY_WORDS):
            rank = i + 1  # 1-based ranking

            # Calculate frequency band
            if rank <= 1000:
                band = 1  # Most frequent
            elif rank <= 3000:
                band = 2  # Very frequent
            elif rank <= 6000:
                band = 3  # Frequent
            elif rank <= 10000:
                band = 4  # Common
            else:
                band = 5  # Less common

            # Calculate frequency score (inverse of rank, normalized)
            frequency_score = 10000.0 / rank

            word_freq = WordFrequency(
                id=str(uuid.uuid4()),
                word=word.lower(),
                rank=rank,
                frequency_score=frequency_score,
                band=band,
                is_active=True
            )

            batch_data.append(word_freq)

            # Insert in batches
            if len(batch_data) >= 100:
                db.bulk_save_objects(batch_data)
                db.commit()
                batch_data = []
                print(f"Processed {rank} words...")

        # Insert remaining
        if batch_data:
            db.bulk_save_objects(batch_data)
            db.commit()

        end_time = time.time()
        print(f"✅ Created {len(HIGH_FREQUENCY_WORDS)} WordFrequency records")
        print(f"   Time: {end_time - start_time:.2f}s")
        print(f"   Band 1 (1-1000): {sum(1 for w in HIGH_FREQUENCY_WORDS if w and HIGH_FREQUENCY_WORDS.index(w) + 1 <= 1000)} words")
        print(f"   Band 2 (1001-3000): {sum(1 for w in HIGH_FREQUENCY_WORDS if w and 1000 < HIGH_FREQUENCY_WORDS.index(w) + 1 <= 3000)} words")
        print(f"   Band 3 (3001-6000): {sum(1 for w in HIGH_FREQUENCY_WORDS if w and 3000 < HIGH_FREQUENCY_WORDS.index(w) + 1 <= 6000)} words")
        print(f"   Band 4 (6001-10000): {sum(1 for w in HIGH_FREQUENCY_WORDS if w and 6000 < HIGH_FREQUENCY_WORDS.index(w) + 1 <= 10000)} words")

    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()

def link_existing_words():
    """Link existing words to WordFrequency data"""
    db = SessionLocal()

    try:
        print("\nLinking existing words to frequency data...")

        # Get all word frequencies
        word_freqs = db.query(WordFrequency).all()
        freq_map = {wf.word: wf for wf in word_freqs}

        # Update existing words
        words_updated = 0
        words = db.query(Word).all()

        for word in words:
            word_text = word.text.lower()
            if word_text in freq_map:
                word.frequency_rank = freq_map[word_text].rank
                words_updated += 1

        db.commit()
        print(f"✅ Updated frequency_rank for {words_updated}/{len(words)} existing words")

        # Show sample
        sample_words = db.query(Word).filter(Word.frequency_rank.isnot(None)).limit(10).all()
        print(f"   Sample: {[f'{w.text}(rank:{w.frequency_rank})' for w in sample_words]}")

    except Exception as e:
        db.rollback()
        print(f"❌ Error linking words: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Starting WordFrequency seed...")
    create_word_frequency_data()
    link_existing_words()
    print("✅ WordFrequency seeding completed!")