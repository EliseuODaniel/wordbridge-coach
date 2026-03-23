"""Tests for card selection payload helpers."""

import uuid

from app.models import Sentence, Word
from app.models.sentence import SourceType
from app.services.card_selection_payload_service import build_card_context_payload


def test_build_card_context_payload_auto_creates_card(db_session, test_user, sample_languages):
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
    db_session.add_all([word, sentence])
    db_session.commit()

    payload = build_card_context_payload(
        db_session,
        user_id=str(test_user.id),
        word=word,
        sentence=sentence,
        is_new=True,
    )

    assert payload["word"] == "book"
    assert payload["is_new"] is True
    assert payload["audio_word_url"].endswith("lang=en")
    assert payload["gap"] == {"start": 4, "end": 7}


def test_build_card_context_payload_preserves_existing_card_and_source(
    db_session, test_user, sample_words, sample_cards
):
    word = sample_words["en_book"]
    card = sample_cards["en_book"]
    sentence = card.sentence
    sentence.source_title = "Dracula"
    db_session.commit()

    payload = build_card_context_payload(
        db_session,
        user_id=str(test_user.id),
        word=word,
        sentence=sentence,
        is_new=False,
    )

    assert payload["card_id"] == str(card.id)
    assert payload["sentence_source"] == "Dracula"
    assert payload["is_new"] is False
