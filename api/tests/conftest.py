"""Pytest configuration and fixtures for FillTheWord testing"""

import os

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://ftw_user:ftw_password@localhost:5433/filltheword_test"
)
os.environ["TEST_DATABASE_URL"] = TEST_DATABASE_URL
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["DEBUG"] = os.getenv("TEST_DEBUG", "false")

import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from typing import Dict, List, Generator

from app.core.database import Base, get_db
from app.core.time import utc_now, utc_today
from app.main import app
from app.models import (
    User, Language, Word, Sentence, Card, Deck,
    WordFrequency, WordTheme, WordThemeMapping,
    UserCardState, UserWordStats, UserThemeStats, UserDailyStats,
    MemoryStage
)
from app.models.sentence import SourceType

# Host execution uses localhost:5433, while containers may override via TEST_DATABASE_URL.
SQLALCHEMY_DATABASE_URL = TEST_DATABASE_URL

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=False  # Set to True for SQL debugging during tests
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _drop_postgres_enum_types() -> None:
    """Remove enum types that may survive interrupted test runs on PostgreSQL."""
    if not SQLALCHEMY_DATABASE_URL.startswith("postgresql"):
        return

    enum_names = ("sourcetype", "memorystage", "messagerole")
    with engine.begin() as connection:
        for enum_name in enum_names:
            connection.execute(text(f"DROP TYPE IF EXISTS {enum_name} CASCADE"))


@pytest.fixture(scope="session")
def db() -> Generator:
    """Setup test database and run migrations"""
    # Reset any leftover schema objects from interrupted runs before recreating tables.
    Base.metadata.drop_all(bind=engine, checkfirst=True)
    _drop_postgres_enum_types()
    # Create all tables using SQLAlchemy models
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up test database
    Base.metadata.drop_all(bind=engine, checkfirst=True)
    _drop_postgres_enum_types()


@pytest.fixture
def db_session(db) -> Generator:
    """Create a fresh database session for each test"""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    # Override the get_db dependency
    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    yield session

    session.close()
    transaction.rollback()
    connection.close()
    app.dependency_overrides.clear()


@pytest.fixture
def client(db_session) -> Generator:
    """Create test client"""
    yield TestClient(app)


@pytest.fixture
def sample_languages(db_session) -> Dict[str, Language]:
    """Create sample languages for testing"""
    languages = {
        'en': Language(
            id=str(uuid.uuid4()),
            code="en",
            name="English",
            voice_model="lessac-glow_tts",
            voice_type="female",
            is_active=True
        ),
        'fr': Language(
            id=str(uuid.uuid4()),
            code="fr",
            name="French",
            voice_model="lessac-glow_tts",
            voice_type="female",
            is_active=True
        ),
        'pt': Language(
            id=str(uuid.uuid4()),
            code="pt",
            name="Portuguese",
            voice_model="lessac-glow_tts",
            voice_type="female",
            is_active=True
        )
    }

    for lang in languages.values():
        db_session.add(lang)
    db_session.commit()

    return languages


@pytest.fixture
def sample_words_frequencies(db_session, sample_languages) -> List[WordFrequency]:
    """Create sample word frequencies for testing EN and FR"""
    frequencies = []

    # English words (ranks 1-200)
    en_words = [
        ("the", 1, 78.5, 1),
        ("be", 2, 76.1, 1),
        ("to", 3, 74.2, 1),
        ("of", 4, 71.8, 1),
        ("and", 5, 69.3, 1),
        ("a", 6, 67.9, 1),
        ("in", 7, 65.4, 1),
        ("that", 8, 62.8, 1),
        ("have", 9, 60.1, 1),
        ("it", 10, 58.3, 1),
        ("there", 50, 72.1, 1),
        ("book", 100, 67.9, 1),
        ("house", 150, 64.2, 1),
        ("beautiful", 200, 60.1, 1)
    ]

    for word, rank, coverage, band in en_words:
        freq = WordFrequency(
            word=word,
            language_code="en",
            rank=rank,
            coverage_pct=coverage,
            band=band,
            frequency_score=1.0 - (rank / 1000),
            is_active=True
        )
        frequencies.append(freq)

    # French words (ranks 1-200)
    fr_words = [
        ("le", 1, 75.2, 1),
        ("de", 2, 72.8, 1),
        ("et", 3, 70.1, 1),
        ("à", 4, 67.5, 1),
        ("un", 5, 64.9, 1),
        ("il", 6, 62.3, 1),
        ("être", 7, 59.8, 1),
        ("et", 8, 57.1, 1),
        ("en", 9, 54.6, 1),
        ("avoir", 10, 52.1, 1),
        ("livre", 100, 65.1, 1),
        ("maison", 150, 61.8, 1),
        ("beau", 200, 58.2, 1)
    ]

    for word, rank, coverage, band in fr_words:
        freq = WordFrequency(
            word=word,
            language_code="fr",
            rank=rank,
            coverage_pct=coverage,
            band=band,
            frequency_score=1.0 - (rank / 1000),
            is_active=True
        )
        frequencies.append(freq)

    for freq in frequencies:
        db_session.add(freq)
    db_session.commit()

    return frequencies


@pytest.fixture
def sample_words(db_session, sample_languages, sample_words_frequencies) -> Dict[str, Word]:
    """Create sample words linked to frequencies"""
    words = {}

    # Create a frequency lookup map
    freq_map = {}
    for freq in sample_words_frequencies:
        freq_map[(freq.language_code, freq.word)] = freq.rank

    # Create English words with frequency_rank
    en_lang = sample_languages['en']
    en_word_data = [
        ("there", "adverb"),
        ("book", "noun"),
        ("house", "noun"),
        ("beautiful", "adjective")
    ]

    for word_text, pos in en_word_data:
        frequency_rank = freq_map.get(("en", word_text), 50)  # Default rank if not found
        word = Word(
            id=str(uuid.uuid4()),
            text=word_text,
            lemma=word_text.lower(),
            part_of_speech=pos,
            difficulty=1,
            language_id=en_lang.id,
            frequency_rank=frequency_rank
        )
        db_session.add(word)
        words[f"en_{word_text}"] = word

    # Create French words with frequency_rank
    fr_lang = sample_languages['fr']
    fr_word_data = [
        ("livre", "noun"),
        ("maison", "noun"),
        ("beau", "adjective")
    ]

    for word_text, pos in fr_word_data:
        frequency_rank = freq_map.get(("fr", word_text), 150)  # Default rank if not found
        word = Word(
            id=str(uuid.uuid4()),
            text=word_text,
            lemma=word_text.lower(),
            part_of_speech=pos,
            difficulty=1,
            language_id=fr_lang.id,
            frequency_rank=frequency_rank
        )
        db_session.add(word)
        words[f"fr_{word_text}"] = word

    db_session.commit()
    return words


@pytest.fixture
def sample_sentences(db_session, sample_languages, sample_words) -> Dict[str, Sentence]:
    """Create sample sentences for testing"""
    sentences = {}

    # English sentences
    en_there_word = sample_words.get("en_there")
    if en_there_word:
        sentence = Sentence(
            id=str(uuid.uuid4()),
            text="The book is ___ there.",
            translation="O livro está lá.",
            grammar_hint="adverb - location",
            gap_start=13,
            gap_end=16,
            language_id=sample_languages['en'].id,
            word_id=en_there_word.id,
            type="FILL_IN_THE_GAP",  # Required field
            source_type=SourceType.CORPUS,  # Required field
            difficulty=1  # Required field
        )
        db_session.add(sentence)
        sentences["en_there"] = sentence

    # Add sentence for "book" (rank 100)
    en_book_word = sample_words.get("en_book")
    if en_book_word:
        sentence = Sentence(
            id=str(uuid.uuid4()),
            text="I am reading a ___.",
            translation="Estou lendo um livro.",
            grammar_hint="noun - object",
            gap_start=16,
            gap_end=19,
            language_id=sample_languages['en'].id,
            word_id=en_book_word.id,
            type="FILL_IN_THE_GAP",  # Required field
            source_type=SourceType.CORPUS,  # Required field
            difficulty=1  # Required field
        )
        db_session.add(sentence)
        sentences["en_book"] = sentence

    # French sentences
    fr_word = sample_words.get("fr_livre")
    if fr_word:
        sentence = Sentence(
            id=str(uuid.uuid4()),
            text="Je lis un ___.",
            translation="I am reading a book.",
            grammar_hint="noun - book",
            gap_start=9,
            gap_end=12,
            language_id=sample_languages['fr'].id,
            word_id=fr_word.id,
            type="FILL_IN_THE_GAP",  # Required field
            source_type=SourceType.CORPUS,  # Required field
            difficulty=1  # Required field
        )
        db_session.add(sentence)
        sentences["fr_livre"] = sentence

    db_session.commit()
    return sentences


@pytest.fixture
def sample_decks(db_session, sample_languages) -> Dict[str, Deck]:
    """Create sample decks for testing"""
    decks = {}

    # Create English deck
    en_deck = Deck(
        id=str(uuid.uuid4()),
        name="English Basic",
        language_id=sample_languages['en'].id,
        difficulty_level=1,
        description="Basic English deck",
        card_count=0,
        is_active=True
    )
    db_session.add(en_deck)
    decks['en'] = en_deck

    # Create French deck
    fr_deck = Deck(
        id=str(uuid.uuid4()),
        name="French Basic",
        language_id=sample_languages['fr'].id,
        difficulty_level=1,
        description="Basic French deck",
        card_count=0,
        is_active=True
    )
    db_session.add(fr_deck)
    decks['fr'] = fr_deck

    db_session.commit()
    return decks


@pytest.fixture
def sample_cards(db_session, sample_sentences, sample_decks) -> Dict[str, Card]:
    """Create sample cards for testing"""
    cards = {}

    for sentence_key, sentence in sample_sentences.items():
        # Determine deck based on sentence language
        deck = sample_decks['en'] if 'en_' in sentence_key else sample_decks['fr']

        card = Card(
            id=str(uuid.uuid4()),
            sentence_id=sentence.id,
            deck_id=deck.id,
            grammar_hint=sentence.grammar_hint or "",
            gap_start=sentence.gap_start,
            gap_end=sentence.gap_end,
            is_active=True,
            difficulty=1
        )
        db_session.add(card)
        cards[sentence_key] = card

    db_session.commit()
    return cards


@pytest.fixture
def sample_themes(db_session) -> List[WordTheme]:
    """Create sample themes for testing"""
    themes = [
        WordTheme(id=str(uuid.uuid4()), name="locations", is_active=True),
        WordTheme(id=str(uuid.uuid4()), name="objects", is_active=True),
        WordTheme(id=str(uuid.uuid4()), name="descriptions", is_active=True),
        WordTheme(id=str(uuid.uuid4()), name="actions", is_active=True)
    ]

    for theme in themes:
        db_session.add(theme)

    db_session.commit()
    return themes


@pytest.fixture
def test_user(db_session, sample_languages) -> User:
    """Create a test user with goal=100 for English"""
    user = User(
        id=str(uuid.uuid4()),
        username="testuser",
        email="test@example.com",
        language_preference="pt",
        native_language_id=sample_languages['pt'].id,
        target_language_id=sample_languages['en'].id,
        daily_new_limit=10,
        easiness_factor=2.5,
        word_goal_rank=100
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_user_french(db_session, sample_languages) -> User:
    """Create a test user with goal=150 for French"""
    user = User(
        id=str(uuid.uuid4()),
        username="testuser_fr",
        email="test_fr@example.com",
        language_preference="pt",
        native_language_id=sample_languages['pt'].id,
        target_language_id=sample_languages['fr'].id,
        daily_new_limit=8,
        easiness_factor=2.3,
        word_goal_rank=150
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def user_card_states(db_session, sample_cards, test_user):
    """Create UserCardState for test user"""
    states = []
    for card in sample_cards.values():
        state = UserCardState(
            id=str(uuid.uuid4()),
            user_id=test_user.id,
            card_id=card.id,
            status=MemoryStage.NEW,
            easiness_factor=2.5,
            interval_days=1,
            repetitions=0,
            next_review_at=utc_now()
        )
        states.append(state)

    for state in states:
        db_session.add(state)
    db_session.commit()

    return states


@pytest.fixture
def sample_user_daily_stats(db_session, test_user):
    """Create sample user daily stats"""
    stats = UserDailyStats(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        date=utc_today(),
        cards_answered=10,
        new_words_learned=3,
        reviews_done=7,
        accuracy=0.8
    )
    db_session.add(stats)
    db_session.commit()
    return stats


@pytest.fixture
def sample_user_theme_stats(db_session, test_user, sample_themes):
    """Create sample user theme stats"""
    stats_list = []
    for i, theme in enumerate(sample_themes[:2]):  # Only for first 2 themes
        stats = UserThemeStats(
            id=str(uuid.uuid4()),
            user_id=test_user.id,
            theme_id=theme.id,
            attempts=10 + i * 5,
            correct=8 + i * 3,
            avg_response_time_ms=2500 + i * 500,
            last_practiced_at=utc_now() - timedelta(days=i)
        )
        # Calculate accuracy after setting attempts and correct
        stats.update_accuracy()
        stats_list.append(stats)
        db_session.add(stats)

    db_session.commit()
    return stats_list
