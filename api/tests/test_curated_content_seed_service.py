"""Tests for the reviewed contemporary content importer."""

from app.services.curated_content_seed_service import seed_curated_english_content


def test_curated_seed_is_idempotent_and_preserves_metadata(
    db_session,
    sample_languages,
    sample_decks,
    sample_words,
):
    first_sentences, first_cards = seed_curated_english_content(
        db_session,
        language_id=sample_languages["en"].id,
        deck=sample_decks["en"],
    )
    db_session.commit()
    second_sentences, second_cards = seed_curated_english_content(
        db_session,
        language_id=sample_languages["en"].id,
        deck=sample_decks["en"],
    )

    assert first_sentences
    assert len(first_sentences) == len(first_cards)
    assert second_sentences == []
    assert second_cards == []
    assert all(sentence.quality_status == "approved" for sentence in first_sentences)
    assert all(sentence.content_version == "contemporary-en-v1" for sentence in first_sentences)
    assert all(sentence.text.count("___") == 1 for sentence in first_sentences)
    assert all(sentence.gap_start == sentence.text.index("___") for sentence in first_sentences)
    assert all(sentence.gap_end == sentence.gap_start + 3 for sentence in first_sentences)
