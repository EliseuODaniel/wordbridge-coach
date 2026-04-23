#!/usr/bin/env python3
"""
Seed data script for French language support
Creates initial French words, sentences, and cards for WordBridge Coach
"""

import sys
import os
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Add the parent directory to the path to import app modules
sys.path.append('/app')

from app.core.database import SessionLocal
from app.models import (
    Language, Word, Sentence, Card, Deck, UserCardState, MemoryStage
)
from sqlalchemy import and_


def create_french_words(db: Session, fr_lang_id: str):
    """Create French vocabulary words with frequency ranks"""
    print("Creating French words...")

    # Common French words (top 50 with approximate frequency ranks)
    french_words = [
        # Top 10 most frequent
        ("le", 1), ("être", 2), ("et", 3), ("à", 4), ("les", 5),
        ("de", 6), ("un", 7), ("il", 8), ("pour", 9), ("que", 10),
        # Common verbs and nouns (11-30)
        ("avoir", 15), ("dans", 18), ("ce", 20), ("son", 22), ("une", 25),
        ("sur", 28), ("avec", 30), ("ne", 35), ("se", 40), ("pas", 45),
        ("tout", 50), ("pouvoir", 55), ("plus", 60), ("par", 65), ("grand", 70),
        ("mais", 75), ("me", 80), ("comme", 85), ("même", 90), ("bien", 95),
        # Additional vocabulary (31-50)
        ("voir", 100), ("sans", 110), ("très", 120), ("si", 130), ("donner", 140),
        ("leur", 150), ("nous", 160), ("devoir", 170), ("prendre", 180), ("savoir", 190),
        ("fin", 200), ("faire", 210), ("main", 220), ("jouer", 230), ("petit", 240),
        ("rien", 250), ("temps", 260), ("entre", 270), ("mon", 280), ("aller", 290),
    ]

    created_words = []
    for word_text, frequency_rank in french_words:
        existing_word = db.query(Word).filter(Word.text == word_text).first()
        if not existing_word:
            word = Word(
                id=str(uuid.uuid4()),
                lemma=word_text,  # Lemma is required, use text as lemma
                text=word_text,
                part_of_speech="noun",  # Default part of speech
                language_id=fr_lang_id,  # Link to French language
                frequency_rank=frequency_rank,
                difficulty=1,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(word)
            created_words.append(word)
            print(f"  Created word: {word_text} (rank: {frequency_rank})")

    db.commit()
    return created_words


def create_french_sentences(db: Session, fr_lang_id: str, words):
    """Create French sentences with gaps and Portuguese translations"""
    print("Creating French sentences...")

    # French sentence templates with Portuguese translations
    sentence_templates = [
        # Basic sentences
        {
            "template": "Il ___ fatigué.",
            "word_index": 0,  # First word in list
            "translation": "Ele está ___ cansado.",
            "gap_start": 3,
            "gap_end": 6,
            "grammar_hint": "Use the verb 'to be'"
        },
        {
            "template": "C'est une ___ maison.",
            "word_index": 1,
            "translation": "É uma casa ___.",
            "gap_start": 8,
            "gap_end": 12,
            "grammar_hint": "Use the adjective for 'big'"
        },
        {
            "template": "Je veux ___ maintenant.",
            "word_index": 2,
            "translation": "Eu quero ___ agora.",
            "gap_start": 8,
            "gap_end": 11,
            "grammar_hint": "Use the verb 'to go'"
        },
        {
            "template": "Elle ___ beaucoup de livres.",
            "word_index": 3,
            "translation": "Ela tem ___ de livros.",
            "gap_start": 5,
            "gap_end": 8,
            "grammar_hint": "Use the verb 'to have'"
        },
        {
            "template": "Le ___ est sur la table.",
            "word_index": 4,
            "translation": "O ___ está na mesa.",
            "gap_start": 3,
            "gap_end": 7,
            "grammar_hint": "Use the noun for a reading item"
        },
        {
            "template": "Nous allons au ___ aujourd'hui.",
            "word_index": 5,
            "translation": "Nós vamos ao ___ hoje.",
            "gap_start": 16,
            "gap_end": 19,
            "grammar_hint": "Use the noun for a place to buy things"
        },
        {
            "template": "Il ___ à l'école tous les jours.",
            "word_index": 6,
            "translation": "Ele vai à ___ todos os dias.",
            "gap_start": 3,
            "gap_end": 6,
            "grammar_hint": "Use the noun for educational institution"
        },
        {
            "template": "C'est un très ___ film.",
            "word_index": 7,
            "translation": "É um filme muito ___.",
            "gap_start": 13,
            "gap_end": 18,
            "grammar_hint": "Use the adjective for 'good'"
        },
        {
            "template": "Je ne sais pas ___ faire.",
            "word_index": 8,
            "translation": "Eu não sei ___ fazer.",
            "gap_start": 14,
            "gap_end": 17,
            "grammar_hint": "Use the phrase for 'what to'"
        },
        {
            "template": "Elle ___ une belle robe.",
            "word_index": 9,
            "translation": "Ela ___ um vestido bonito.",
            "gap_start": 5,
            "gap_end": 8,
            "grammar_hint": "Use the verb 'to wear' or 'to have'"
        },
        # More complex sentences
        {
            "template": "___ beaucoup de temps pour finir.",
            "word_index": 10,
            "translation": "___ muito tempo para terminar.",
            "gap_start": 0,
            "gap_end": 5,
            "grammar_hint": "Use 'It takes'"
        },
        {
            "template": "Le ___ du soleil est chaud.",
            "word_index": 11,
            "translation": "O ___ do sol é quente.",
            "gap_start": 3,
            "gap_end": 6,
            "grammar_hint": "Use 'heat' or 'temperature'"
        },
        {
            "template": "Je peux ___ avec toi.",
            "word_index": 12,
            "translation": "Eu posso ___ com você.",
            "gap_start": 8,
            "gap_end": 12,
            "grammar_hint": "Use the verb 'to come'"
        },
        {
            "template": "Elle ___ ses devoirs ce soir.",
            "word_index": 13,
            "translation": "Ela ___ seus deveres esta noite.",
            "gap_start": 5,
            "gap_end": 8,
            "grammar_hint": "Use the verb 'to do'"
        },
        {
            "template": "C'est un ___ d'ordinateur.",
            "word_index": 14,
            "translation": "É um ___ de computador.",
            "gap_start": 8,
            "gap_end": 11,
            "grammar_hint": "Use 'game' or 'program'"
        },
        {
            "template": "Le ___ est fermé aujourd'hui.",
            "word_index": 15,
            "translation": "O ___ está fechado hoje.",
            "gap_start": 3,
            "gap_end": 7,
            "grammar_hint": "Use 'store' or 'shop'"
        },
        {
            "template": "Je ___ le français depuis longtemps.",
            "word_index": 16,
            "translation": "Eu ___ francês há muito tempo.",
            "gap_start": 3,
            "gap_end": 7,
            "grammar_hint": "Use the verb 'to speak'"
        },
        {
            "template": "___ est une belle journée.",
            "word_index": 17,
            "translation": "___ é um belo dia.",
            "gap_start": 0,
            "gap_end": 2,
            "grammar_hint": "Use 'Today' or 'This'"
        },
        {
            "template": "Les ___ sont dans le jardin.",
            "word_index": 18,
            "translation": "Os ___ estão no jardim.",
            "gap_start": 4,
            "gap_end": 10,
            "grammar_hint": "Use 'children' or 'kids'"
        },
        {
            "template": "J'ai besoin d'un ___ pour écrire.",
            "word_index": 19,
            "translation": "Preciso de um ___ para escrever.",
            "gap_start": 16,
            "gap_end": 20,
            "grammar_hint": "Use the writing instrument"
        }
    ]

    created_sentences = []
    for i, template in enumerate(sentence_templates):
        if template["word_index"] < len(words):
            word = words[template["word_index"]]

            # Replace the target word in template
            sentence_text = template["template"].replace("___", word.text)

            # Check if sentence already exists
            existing_sentence = db.query(Sentence).filter(
                and_(
                    Sentence.text == sentence_text,
                    Sentence.language_id == fr_lang_id
                )
            ).first()

            if not existing_sentence:
                sentence = Sentence(
                    id=str(uuid.uuid4()),
                    text=sentence_text,
                    translation=template["translation"],
                    word_id=word.id,
                    language_id=fr_lang_id,
                    type="fill_gap",
                    difficulty=1,
                    gap_start=template["gap_start"],
                    gap_end=template["gap_end"],
                    created_at=datetime.utcnow()
                )
                db.add(sentence)
                created_sentences.append(sentence)
                print(f"  Created sentence: {sentence_text}")

    db.commit()
    return created_sentences


def create_french_cards(db: Session, sentences):
    """Create cards for French sentences"""
    print("Creating French cards...")

    # Use existing deck for French cards
    # Get the first available deck (simplified approach for MVP)
    existing_deck = db.query(Deck).first()
    if not existing_deck:
        print("❌ No decks found. Please run main seed first.")
        return []

    created_cards = []
    for sentence in sentences:
        # Check if card already exists for this sentence
        existing_card = db.query(Card).filter(Card.sentence_id == sentence.id).first()
        if not existing_card:
            card = Card(
                id=str(uuid.uuid4()),
                sentence_id=sentence.id,
                deck_id=existing_deck.id,  # Use existing deck
                grammar_hint="Use the correct word",
                difficulty=1,
                position=1,
                gap_start=sentence.gap_start,
                gap_end=sentence.gap_end,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(card)
            created_cards.append(card)
            print(f"  Created card for sentence: {sentence.text[:30]}...")

    db.commit()
    return created_cards


def main():
    """Main function to seed French data"""
    print("🇫🇷 Starting French data seeding...")

    db = SessionLocal()
    try:
        # Get French language
        fr_lang = db.query(Language).filter(Language.code == 'fr').first()
        if not fr_lang:
            print("❌ French language not found. Please run main seed first.")
            return

        print(f"✅ Found French language: {fr_lang.name}")

        # Create words
        words = create_french_words(db, fr_lang.id)
        print(f"✅ Created {len(words)} French words")

        # Create sentences
        sentences = create_french_sentences(db, fr_lang.id, words)
        print(f"✅ Created {len(sentences)} French sentences")

        # Create cards
        cards = create_french_cards(db, sentences)
        print(f"✅ Created {len(cards)} French cards")

        print("🎉 French data seeding completed successfully!")

    except Exception as e:
        print(f"❌ Error seeding French data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
