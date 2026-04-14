"""Tests for card request/user resolution and response serialization helpers."""

import uuid

import pytest
from fastapi import HTTPException

from app.models import Card, Deck, Sentence, User, Word
from app.models.sentence import SourceType
from app.models.user_card_state import MemoryStage
from app.services.card_response_service import format_card_response, resolve_request_user_id


def test_resolve_request_user_id_returns_explicit_value(db_session):
    explicit_user_id = str(uuid.uuid4())

    assert resolve_request_user_id(db_session, explicit_user_id) == explicit_user_id


def test_resolve_request_user_id_uses_demo_user_when_missing(db_session, sample_languages):
    demo_user = User(
        id=str(uuid.uuid4()),
        username="demo",
        email="demo@example.com",
        native_language_id=sample_languages["pt"].id,
        target_language_id=sample_languages["en"].id,
        language_preference="pt",
    )
    db_session.add(demo_user)
    db_session.commit()

    assert resolve_request_user_id(db_session, None) == str(demo_user.id)


def test_resolve_request_user_id_raises_when_demo_user_missing(db_session):
    with pytest.raises(HTTPException) as exc_info:
        resolve_request_user_id(db_session, None)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail["error"] == "Demo user not found"


def test_format_card_response_serializes_expected_payload(db_session, sample_languages):
    word = Word(
        id=str(uuid.uuid4()),
        lemma="book",
        text="book",
        part_of_speech="noun",
        language_id=sample_languages["en"].id,
        frequency_rank=100,
        difficulty=1,
    )
    sentence = Sentence(
        id=str(uuid.uuid4()),
        text="The ___ is on the table.",
        translation="O livro está na mesa.",
        word_id=word.id,
        language_id=sample_languages["en"].id,
        type="example",
        source_type=SourceType.CORPUS,
        difficulty=1,
        gap_start=4,
        gap_end=7,
    )
    deck = Deck(
        id=str(uuid.uuid4()),
        name="Daily English",
        language_id=sample_languages["en"].id,
        difficulty_level=1,
        is_active=True,
    )
    card = Card(
        id=str(uuid.uuid4()),
        sentence_id=sentence.id,
        deck_id=deck.id,
        grammar_hint="Use the noun for something you read",
        difficulty=1,
        gap_start=4,
        gap_end=7,
        is_active=True,
    )

    sentence.word = word
    card.sentence = sentence

    response = format_card_response(card, MemoryStage.NEW)

    assert response.card_id == str(card.id)
    assert response.word_id == str(word.id)
    assert response.sentence_id == str(sentence.id)
    assert response.word == "book"
    assert response.sentence == "The ___ is on the table."
    assert response.sentence_translation == "O livro está na mesa."
    assert response.memory_stage == "NEW"
    assert response.is_new is True
    assert response.audio_word_url.endswith(f"/api/tts/word/{card.id}?text=book&lang=en")
    assert response.audio_sentence_url.endswith(
        f"/api/tts/sentence/{card.id}?text=The%20book%20is%20on%20the%20table.&lang=en"
    )
