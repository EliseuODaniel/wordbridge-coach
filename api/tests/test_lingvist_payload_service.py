from types import SimpleNamespace

from app.services import lingvist_payload_service
from app.schemas.lingvist import MicroProgress
from app.services.lingvist_payload_service import (
    build_grammar_tag_pt,
    build_lingvist_card_response,
    build_relative_audio_urls,
    extract_word_translation,
)


def test_build_grammar_tag_pt_includes_pos_and_features():
    word = SimpleNamespace(
        part_of_speech="noun",
        features={"number": "singular", "gender": "masculine"},
    )

    assert build_grammar_tag_pt(word) == "substantivo, singular, masculino"


def test_extract_word_translation_strips_and_normalizes_empty_values():
    word_with_translation = SimpleNamespace(features={"pt_translation": "  livro  "})
    word_without_translation = SimpleNamespace(features={"pt_translation": "   "})

    assert extract_word_translation(word_with_translation) == "livro"
    assert extract_word_translation(word_without_translation) is None


def test_build_relative_audio_urls_uses_target_language_and_filled_sentence():
    card = SimpleNamespace(id="card-1")
    word = SimpleNamespace(text="book")
    sentence = SimpleNamespace(text="The ___ is here.")

    word_url, sentence_url = build_relative_audio_urls(card, word, sentence, "en")

    assert word_url == "/api/tts/word/card-1?text=book&lang=en"
    assert sentence_url == "/api/tts/sentence/card-1?text=The%20book%20is%20here.&lang=en"


def test_build_lingvist_card_response_uses_enrichment_dependencies(monkeypatch):
    card = SimpleNamespace(id="card-1", gap_start=4, gap_end=7)
    word = SimpleNamespace(
        id="word-1",
        text="book",
        part_of_speech="noun",
        features={"pt_translation": "livro"},
    )
    sentence = SimpleNamespace(
        id="sentence-1",
        text="The ___ is here.",
        translation="O livro esta aqui.",
        source_title="source",
    )

    monkeypatch.setattr(
        lingvist_payload_service,
        "get_lingvist_entities_from_context",
        lambda db, card_context: (card, word, sentence),
    )
    monkeypatch.setattr(
        lingvist_payload_service,
        "get_micro_progress",
        lambda db, user_id, user: MicroProgress(current=1, total=10, new_words=1),
    )
    monkeypatch.setattr(
        lingvist_payload_service,
        "get_user_target_language_code",
        lambda db, user_id, default="en": "fr",
    )

    autofill_calls = []

    def fake_autofill(db, loaded_word, loaded_sentence, loaded_card):
        autofill_calls.append((loaded_word.text, loaded_sentence.text, loaded_card.id))

    payload = build_lingvist_card_response(
        db=object(),
        user_id="user-1",
        user=SimpleNamespace(daily_new_limit=10),
        card_context={
            "card_id": "card-1",
            "word_id": "word-1",
            "sentence_id": "sentence-1",
            "is_new": True,
        },
        autofill_translations=fake_autofill,
    )

    assert autofill_calls == [("book", "The ___ is here.", "card-1")]
    assert payload.word == "book"
    assert payload.word_translation_pt == "livro"
    assert payload.audio_word_url.endswith("lang=fr")
    assert payload.micro_progress.current == 1
