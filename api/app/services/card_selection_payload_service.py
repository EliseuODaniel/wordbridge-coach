"""Payload helpers for card selection flows."""

from __future__ import annotations

from urllib.parse import quote

from app.models import Card, Deck
from app.services.lingvist_payload_service import get_user_target_language_code
from app.services.content_quality_service import cloze_gap_bounds


def ensure_active_card_for_sentence(db, sentence, word):
    """Load or create the active card backing a selected sentence."""
    card = db.query(Card).filter(
        Card.sentence_id == sentence.id,
        Card.is_active == True,
    ).first()

    if card:
        return card

    deck = db.query(Deck).filter(
        Deck.language_id == word.language_id,
        Deck.is_active == True,
    ).first()

    if not deck:
        deck = Deck(
            name=f"Default {word.language_id}",
            language_id=word.language_id,
            difficulty_level=1,
            description="Auto-created default deck",
            is_active=True,
        )
        db.add(deck)
        db.flush()

    text = sentence.text or ""
    gap_start = text.find("___")
    gap_end = gap_start + 3 if gap_start >= 0 else len(text)

    card = Card(
        sentence_id=sentence.id,
        deck_id=deck.id,
        grammar_hint="",
        gap_start=gap_start,
        gap_end=gap_end,
        is_active=True,
    )
    db.add(card)
    db.flush()
    return card


def build_card_context_payload(db, user_id: str, word, sentence, is_new: bool):
    """Build the stable card context dict used by selection flows."""
    card = ensure_active_card_for_sentence(db, sentence, word)
    gap_start, gap_end = cloze_gap_bounds(sentence)
    lang_code = get_user_target_language_code(db, user_id)
    audio_word_url, audio_sentence_url = build_audio_urls(card.id, word.text or "", sentence.text or "", lang_code)

    return {
        "card_id": str(card.id),
        "word_id": str(word.id),
        "sentence_id": str(sentence.id),
        "word": word.text,
        "sentence": sentence.text or "",
        "gap": {
            "start": gap_start,
            "end": gap_end,
        },
        "sentence_translation": sentence.translation or "",
        "grammar_hint": card.grammar_hint or "",
        "memory_stage": "NEW" if is_new else "REVIEW",
        "is_new": is_new,
        "audio_word_url": audio_word_url,
        "audio_sentence_url": audio_sentence_url,
        "sentence_source": sentence.source_title if sentence.source_title else None,
    }


def build_audio_urls(card_id, word_text: str, sentence_text: str, lang_code: str) -> tuple[str, str]:
    """Build relative TTS URLs for a word and its filled sentence."""
    word_text_encoded = quote(word_text)
    audio_word_url = f"/api/tts/word/{card_id}?text={word_text_encoded}&lang={lang_code}"

    sentence_with_word = sentence_text.replace("___", word_text, 1)
    sentence_text_encoded = quote(sentence_with_word)
    audio_sentence_url = f"/api/tts/sentence/{card_id}?text={sentence_text_encoded}&lang={lang_code}"

    return audio_word_url, audio_sentence_url
