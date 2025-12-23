#!/usr/bin/env python3
"""
Seed data script for FillTheWord MVP
Creates initial languages, words, sentences, cards, and demo user with proper UUIDs
"""

import sys
import os
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Add the parent directory to the path to import app modules
sys.path.append('/app')

from app.core.database import SessionLocal
# Import ALL models to ensure proper SQLAlchemy mapping
from app.models import (
    Language, Word, Sentence, Card, Deck, User, UserCardState, ReviewEvent
)
from app.models.user_card_state import MemoryStage


def create_languages(db: Session):
    """Create language entries"""
    print("Creating languages...")

    languages = [
        {
            'code': 'en',
            'name': 'English',
            'voice_model': 'lessac-glow_tts',
            'voice_type': 'female',
            'is_active': True
        },
        {
            'code': 'pt',
            'name': 'Portuguese',
            'voice_model': 'tugm-glow_tts',
            'voice_type': 'female',
            'is_active': True
        },
        {
            'code': 'es',
            'name': 'Spanish',
            'voice_model': 'carlfm-glow_tts',
            'voice_type': 'male',
            'is_active': True
        },
        {
            'code': 'fr',
            'name': 'French',
            'voice_model': 'fr_female-glow_tts',
            'voice_type': 'female',
            'is_active': True
        }
    ]

    lang_ids = {}
    for lang_data in languages:
        # Check if language already exists
        existing_lang = db.query(Language).filter(Language.code == lang_data['code']).first()
        if existing_lang:
            lang_ids[lang_data['code']] = existing_lang.id
            print(f"Language {lang_data['code']} already exists, using existing ID")
        else:
            language = Language(
                id=uuid.uuid4(),
                **lang_data
            )
            db.add(language)
            db.commit()
            lang_ids[lang_data['code']] = language.id
            print(f"Created language {lang_data['code']}")

    print(f"Processed {len(languages)} languages")
    return lang_ids


def create_words(db: Session, lang_ids: dict):
    """Create vocabulary words"""
    print("Creating words...")

    # Expanded English vocabulary for MVP (100+ words)
    words_data = [
        {
            'lemma': 'book',
            'text': 'book',
            'part_of_speech': 'noun',
            'pronunciation': '/bʊk/',
            'frequency_rank': 100,
            'difficulty': 1,
            'features': {'plural': 'books', 'category': 'object', 'pt_translation': 'livro'}
        },
        {
            'lemma': 'house',
            'text': 'house',
            'part_of_speech': 'noun',
            'pronunciation': '/haʊs/',
            'frequency_rank': 200,
            'difficulty': 1,
            'features': {'plural': 'houses', 'category': 'object', 'pt_translation': 'casa'}
        },
        {
            'lemma': 'water',
            'text': 'water',
            'part_of_speech': 'noun',
            'pronunciation': '/ˈwɔːtər/',
            'frequency_rank': 50,
            'difficulty': 1,
            'features': {'category': 'liquid', 'uncountable': True, 'pt_translation': 'água'}
        },
        {
            'lemma': 'read',
            'text': 'read',
            'part_of_speech': 'verb',
            'pronunciation': '/riːd/',
            'frequency_rank': 150,
            'difficulty': 1,
            'features': {'tenses': ['reads', 'reading', 'read'], 'category': 'action'}
        },
        {
            'lemma': 'write',
            'text': 'write',
            'part_of_speech': 'verb',
            'pronunciation': '/raɪt/',
            'frequency_rank': 180,
            'difficulty': 1,
            'features': {'tenses': ['writes', 'writing', 'wrote', 'written'], 'category': 'action'}
        },
        {
            'lemma': 'beautiful',
            'text': 'beautiful',
            'part_of_speech': 'adjective',
            'pronunciation': '/ˈbjuːtɪfəl/',
            'frequency_rank': 500,
            'difficulty': 2,
            'features': {'comparative': 'more beautiful', 'superlative': 'most beautiful'}
        },
        {
            'lemma': 'quickly',
            'text': 'quickly',
            'part_of_speech': 'adverb',
            'pronunciation': '/ˈkwɪkli/',
            'frequency_rank': 300,
            'difficulty': 2,
            'features': {'base_form': 'quick'}
        },
        {
            'lemma': 'friend',
            'text': 'friend',
            'part_of_speech': 'noun',
            'pronunciation': '/frɛnd/',
            'frequency_rank': 250,
            'difficulty': 1,
            'features': {'plural': 'friends', 'category': 'person'}
        },
        # Common nouns (20 more)
        {
            'lemma': 'cat',
            'text': 'cat',
            'part_of_speech': 'noun',
            'pronunciation': '/kæt/',
            'frequency_rank': 300,
            'difficulty': 1,
            'features': {'plural': 'cats', 'category': 'animal'}
        },
        {
            'lemma': 'dog',
            'text': 'dog',
            'part_of_speech': 'noun',
            'pronunciation': '/dɔɡ/',
            'frequency_rank': 280,
            'difficulty': 1,
            'features': {'plural': 'dogs', 'category': 'animal'}
        },
        {
            'lemma': 'car',
            'text': 'car',
            'part_of_speech': 'noun',
            'pronunciation': '/kɑr/',
            'frequency_rank': 200,
            'difficulty': 1,
            'features': {'plural': 'cars', 'category': 'vehicle'}
        },
        {
            'lemma': 'table',
            'text': 'table',
            'part_of_speech': 'noun',
            'pronunciation': '/ˈteɪbəl/',
            'frequency_rank': 320,
            'difficulty': 1,
            'features': {'plural': 'tables', 'category': 'furniture'}
        },
        {
            'lemma': 'chair',
            'text': 'chair',
            'part_of_speech': 'noun',
            'pronunciation': '/tʃɛr/',
            'frequency_rank': 350,
            'difficulty': 1,
            'features': {'plural': 'chairs', 'category': 'furniture'}
        },
        {
            'lemma': 'door',
            'text': 'door',
            'part_of_speech': 'noun',
            'pronunciation': '/dɔr/',
            'frequency_rank': 260,
            'difficulty': 1,
            'features': {'plural': 'doors', 'category': 'object'}
        },
        {
            'lemma': 'window',
            'text': 'window',
            'part_of_speech': 'noun',
            'pronunciation': '/ˈwɪndoʊ/',
            'frequency_rank': 380,
            'difficulty': 1,
            'features': {'plural': 'windows', 'category': 'object'}
        },
        {
            'lemma': 'food',
            'text': 'food',
            'part_of_speech': 'noun',
            'pronunciation': '/fuːd/',
            'frequency_rank': 120,
            'difficulty': 1,
            'features': {'category': 'consumable', 'uncountable': True}
        },
        {
            'lemma': 'apple',
            'text': 'apple',
            'part_of_speech': 'noun',
            'pronunciation': '/ˈæpəl/',
            'frequency_rank': 400,
            'difficulty': 1,
            'features': {'plural': 'apples', 'category': 'fruit'}
        },
        {
            'lemma': 'banana',
            'text': 'banana',
            'part_of_speech': 'noun',
            'pronunciation': '/bəˈnænə/',
            'frequency_rank': 420,
            'difficulty': 1,
            'features': {'plural': 'bananas', 'category': 'fruit'}
        },
        {
            'lemma': 'coffee',
            'text': 'coffee',
            'part_of_speech': 'noun',
            'pronunciation': '/ˈkɔfi/',
            'frequency_rank': 160,
            'difficulty': 1,
            'features': {'category': 'drink', 'uncountable': True}
        },
        {
            'lemma': 'tea',
            'text': 'tea',
            'part_of_speech': 'noun',
            'pronunciation': '/tiː/',
            'frequency_rank': 170,
            'difficulty': 1,
            'features': {'category': 'drink', 'uncountable': True}
        },
        {
            'lemma': 'bread',
            'text': 'bread',
            'part_of_speech': 'noun',
            'pronunciation': '/brɛd/',
            'frequency_rank': 180,
            'difficulty': 1,
            'features': {'category': 'food', 'uncountable': True}
        },
        {
            'lemma': 'milk',
            'text': 'milk',
            'part_of_speech': 'noun',
            'pronunciation': '/mɪlk/',
            'frequency_rank': 140,
            'difficulty': 1,
            'features': {'category': 'drink', 'uncountable': True}
        },
        {
            'lemma': 'phone',
            'text': 'phone',
            'part_of_speech': 'noun',
            'pronunciation': '/foʊn/',
            'frequency_rank': 190,
            'difficulty': 1,
            'features': {'plural': 'phones', 'category': 'technology'}
        },
        {
            'lemma': 'computer',
            'text': 'computer',
            'part_of_speech': 'noun',
            'pronunciation': '/kəmˈpjuːtər/',
            'frequency_rank': 220,
            'difficulty': 1,
            'features': {'plural': 'computers', 'category': 'technology'}
        },
        {
            'lemma': 'school',
            'text': 'school',
            'part_of_speech': 'noun',
            'pronunciation': '/skuːl/',
            'frequency_rank': 210,
            'difficulty': 1,
            'features': {'plural': 'schools', 'category': 'place'}
        },
        {
            'lemma': 'teacher',
            'text': 'teacher',
            'part_of_speech': 'noun',
            'pronunciation': '/ˈtiːtʃər/',
            'frequency_rank': 270,
            'difficulty': 1,
            'features': {'plural': 'teachers', 'category': 'person'}
        },
        {
            'lemma': 'student',
            'text': 'student',
            'part_of_speech': 'noun',
            'pronunciation': '/ˈstuːdənt/',
            'frequency_rank': 230,
            'difficulty': 1,
            'features': {'plural': 'students', 'category': 'person'}
        },
        {
            'lemma': 'family',
            'text': 'family',
            'part_of_speech': 'noun',
            'pronunciation': '/ˈfæməli/',
            'frequency_rank': 130,
            'difficulty': 1,
            'features': {'plural': 'families', 'category': 'group'}
        },
        # Common verbs (15 more)
        {
            'lemma': 'eat',
            'text': 'eat',
            'part_of_speech': 'verb',
            'pronunciation': '/iːt/',
            'frequency_rank': 90,
            'difficulty': 1,
            'features': {'tenses': ['eats', 'eating', 'ate', 'eaten'], 'category': 'action'}
        },
        {
            'lemma': 'drink',
            'text': 'drink',
            'part_of_speech': 'verb',
            'pronunciation': '/drɪŋk/',
            'frequency_rank': 110,
            'difficulty': 1,
            'features': {'tenses': ['drinks', 'drinking', 'drank', 'drunk'], 'category': 'action'}
        },
        {
            'lemma': 'sleep',
            'text': 'sleep',
            'part_of_speech': 'verb',
            'pronunciation': '/sliːp/',
            'frequency_rank': 240,
            'difficulty': 1,
            'features': {'tenses': ['sleeps', 'sleeping', 'slept'], 'category': 'action'}
        },
        {
            'lemma': 'work',
            'text': 'work',
            'part_of_speech': 'verb',
            'pronunciation': '/wɜrk/',
            'frequency_rank': 70,
            'difficulty': 1,
            'features': {'tenses': ['works', 'working', 'worked'], 'category': 'action'}
        },
        {
            'lemma': 'play',
            'text': 'play',
            'part_of_speech': 'verb',
            'pronunciation': '/pleɪ/',
            'frequency_rank': 80,
            'difficulty': 1,
            'features': {'tenses': ['plays', 'playing', 'played'], 'category': 'action'}
        },
        {
            'lemma': 'go',
            'text': 'go',
            'part_of_speech': 'verb',
            'pronunciation': '/ɡoʊ/',
            'frequency_rank': 40,
            'difficulty': 1,
            'features': {'tenses': ['goes', 'going', 'went', 'gone'], 'category': 'action'}
        },
        {
            'lemma': 'come',
            'text': 'come',
            'part_of_speech': 'verb',
            'pronunciation': '/kʌm/',
            'frequency_rank': 60,
            'difficulty': 1,
            'features': {'tenses': ['comes', 'coming', 'came'], 'category': 'action'}
        },
        {
            'lemma': 'see',
            'text': 'see',
            'part_of_speech': 'verb',
            'pronunciation': '/siː/',
            'frequency_rank': 50,
            'difficulty': 1,
            'features': {'tenses': ['sees', 'seeing', 'saw', 'seen'], 'category': 'action'}
        },
        {
            'lemma': 'hear',
            'text': 'hear',
            'part_of_speech': 'verb',
            'pronunciation': '/hɪr/',
            'frequency_rank': 310,
            'difficulty': 1,
            'features': {'tenses': ['hears', 'hearing', 'heard'], 'category': 'action'}
        },
        {
            'lemma': 'speak',
            'text': 'speak',
            'part_of_speech': 'verb',
            'pronunciation': '/spiːk/',
            'frequency_rank': 290,
            'difficulty': 1,
            'features': {'tenses': ['speaks', 'speaking', 'spoke', 'spoken'], 'category': 'action'}
        },
        {
            'lemma': 'walk',
            'text': 'walk',
            'part_of_speech': 'verb',
            'pronunciation': '/wɔk/',
            'frequency_rank': 330,
            'difficulty': 1,
            'features': {'tenses': ['walks', 'walking', 'walked'], 'category': 'action'}
        },
        {
            'lemma': 'run',
            'text': 'run',
            'part_of_speech': 'verb',
            'pronunciation': '/rʌn/',
            'frequency_rank': 340,
            'difficulty': 1,
            'features': {'tenses': ['runs', 'running', 'ran'], 'category': 'action'}
        },
        {
            'lemma': 'sit',
            'text': 'sit',
            'part_of_speech': 'verb',
            'pronunciation': '/sɪt/',
            'frequency_rank': 360,
            'difficulty': 1,
            'features': {'tenses': ['sits', 'sitting', 'sat'], 'category': 'action'}
        },
        {
            'lemma': 'stand',
            'text': 'stand',
            'part_of_speech': 'verb',
            'pronunciation': '/stænd/',
            'frequency_rank': 370,
            'difficulty': 1,
            'features': {'tenses': ['stands', 'standing', 'stood'], 'category': 'action'}
        },
        {
            'lemma': 'open',
            'text': 'open',
            'part_of_speech': 'verb',
            'pronunciation': '/ˈoʊpən/',
            'frequency_rank': 390,
            'difficulty': 1,
            'features': {'tenses': ['opens', 'opening', 'opened'], 'category': 'action'}
        },
        # Common adjectives (15 more)
        {
            'lemma': 'big',
            'text': 'big',
            'part_of_speech': 'adjective',
            'pronunciation': '/bɪɡ/',
            'frequency_rank': 160,
            'difficulty': 1,
            'features': {'comparative': 'bigger', 'superlative': 'biggest'}
        },
        {
            'lemma': 'small',
            'text': 'small',
            'part_of_speech': 'adjective',
            'pronunciation': '/smɔl/',
            'frequency_rank': 190,
            'difficulty': 1,
            'features': {'comparative': 'smaller', 'superlative': 'smallest'}
        },
        {
            'lemma': 'good',
            'text': 'good',
            'part_of_speech': 'adjective',
            'pronunciation': '/ɡʊd/',
            'frequency_rank': 30,
            'difficulty': 1,
            'features': {'comparative': 'better', 'superlative': 'best'}
        },
        {
            'lemma': 'bad',
            'text': 'bad',
            'part_of_speech': 'adjective',
            'pronunciation': '/bæd/',
            'frequency_rank': 100,
            'difficulty': 1,
            'features': {'comparative': 'worse', 'superlative': 'worst'}
        },
        {
            'lemma': 'hot',
            'text': 'hot',
            'part_of_speech': 'adjective',
            'pronunciation': '/hɑt/',
            'frequency_rank': 410,
            'difficulty': 1,
            'features': {'comparative': 'hotter', 'superlative': 'hottest'}
        },
        {
            'lemma': 'cold',
            'text': 'cold',
            'part_of_speech': 'adjective',
            'pronunciation': '/koʊld/',
            'frequency_rank': 430,
            'difficulty': 1,
            'features': {'comparative': 'colder', 'superlative': 'coldest'}
        },
        {
            'lemma': 'new',
            'text': 'new',
            'part_of_speech': 'adjective',
            'pronunciation': '/nuː/',
            'frequency_rank': 85,
            'difficulty': 1,
            'features': {'comparative': 'newer', 'superlative': 'newest'}
        },
        {
            'lemma': 'old',
            'text': 'old',
            'part_of_speech': 'adjective',
            'pronunciation': '/oʊld/',
            'frequency_rank': 95,
            'difficulty': 1,
            'features': {'comparative': 'older', 'superlative': 'oldest'}
        },
        {
            'lemma': 'happy',
            'text': 'happy',
            'part_of_speech': 'adjective',
            'pronunciation': '/ˈhæpi/',
            'frequency_rank': 440,
            'difficulty': 1,
            'features': {'comparative': 'happier', 'superlative': 'happiest'}
        },
        {
            'lemma': 'sad',
            'text': 'sad',
            'part_of_speech': 'adjective',
            'pronunciation': '/sæd/',
            'frequency_rank': 450,
            'difficulty': 1,
            'features': {'comparative': 'sadder', 'superlative': 'saddest'}
        },
        {
            'lemma': 'easy',
            'text': 'easy',
            'part_of_speech': 'adjective',
            'pronunciation': '/ˈiːzi/',
            'frequency_rank': 460,
            'difficulty': 1,
            'features': {'comparative': 'easier', 'superlative': 'easiest'}
        },
        {
            'lemma': 'hard',
            'text': 'hard',
            'part_of_speech': 'adjective',
            'pronunciation': '/hɑrd/',
            'frequency_rank': 470,
            'difficulty': 1,
            'features': {'comparative': 'harder', 'superlative': 'hardest'}
        },
        {
            'lemma': 'clean',
            'text': 'clean',
            'part_of_speech': 'adjective',
            'pronunciation': '/kliːn/',
            'frequency_rank': 480,
            'difficulty': 1,
            'features': {'comparative': 'cleaner', 'superlative': 'cleanest'}
        },
        {
            'lemma': 'dirty',
            'text': 'dirty',
            'part_of_speech': 'adjective',
            'pronunciation': '/ˈdɜrti/',
            'frequency_rank': 490,
            'difficulty': 1,
            'features': {'comparative': 'dirtier', 'superlative': 'dirtiest'}
        },
        {
            'lemma': 'young',
            'text': 'young',
            'part_of_speech': 'adjective',
            'pronunciation': '/jʌŋ/',
            'frequency_rank': 300,
            'difficulty': 1,
            'features': {'comparative': 'younger', 'superlative': 'youngest'}
        },
        # Adverbs (10 more)
        {
            'lemma': 'slowly',
            'text': 'slowly',
            'part_of_speech': 'adverb',
            'pronunciation': '/ˈsloʊli/',
            'frequency_rank': 410,
            'difficulty': 2,
            'features': {'base_form': 'slow'}
        },
        {
            'lemma': 'carefully',
            'text': 'carefully',
            'part_of_speech': 'adverb',
            'pronunciation': '/ˈkɛrfəli/',
            'frequency_rank': 420,
            'difficulty': 2,
            'features': {'base_form': 'careful'}
        },
        {
            'lemma': 'always',
            'text': 'always',
            'part_of_speech': 'adverb',
            'pronunciation': '/ˈɔlweɪz/',
            'frequency_rank': 260,
            'difficulty': 1,
            'features': {}
        },
        {
            'lemma': 'never',
            'text': 'never',
            'part_of_speech': 'adverb',
            'pronunciation': '/ˈnɛvər/',
            'frequency_rank': 270,
            'difficulty': 1,
            'features': {}
        },
        {
            'lemma': 'sometimes',
            'text': 'sometimes',
            'part_of_speech': 'adverb',
            'pronunciation': '/ˈsʌmtaɪmz/',
            'frequency_rank': 280,
            'difficulty': 1,
            'features': {}
        },
        {
            'lemma': 'today',
            'text': 'today',
            'part_of_speech': 'adverb',
            'pronunciation': '/təˈdeɪ/',
            'frequency_rank': 120,
            'difficulty': 1,
            'features': {}
        },
        {
            'lemma': 'tomorrow',
            'text': 'tomorrow',
            'part_of_speech': 'adverb',
            'pronunciation': '/təˈmɔroʊ/',
            'frequency_rank': 290,
            'difficulty': 1,
            'features': {}
        },
        {
            'lemma': 'yesterday',
            'text': 'yesterday',
            'part_of_speech': 'adverb',
            'pronunciation': '/ˈjɛstərdeɪ/',
            'frequency_rank': 300,
            'difficulty': 1,
            'features': {}
        },
        {
            'lemma': 'here',
            'text': 'here',
            'part_of_speech': 'adverb',
            'pronunciation': '/hɪr/',
            'frequency_rank': 130,
            'difficulty': 1,
            'features': {}
        },
        {
            'lemma': 'there',
            'text': 'there',
            'part_of_speech': 'adverb',
            'pronunciation': '/ðɛr/',
            'frequency_rank': 140,
            'difficulty': 1,
            'features': {}
        }
    ]

    # French vocabulary for MVP
    french_words_data = [
        {
            'lemma': 'livre',
            'text': 'livre',
            'part_of_speech': 'noun',
            'pronunciation': '/liːvʁ/',
            'frequency_rank': 100,
            'difficulty': 1,
            'features': {'plural': 'livres', 'category': 'object'}
        },
        {
            'lemma': 'maison',
            'text': 'maison',
            'part_of_speech': 'noun',
            'pronunciation': '/mɛzɔ̃/',
            'frequency_rank': 50,
            'difficulty': 1,
            'features': {'plural': 'maisons', 'category': 'object'}
        },
        {
            'lemma': 'eau',
            'text': 'eau',
            'part_of_speech': 'noun',
            'pronunciation': '/o/',
            'frequency_rank': 30,
            'difficulty': 1,
            'features': {'category': 'liquid', 'uncountable': True}
        },
        {
            'lemma': 'lire',
            'text': 'lire',
            'part_of_speech': 'verb',
            'pronunciation': '/liːʁ/',
            'frequency_rank': 80,
            'difficulty': 1,
            'features': {'tenses': ['lit', 'lis', 'lit'], 'category': 'action'}
        },
        {
            'lemma': 'écrire',
            'text': 'écrire',
            'part_of_speech': 'verb',
            'pronunciation': '/ekʁiːʁ/',
            'frequency_rank': 120,
            'difficulty': 2,
            'features': {'tenses': ['écrit', 'écris', 'écrit'], 'category': 'action'}
        }
    ]

    created_words = []

    # Create English words
    for word_data in words_data:
        word = Word(
            id=uuid.uuid4(),
            language_id=lang_ids['en'],
            **word_data
        )
        db.add(word)
        created_words.append(word)

    # Create French words
    for word_data in french_words_data:
        word = Word(
            id=uuid.uuid4(),
            language_id=lang_ids['fr'],
            **word_data
        )
        db.add(word)
        created_words.append(word)

    db.commit()
    print(f"Created {len(created_words)} words")
    return created_words


def create_sentences(db: Session, words: list, lang_ids: dict):
    """Create sentences with translations and gaps"""
    print("Creating sentences...")

    # Existing custom sentences
    custom_sentences_data = [
        {
            'word_lemma': 'book',
            'text': 'The ___ is on the table.',
            'translation': 'O livro está na mesa.',
            'type': 'example',
            'gap_start': 4,
            'gap_end': 8,
            'difficulty': 1
        },
        {
            'word_lemma': 'house',
            'text': 'They live in a big ___.',
            'translation': 'Eles moram em uma casa grande.',
            'type': 'example',
            'gap_start': 18,
            'gap_end': 23,
            'difficulty': 1
        },
        {
            'word_lemma': 'water',
            'text': 'Please give me some ___ to drink.',
            'translation': 'Por favor, me dê um pouco de ___ para beber.',
            'type': 'example',
            'gap_start': 20,
            'gap_end': 25,
            'difficulty': 1
        },
        {
            'word_lemma': 'read',
            'text': 'I like to ___ books every day.',
            'translation': 'Eu gosto de ___ livros todos os dias.',
            'type': 'usage',
            'gap_start': 13,
            'gap_end': 17,
            'difficulty': 1
        },
        {
            'word_lemma': 'write',
            'text': 'Can you ___ your name here?',
            'translation': 'Você pode ___ seu nome aqui?',
            'type': 'question',
            'gap_start': 8,
            'gap_end': 13,
            'difficulty': 1
        },
        {
            'word_lemma': 'beautiful',
            'text': 'What a ___ sunset!',
            'translation': 'Que pôr do sol ___!',
            'type': 'expression',
            'gap_start': 7,
            'gap_end': 16,
            'difficulty': 2
        },
        {
            'word_lemma': 'quickly',
            'text': 'She ran ___ to catch the bus.',
            'translation': 'Ela correu ___ para pegar o ônibus.',
            'type': 'example',
            'gap_start': 12,
            'gap_end': 19,
            'difficulty': 2
        },
        {
            'word_lemma': 'friend',
            'text': 'My best ___ is coming to visit.',
            'translation': 'Meu melhor ___ está vindo visitar.',
            'type': 'example',
            'gap_start': 8,
            'gap_end': 14,
            'difficulty': 1
              }
    ]

    created_sentences = []

    # Create custom sentences first
    for sent_data in custom_sentences_data:
        word_lemma = sent_data['word_lemma']
        # Remove word_lemma from dict for Sentence creation
        sentence_data = {k: v for k, v in sent_data.items() if k != 'word_lemma'}

        word = next((w for w in words if w.lemma == word_lemma), None)

        if word:
            sentence = Sentence(
                id=uuid.uuid4(),
                word_id=word.id,
                language_id=lang_ids['en'],
                **sentence_data
            )
            db.add(sentence)
            created_sentences.append(sentence)

    # Generate automatic sentences for remaining words
    sentence_templates = [
        {
            'template': 'I need to buy a ___.',
            'translation': 'Eu preciso comprar um/uma ___.',
            'type': 'usage'
        },
        {
            'template': 'The ___ is very nice.',
            'translation': 'O/A ___ é muito bom(a).',
            'type': 'example'
        },
        {
            'template': 'Can you see the ___?',
            'translation': 'Você consegue ver o/a ___?',
            'type': 'question'
        },
        {
            'template': 'My ___ is new.',
            'translation': 'Meu/minha ___ é novo(a).',
            'type': 'example'
        },
        {
            'template': 'I like this ___.',
            'translation': 'Eu gosto deste/desta ___.',
            'type': 'usage'
        }
    ]

    # Track which words already have sentences
    words_with_sentences = {sent['word_lemma'] for sent in custom_sentences_data}

    # Create multiple sentences per word to reach >=100 cards
    sentence_counter = 0
    max_sentences = 100

    for word in words:
        if word.lemma not in words_with_sentences and len(created_sentences) < max_sentences:
            # Choose a template based on word type
            if word.part_of_speech == 'noun':
                template_data = sentence_templates[len(created_sentences) % len(sentence_templates)]
            elif word.part_of_speech == 'verb':
                verb_templates = [
                    {'template': 'I want to ___.', 'translation': 'Eu quero ___.', 'type': 'usage'},
                    {'template': 'Let\'s ___ together.', 'translation': 'Vamos ___ juntos.', 'type': 'suggestion'},
                    {'template': 'She can ___ very well.', 'translation': 'Ela pode ___ muito bem.', 'type': 'example'}
                ]
                template_data = verb_templates[len(created_sentences) % len(verb_templates)]
            elif word.part_of_speech == 'adjective':
                adj_templates = [
                    {'template': 'The house is ___.', 'translation': 'A casa é ___.', 'type': 'example'},
                    {'template': 'This is very ___.', 'translation': 'Isto é muito ___.', 'type': 'usage'},
                    {'template': 'You look ___.', 'translation': 'Você parece ___.', 'type': 'compliment'}
                ]
                template_data = adj_templates[len(created_sentences) % len(adj_templates)]
            elif word.part_of_speech == 'adverb':
                adv_templates = [
                    {'template': 'She walks ___.', 'translation': 'Ela anda ___.', 'type': 'example'},
                    {'template': 'He works ___.', 'translation': 'Ele trabalha ___.', 'type': 'usage'},
                    {'template': 'Please speak ___.', 'translation': 'Por favor, fale ___.', 'type': 'request'}
                ]
                template_data = adv_templates[len(created_sentences) % len(adv_templates)]
            else:
                template_data = sentence_templates[0]

            # Generate sentence with gap
            sentence_text = template_data['template'].replace('___', '___')
            gap_start = template_data['template'].find('___')
            gap_end = gap_start + 3  # "___" length

            sentence = Sentence(
                id=uuid.uuid4(),
                word_id=word.id,
                language_id=lang_ids['en'],
                text=sentence_text,
                translation=template_data['translation'].replace('___', word.features.get('pt_translation', '___') if word.features else '___'),
                type=template_data['type'],
                difficulty=word.difficulty,
                gap_start=gap_start,
                gap_end=gap_end
            )
            db.add(sentence)
            created_sentences.append(sentence)

    # Second pass: create additional sentences for words that already have sentences
    if len(created_sentences) < max_sentences:
        for word in words:
            if len(created_sentences) >= max_sentences:
                break

            # Skip first 20 words to add variety
            if len(created_sentences) < 20:
                continue

            # Choose a different template for variety
            template_index = len(created_sentences) % len(sentence_templates)
            template_data = sentence_templates[template_index]

            # Generate sentence with gap
            sentence_text = template_data['template'].replace('___', '___')
            gap_start = template_data['template'].find('___')
            gap_end = gap_start + 3  # "___" length

            sentence = Sentence(
                id=uuid.uuid4(),
                word_id=word.id,
                language_id=lang_ids['en'],
                text=sentence_text,
                translation=template_data['translation'].replace('___', word.features.get('pt_translation', '___') if word.features else '___'),
                type=template_data['type'],
                difficulty=word.difficulty,
                gap_start=gap_start,
                gap_end=gap_end
            )
            db.add(sentence)
            created_sentences.append(sentence)

    db.commit()
    print(f"Created {len(created_sentences)} sentences")
    return created_sentences


def create_decks(db: Session, lang_ids: dict):
    """Create deck categories"""
    print("Creating decks...")

    decks_data = [
        {
            'name': 'Everyday English',
            'language_id': lang_ids['en'],
            'difficulty_level': 1,
            'description': 'Common everyday vocabulary for beginners',
            'card_count': 0,
            'is_active': True
        },
        {
            'name': 'Basic Actions',
            'language_id': lang_ids['en'],
            'difficulty_level': 2,
            'description': 'Common verbs and actions',
            'card_count': 0,
            'is_active': True
        },
        {
            'name': 'Descriptive Words',
            'language_id': lang_ids['en'],
            'difficulty_level': 3,
            'description': 'Adjectives and descriptions',
            'card_count': 0,
            'is_active': True
        }
    ]

    created_decks = []
    for deck_data in decks_data:
        deck = Deck(
            id=uuid.uuid4(),
            **deck_data
        )
        db.add(deck)
        created_decks.append(deck)

    db.commit()
    print(f"Created {len(created_decks)} decks")
    return created_decks


def create_cards(db: Session, sentences: list, decks: list):
    """Create study cards from sentences"""
    print("Creating cards...")

    # Grammar hints for each word/sentence
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

    created_cards = []
    for sentence in sentences:
        # Assign cards to decks based on difficulty
        deck = decks[sentence.difficulty - 1]  # difficulty 1-3 maps to deck 0-2

        # Get the word to find the appropriate grammar hint
        word = db.query(Word).filter(Word.id == sentence.word_id).first()
        grammar_hint = grammar_hints.get(word.lemma, 'Preencha com a palavra correta')

        card = Card(
            id=uuid.uuid4(),
            sentence_id=sentence.id,
            deck_id=deck.id,
            grammar_hint=grammar_hint,
            difficulty=sentence.difficulty,
            gap_start=sentence.gap_start,
            gap_end=sentence.gap_end,
            is_active=True
        )
        db.add(card)
        created_cards.append(card)

        # Update deck card count
        deck.card_count += 1

    db.commit()
    print(f"Created {len(created_cards)} cards")
    return created_cards


def create_demo_user(db: Session):
    """Create demo user for testing"""
    print("Creating demo user...")

    # Check if demo user already exists
    existing_user = db.query(User).filter(User.username == "demo").first()
    if existing_user:
        print(f"Demo user already exists: {existing_user.username}")
        return existing_user

    # Get language IDs
    en_lang = db.query(Language).filter(Language.code == "en").first()
    pt_lang = db.query(Language).filter(Language.code == "pt").first()

    if not en_lang or not pt_lang:
        raise ValueError("Languages 'en' and 'pt' must exist before creating demo user")

    demo_user = User(
        id=uuid.uuid4(),
        username="demo",
        email="demo@filltheword.com",
        native_language_id=pt_lang.id,  # Portuguese: native language
        target_language_id=en_lang.id,   # English: learning target
        language_preference="pt",        # UI in Portuguese
        daily_new_limit=10,
        easiness_factor=2.5
    )
    db.add(demo_user)

    db.commit()
    print(f"Created demo user: {demo_user.username}")
    return demo_user


def create_user_card_states(db: Session, user: User, cards: list):
    """Create initial user card states for SM-2 algorithm"""
    print("Creating user card states...")

    now = datetime.utcnow()
    created_states = []

    for card in cards:
        state = UserCardState(
            id=uuid.uuid4(),
            user_id=user.id,
            card_id=card.id,
            repetitions=0,
            easiness_factor=2.5,
            interval_days=1,
            next_review_at=now,  # Due immediately for first review
            last_reviewed_at=None,
            status=MemoryStage.NEW,
            total_reviews=0,
            correct_reviews=0
        )
        db.add(state)
        created_states.append(state)

    db.commit()
    print(f"Created {len(created_states)} user card states")
    return created_states


def cleanup_existing_data(db: Session):
    """Clean up existing seed data to avoid duplicates"""
    print("Cleaning up existing seed data...")

    # Delete in reverse order of dependencies
    db.query(UserCardState).delete()
    db.query(ReviewEvent).delete()  # Must delete before Card
    db.query(Card).delete()
    db.query(Sentence).delete()
    db.query(Word).delete()
    db.query(Deck).delete()
    db.query(User).filter(User.username == "demo").delete()

    db.commit()
    print("Cleaned up existing seed data")


def main():
    """Main seed function"""
    import argparse
    parser = argparse.ArgumentParser(description='Seed FillTheWord database')
    parser.add_argument('--reset', action='store_true', help='Reset all data before seeding')
    args = parser.parse_args()

    print("Starting FillTheWord seed data creation...")
    if args.reset:
        print("🔄 Reset mode: cleaning existing data...")

    db = SessionLocal()
    try:
        if args.reset:
            cleanup_existing_data(db)

        # Create data in dependency order
        lang_ids = create_languages(db)
        words = create_words(db, lang_ids)
        sentences = create_sentences(db, words, lang_ids)
        decks = create_decks(db, lang_ids)
        cards = create_cards(db, sentences, decks)
        demo_user = create_demo_user(db)
        user_states = create_user_card_states(db, demo_user, cards)

        print("\n🎉 Seed data creation completed successfully!")
        print(f"📊 Summary:")
        print(f"  - Languages: {len(lang_ids)}")
        print(f"  - Words: {len(words)}")
        print(f"  - Sentences: {len(sentences)}")
        print(f"  - Decks: {len(decks)}")
        print(f"  - Cards: {len(cards)}")
        print(f"  - Demo User: 1")
        print(f"  - User Card States: {len(user_states)}")

    except Exception as e:
        print(f"❌ Error during seed data creation: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
