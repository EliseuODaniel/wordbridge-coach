"""Helpers for card endpoint request/user resolution and response serialization."""

from typing import Optional
from urllib.parse import quote

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Card, User
from app.models.user_card_state import MemoryStage
from app.schemas.card import CardResponse


def resolve_request_user_id(db: Session, user_id: Optional[str]) -> str:
    """Resolve an omitted request user to the local demo account."""
    if user_id:
        return user_id

    demo_user = db.query(User).filter(User.username == "demo").first()
    if not demo_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Demo user not found", "message": "User setup required"},
        )

    return str(demo_user.id)


def format_card_response(card: Card, memory_stage) -> CardResponse:
    """Serialize a card into the stable API payload used by study endpoints."""
    memory_stage_str = _normalize_memory_stage(memory_stage)
    sentence_text, sentence_translation = _get_sentence_content(card)
    word_text, sentence_text_for_audio = _get_audio_content(card, sentence_text)
    audio_word_url, audio_sentence_url = _build_tts_urls(
        card_id=str(card.id),
        word_text=word_text,
        sentence_text=sentence_text_for_audio,
    )

    return CardResponse(
        card_id=str(card.id),
        word_id=str(card.sentence.word.id) if card.sentence and card.sentence.word else "",
        sentence_id=str(card.sentence_id) if card.sentence_id else "",
        word=word_text,
        sentence=sentence_text,
        gap={"start": card.gap_start, "end": card.gap_end},
        sentence_translation=sentence_translation,
        grammar_hint=card.grammar_hint,
        memory_stage=memory_stage_str,
        is_new=memory_stage_str == "NEW",
        audio_word_url=audio_word_url,
        audio_sentence_url=audio_sentence_url,
    )


def _normalize_memory_stage(memory_stage) -> str:
    """Support either enum or plain string memory stage values."""
    if isinstance(memory_stage, MemoryStage):
        return memory_stage.value
    return memory_stage


def _get_sentence_content(card: Card) -> tuple[str, str]:
    """Read sentence text/translation with the same fallback used by legacy code."""
    try:
        return card.sentence.text, card.sentence.translation
    except Exception:
        return "The ___ is on the table.", "O livro está na mesa."


def _get_audio_content(card: Card, sentence_text: str) -> tuple[str, str]:
    """Read word text and build the filled sentence used by TTS URLs."""
    try:
        word_text = card.sentence.word.text if card.sentence and card.sentence.word else "word"
        return word_text, sentence_text.replace("___", word_text, 1)
    except Exception:
        return "word", sentence_text.replace("___", "word", 1)


def _build_tts_urls(card_id: str, word_text: str, sentence_text: str) -> tuple[str, str]:
    """Build relative TTS URLs that work behind the frontend proxy."""
    word_text_encoded = quote(word_text or '')
    sentence_text_encoded = quote(sentence_text or '')
    audio_word_url = f"/api/tts/word/{card_id}?text={word_text_encoded}&lang=en"
    audio_sentence_url = f"/api/tts/sentence/{card_id}?text={sentence_text_encoded}&lang=en"
    return audio_word_url, audio_sentence_url
