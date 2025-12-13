#!/usr/bin/env python3
"""
Simple seed data script using direct SQL to avoid ORM mapping issues
"""

import sys
import os
import uuid
from datetime import datetime

# Add the parent directory to the path to import app modules
sys.path.append('/app')

from app.core.database import engine

def main():
    """Simple seed using raw SQL"""
    print("Starting simple seed data creation...")

    conn = engine.connect()
    try:
        # Check if we already have data
        result = conn.execute("SELECT COUNT(*) FROM word")
        word_count = result.fetchone()[0]

        if word_count >= 8:
            print("Seed data already exists, skipping creation")
            return

        print("Creating seed data using raw SQL...")

        # Get English language ID
        cur.execute("SELECT id FROM language WHERE code = 'en' LIMIT 1")
        lang_result = cur.fetchone()
        if not lang_result:
            print("English language not found, creating...")
            en_lang_id = uuid.uuid4()
            cur.execute("""
                INSERT INTO language (id, code, name, voice_model, voice_type, is_active, created_at, updated_at)
                VALUES (%s, 'en', 'English', 'lessac-glow_tts', 'female', true, %s, %s)
            """, (en_lang_id, datetime.utcnow(), datetime.utcnow()))
        else:
            en_lang_id = lang_result[0]

        # Words to create
        words_data = [
            ('book', 'book', 'noun', '/bʊk/', 100, 1),
            ('house', 'house', 'noun', '/haʊs/', 200, 1),
            ('water', 'water', 'noun', '/ˈwɔːtər/', 50, 1),
            ('read', 'read', 'verb', '/riːd/', 150, 1),
            ('write', 'write', 'verb', '/raɪt/', 180, 1),
            ('beautiful', 'beautiful', 'adjective', '/ˈbjuːtɪfəl/', 500, 2),
            ('quickly', 'quickly', 'adverb', '/ˈkwɪkli/', 300, 2),
            ('friend', 'friend', 'noun', '/frɛnd/', 250, 1)
        ]

        word_ids = {}
        for lemma, text, pos, pronunciation, freq, difficulty in words_data:
            word_id = uuid.uuid4()
            word_ids[lemma] = word_id
            cur.execute("""
                INSERT INTO word (id, lemma, text, part_of_speech, pronunciation, frequency_rank, difficulty, language_id, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (word_id, lemma, text, pos, pronunciation, freq, difficulty, en_lang_id, datetime.utcnow(), datetime.utcnow()))

        # Sentences to create
        sentences_data = [
            ('book', 'The ___ is on the table.', 'O livro está na mesa.', 'example', 4, 8, 1),
            ('house', 'They live in a big ___.', 'Eles moram em uma casa grande.', 'example', 18, 23, 1),
            ('water', 'Please give me some ___ to drink.', 'Por favor, me dê um pouco de ___ para beber.', 'example', 20, 25, 1),
            ('read', 'I like to ___ books every day.', 'Eu gosto de ___ livros todos os dias.', 'usage', 13, 17, 1),
            ('write', 'Can you ___ your name here?', 'Você pode ___ seu nome aqui?', 'question', 8, 13, 1),
            ('beautiful', 'What a ___ sunset!', 'Que pôr do sol ___!', 'expression', 7, 16, 2),
            ('quickly', 'She ran ___ to catch the bus.', 'Ela correu ___ para pegar o ônibus.', 'example', 12, 19, 2),
            ('friend', 'My best ___ is coming to visit.', 'Meu melhor ___ está vindo visitar.', 'example', 8, 14, 1)
        ]

        sentence_ids = []
        for word_lemma, text, translation, sent_type, gap_start, gap_end, difficulty in sentences_data:
            sentence_id = uuid.uuid4()
            sentence_ids.append(sentence_id)
            cur.execute("""
                INSERT INTO sentence (id, text, translation, type, difficulty, gap_start, gap_end, word_id, language_id, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (sentence_id, text, translation, sent_type, difficulty, gap_start, gap_end, word_ids[word_lemma], en_lang_id, datetime.utcnow(), datetime.utcnow()))

        # Create demo deck
        deck_id = uuid.uuid4()
        cur.execute("""
            INSERT INTO deck (id, name, language_id, difficulty_level, description, card_count, is_active, created_at, updated_at)
            VALUES (%s, 'Everyday English', %s, 1, 'Common everyday vocabulary for beginners', 0, true, %s, %s)
        """, (deck_id, en_lang_id, datetime.utcnow(), datetime.utcnow()))

        # Grammar hints
        grammar_hints = {
            'book': 'É um objeto que você lê',
            'house': 'Lugar onde as pessoas moram',
            'water': 'Líquido essencial para a vida',
            'read': 'Ação de olhar texto',
            'write': 'Ação de registrar com caneta',
            'beautiful': 'Adjetivo para algo bonito',
            'quickly': 'Advérbio de velocidade',
            'friend': 'Pessoa próxima e querida'
        }

        # Create cards
        card_ids = []
        for i, (sentence_id, word_lemma) in enumerate(zip(sentence_ids, words_data)):
            card_id = uuid.uuid4()
            card_ids.append(card_id)
            cur.execute("""
                INSERT INTO card (id, sentence_id, deck_id, grammar_hint, difficulty, gap_start, gap_end, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, true, %s, %s)
            """, (card_id, sentence_id, deck_id, grammar_hints[word_lemma[0]], sentences_data[i][6], sentences_data[i][4], sentences_data[i][5], datetime.utcnow(), datetime.utcnow()))

        # Update deck card count
        cur.execute("UPDATE deck SET card_count = %s WHERE id = %s", (len(card_ids), deck_id))

        # Create demo user
        cur.execute("SELECT id FROM \"user\" WHERE username = 'demo' LIMIT 1")
        demo_user = cur.fetchone()
        if not demo_user:
            demo_user_id = uuid.uuid4()
            cur.execute("""
                INSERT INTO "user" (id, username, email, native_language, target_language, language_preference, daily_new_limit, easiness_factor, created_at, updated_at)
                VALUES (%s, 'demo', 'demo@filltheword.com', 'pt', 'en', 'en', 10, 2.5, %s, %s)
            """, (demo_user_id, datetime.utcnow(), datetime.utcnow()))
        else:
            demo_user_id = demo_user[0]

        # Create user card states
        for card_id in card_ids:
            cur.execute("""
                INSERT INTO usercardstate (id, user_id, card_id, repetitions, easiness_factor, interval_days, next_review_at, last_reviewed_at, status, total_reviews, correct_reviews, created_at, updated_at)
                VALUES (%s, %s, %s, 0, 2.5, 1, %s, NULL, 'new', 0, 0, %s, %s)
            """, (uuid.uuid4(), demo_user_id, card_id, datetime.utcnow(), datetime.utcnow(), datetime.utcnow()))

        conn.commit()

        print("\n🎉 Simple seed data creation completed successfully!")
        print(f"📊 Summary:")
        print(f"  - Languages: 1 (en)")
        print(f"  - Words: {len(words_data)}")
        print(f"  - Sentences: {len(sentences_data)}")
        print(f"  - Decks: 1")
        print(f"  - Cards: {len(card_ids)}")
        print(f"  - Demo User: 1")
        print(f"  - User Card States: {len(card_ids)}")

    except Exception as e:
        print(f"❌ Error during seed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()