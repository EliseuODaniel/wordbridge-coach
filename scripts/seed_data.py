#!/usr/bin/env python3
"""
Seed data script for FillTheWord MVP
Creates initial vocabulary, sentences, and cards for testing
"""

import sys
import os
import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path to import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_seed_data():
    """Create initial seed data for FillTheWord MVP"""
    
    # Database connection
    database_url = os.getenv("DATABASE_URL", "sqlite:///./filltheword.db")
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)
    
    # Create session
    db = SessionLocal()
    
    try:
        print("🌱 Creating seed data for FillTheWord MVP...")
        
        # Check if data already exists
        from app.models import Language, Word, Sentence, Card, Deck, User, UserCardState
        
        # Create languages if they don't exist
        print("Creating languages...")
        languages = []
        language_data = [
            {"code": "en", "name": "English", "voice_model": "lessac-glow_tts", "voice_type": "female"},
            {"code": "pt", "name": "Português", "voice_model": "pt_br_female-glow_tts", "voice_type": "female"},
            {"code": "es", "name": "Español", "voice_model": "es_male-glow_tts", "voice_type": "male"},
        ]
        
        for lang_data in language_data:
            existing_lang = db.query(Language).filter(Language.code == lang_data["code"]).first()
            if not existing_lang:
                language = Language(
                    id=uuid.uuid4(),
                    **lang_data,
                    is_active=True
                )
                db.add(language)
                languages.append(language)
                print(f"  Created language: {lang_data['name']}")
            else:
                languages.append(existing_lang)
                print(f"  Language already exists: {lang_data['name']}")
        
        # Get English language for creating content
        en_lang = next((lang for lang in languages if lang.code == "en"), None)
        if not en_lang:
            raise Exception("English language not found")
        
        db.commit()
        
        # Create decks
        print("Creating decks...")
        decks = []
        deck_data = [
            {"name": "Daily English", "difficulty_level": 1, "description": "Common everyday vocabulary"},
            {"name": "Common Objects", "difficulty_level": 1, "description": "Objects you see every day"},
            {"name": "Actions & Verbs", "difficulty_level": 2, "description": "Common actions and verbs"},
        ]
        
        for deck_info in deck_data:
            existing_deck = db.query(Deck).filter(Deck.name == deck_info["name"]).first()
            if not existing_deck:
                deck = Deck(
                    id=uuid.uuid4(),
                    language_id=en_lang.id,
                    **deck_info,
                    is_active=True
                )
                db.add(deck)
                decks.append(deck)
                print(f"  Created deck: {deck_info['name']}")
            else:
                decks.append(existing_deck)
                print(f"  Deck already exists: {deck_info['name']}")
        
        db.commit()
        
        # Create vocabulary words
        print("Creating vocabulary words...")
        vocabulary_data = [
            # Level 1 - Very common
            {"lemma": "book", "text": "book", "part_of_speech": "noun", "difficulty": 1, "frequency_rank": 1},
            {"lemma": "cat", "text": "cat", "part_of_speech": "noun", "difficulty": 1, "frequency_rank": 2},
            {"lemma": "house", "text": "house", "part_of_speech": "noun", "difficulty": 1, "frequency_rank": 3},
            {"lemma": "water", "text": "water", "part_of_speech": "noun", "difficulty": 1, "frequency_rank": 4},
            {"lemma": "food", "text": "food", "part_of_speech": "noun", "difficulty": 1, "frequency_rank": 5},
            {"lemma": "table", "text": "table", "part_of_speech": "noun", "difficulty": 1, "frequency_rank": 6},
            {"lemma": "chair", "text": "chair", "part_of_speech": "noun", "difficulty": 1, "frequency_rank": 7},
            {"lemma": "dog", "text": "dog", "part_of_speech": "noun", "difficulty": 1, "frequency_rank": 8},
            {"lemma": "car", "text": "car", "part_of_speech": "noun", "difficulty": 1, "frequency_rank": 9},
            {"lemma": "tree", "text": "tree", "part_of_speech": "noun", "difficulty": 1, "frequency_rank": 10},
            
            # Level 2 - Common
            {"lemma": "beautiful", "text": "beautiful", "part_of_speech": "adjective", "difficulty": 2, "frequency_rank": 11},
            {"lemma": "important", "text": "important", "part_of_speech": "adjective", "difficulty": 2, "frequency_rank": 12},
            {"lemma": "different", "text": "different", "part_of_speech": "adjective", "difficulty": 2, "frequency_rank": 13},
            {"lemma": "read", "text": "read", "part_of_speech": "verb", "difficulty": 2, "frequency_rank": 14},
            {"lemma": "write", "text": "write", "part_of_speech": "verb", "difficulty": 2, "frequency_rank": 15},
            {"lemma": "study", "text": "study", "part_of_speech": "verb", "difficulty": 2, "frequency_rank": 16},
            
            # Level 3 - Less common
            {"lemma": "necessary", "text": "necessary", "part_of_speech": "adjective", "difficulty": 3, "frequency_rank": 17},
            {"lemma": "delicious", "text": "delicious", "part_of_speech": "adjective", "difficulty": 3, "frequency_rank": 18},
            {"lemma": "expensive", "text": "expensive", "part_of_speech": "adjective", "difficulty": 3, "frequency_rank": 19},
            {"lemma": "understand", "text": "understand", "part_of_speech": "verb", "difficulty": 3, "frequency_rank": 20},
        ]
        
        words = []
        for word_info in vocabulary_data:
            existing_word = db.query(Word).filter(Word.text == word_info["text"]).first()
            if not existing_word:
                word = Word(
                    id=uuid.uuid4(),
                    language_id=en_lang.id,
                    pronunciation=f"/{word_info['text']}/",  # Mock IPA
                    **word_info
                )
                db.add(word)
                words.append(word)
                print(f"  Created word: {word_info['text']}")
            else:
                words.append(existing_word)
                print(f"  Word already exists: {word_info['text']}")
        
        db.commit()
        
        # Create sentences and cards
        print("Creating sentences and cards...")
        sentences_data = [
            # Book sentences
            {"word": "book", "text": "The ___ is on the table.", "translation": "O livro está na mesa.", "grammar_hint": "É um objeto que você lê", "difficulty": 1},
            {"word": "book", "text": "I am reading an interesting ___.", "translation": "Estou lendo um livro interessante.", "grammar_hint": "Pode ser interesting ou boring", "difficulty": 2},
            {"word": "book", "text": "She borrowed a ___ from the library.", "translation": "Ela pegou um livro emprestado da biblioteca.", "grammar_hint": "Normalmente se empresta de library", "difficulty": 2},
            
            # Cat sentences
            {"word": "cat", "text": "A ___ sleeps in the garden.", "translation": "Um gato dorme no jardim.", "grammar_hint": "É um animal de estimação que mia", "difficulty": 1},
            {"word": "cat", "text": "The ___ is chasing a mouse.", "translation": "O gato está perseguindo um mouse.", "grammar_hint": "Animal que caça ratos", "difficulty": 2},
            {"word": "cat", "text": "My ___ is very playful.", "translation": "Meu gato é muito brincalhão.", "grammar_hint": "Animal de estimação comum", "difficulty": 1},
            
            # House sentences
            {"word": "house", "text": "They live in a big ___.", "translation": "Eles vivem em uma casa grande.", "grammar_hint": "Lugar onde as pessoas moram", "difficulty": 1},
            {"word": "house", "text": "The ___ has a beautiful garden.", "translation": "A casa tem um jardim bonito.", "grammar_hint": "Edifício residencial", "difficulty": 2},
            {"word": "house", "text": "I want to buy a new ___.", "translation": "Eu quero comprar uma casa nova.", "grammar_hint": "Imóvel para morar", "difficulty": 1},
            
            # Water sentences
            {"word": "water", "text": "I need a glass of ___.", "translation": "Preciso de um copo de água.", "grammar_hint": "Líquido essencial para a vida", "difficulty": 1},
            {"word": "water", "text": "The plants need more ___.", "translation": "As plantas precisam de mais água.", "grammar_hint": "Líquido para regar plantas", "difficulty": 1},
            {"word": "water", "text": "She drinks ___ every morning.", "translation": "Ela bebe água toda manhã.", "grammar_hint": "Líquido transparente", "difficulty": 1},
            
            # Table sentences
            {"word": "table", "text": "The food is on the ___.", "translation": "A comida está na mesa.", "grammar_hint": "Móvel para refeições", "difficulty": 1},
            {"word": "table", "text": "We sat around the dinner ___.", "translation": "Sentamos ao redor da mesa de jantar.", "grammar_hint": "Móvel com cadeiras ao redor", "difficulty": 2},
            {"word": "table", "text": "The book is on the ___.", "translation": "O livro está na mesa.", "grammar_hint": "Móvel plano e elevado", "difficulty": 1},
        ]
        
        cards_created = 0
        for sentence_info in sentences_data:
            # Find the word
            target_word = next((w for w in words if w.text == sentence_info["word"]), None)
            if not target_word:
                print(f"  Warning: Word '{sentence_info['word']}' not found, skipping sentence")
                continue
            
            # Create sentence with gap
            gap_start = sentence_info["text"].index("___")
            gap_end = gap_start + 3  # "___" has 3 characters
            
            sentence = Sentence(
                id=uuid.uuid4(),
                text=sentence_info["text"],
                translation=sentence_info["translation"],
                word_id=target_word.id,
                language_id=en_lang.id,
                type="example",
                difficulty=sentence_info["difficulty"],
                gap_start=gap_start,
                gap_end=gap_end
            )
            db.add(sentence)
            
            # Create card
            deck = decks[0]  # Use first deck (Daily English)
            card = Card(
                id=uuid.uuid4(),
                sentence_id=sentence.id,
                deck_id=deck.id,
                grammar_hint=sentence_info["grammar_hint"],
                difficulty=sentence_info["difficulty"],
                gap_start=gap_start,
                gap_end=gap_end,
                is_active=True
            )
            db.add(card)
            cards_created += 1
            
            print(f"  Created card: {sentence_info['text']}")
        
        db.commit()
        
        # Create demo user
        print("Creating demo user...")
        existing_user = db.query(User).filter(User.username == "demo").first()
        if not existing_user:
            demo_user = User(
                id=uuid.uuid4(),
                username="demo",
                email="demo@filltheword.com",
                native_language="pt",
                target_language="en",
                language_preference="en",
                daily_new_limit=10,
                easiness_factor=2.5
            )
            db.add(demo_user)
            print("  Created demo user")
        else:
            demo_user = existing_user
            print("  Demo user already exists")
        
        db.commit()
        
        # Create user card states for demo user
        print("Creating user card states for demo user...")
        all_cards = db.query(Card).filter(Card.is_active == True).all()
        
        for card in all_cards:
            existing_state = db.query(UserCardState).filter(
                UserCardState.user_id == demo_user.id,
                UserCardState.card_id == card.id
            ).first()
            
            if not existing_state:
                # Create card state with varied initial stages
                import random
                initial_stages = ["new", "learning", "review"]
                stage = random.choice(initial_stages)
                
                if stage == "new":
                    repetitions = 0
                    interval_days = 1
                    next_review = datetime.utcnow() + timedelta(days=1)
                elif stage == "learning":
                    repetitions = random.randint(1, 2)
                    interval_days = random.randint(1, 6)
                    next_review = datetime.utcnow() + timedelta(days=interval_days)
                else:  # review
                    repetitions = random.randint(3, 5)
                    interval_days = random.randint(7, 21)
                    next_review = datetime.utcnow() + timedelta(days=interval_days)
                
                user_card_state = UserCardState(
                    id=uuid.uuid4(),
                    user_id=demo_user.id,
                    card_id=card.id,
                    repetitions=repetitions,
                    easiness_factor=2.5,
                    interval_days=interval_days,
                    next_review_at=next_review,
                    last_reviewed_at=datetime.utcnow() - timedelta(days=1),
                    status=stage,
                    total_reviews=repetitions,
                    correct_reviews=max(0, repetitions - 1)
                )
                db.add(user_card_state)
        
        db.commit()
        
        print(f"✅ Seed data created successfully!")
        print(f"   - Languages: {len(languages)}")
        print(f"   - Decks: {len(decks)}")
        print(f"   - Words: {len(words)}")
        print(f"   - Cards: {cards_created}")
        print(f"   - Demo user: {demo_user.username}")
        print()
        print("🚀 FillTheWord MVP is ready to use!")
        print("   Frontend: http://localhost:3000")
        print("   API Docs: http://localhost:8000/docs")
        print("   TTS API: http://localhost:8001/docs")
        
    except Exception as e:
        print(f"❌ Error creating seed data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_seed_data()
