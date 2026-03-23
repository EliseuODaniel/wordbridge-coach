"""Lingvist payload helpers extracted from the cards endpoint."""

from __future__ import annotations

from datetime import date
from typing import Optional
from urllib.parse import quote

from fastapi import HTTPException, status
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models import Card, Language, Sentence, User, UserCardState, Word
from app.models.user_card_state import MemoryStage
from app.models.user_session_stats import UserSessionStats
from app.schemas.lingvist import LingvistCardResponse, MicroProgress


def get_user_target_language_code(db: Session, user_id: str, default: str = "en") -> str:
    """Return the target language code for a user when available."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.target_language_id:
        return default

    target_lang = db.query(Language).filter(Language.id == user.target_language_id).first()
    return target_lang.code if target_lang else default


def get_card_memory_stage(db: Session, user_id: str, card_id: str) -> str:
    """Resolve the persisted memory stage for a card, defaulting to NEW."""
    card_state = db.query(UserCardState).filter(
        and_(
            UserCardState.user_id == user_id,
            UserCardState.card_id == card_id,
        )
    ).first()

    return card_state.status.value if card_state else "NEW"


def get_lingvist_entities_from_context(db: Session, card_context: dict) -> tuple[Card, Word, Sentence]:
    """Load the card, word, and sentence referenced by a card context payload."""
    card = db.query(Card).filter(Card.id == card_context["card_id"]).first()
    word = db.query(Word).filter(Word.id == card_context["word_id"]).first()
    sentence = db.query(Sentence).filter(Sentence.id == card_context["sentence_id"]).first()

    if not card or not word or not sentence:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Card data incomplete", "message": "Missing card/word/sentence"},
        )

    return card, word, sentence


def build_relative_audio_urls(card: Card, word: Word, sentence: Sentence, lang_code: str) -> tuple[str, str]:
    """Build relative API audio URLs for a word and its filled sentence."""
    word_text_encoded = quote(word.text or "")
    audio_word_url = f"/api/tts/word/{card.id}?text={word_text_encoded}&lang={lang_code}"

    sentence_with_gap = sentence.text or ""
    sentence_with_word = sentence_with_gap.replace("___", word.text, 1)
    sentence_text_encoded = quote(sentence_with_word)
    audio_sentence_url = f"/api/tts/sentence/{card.id}?text={sentence_text_encoded}&lang={lang_code}"

    return audio_word_url, audio_sentence_url


def build_grammar_tag_pt(word: Word) -> str:
    """Build PT-BR grammar tag from word.part_of_speech and word.features."""
    pos_mapping = {
        "noun": "substantivo",
        "verb": "verbo",
        "adjective": "adjetivo",
        "adverb": "advérbio",
        "preposition": "preposição",
        "article": "artigo",
        "pronoun": "pronome",
        "conjunction": "conjunção",
    }

    pos_pt = pos_mapping.get(word.part_of_speech, word.part_of_speech)
    features = []

    if word.features and isinstance(word.features, dict):
        if word.features.get("number"):
            number_pt = {"singular": "singular", "plural": "plural"}.get(word.features["number"])
            if number_pt:
                features.append(number_pt)

        if word.features.get("gender"):
            gender_pt = {
                "masculine": "masculino",
                "feminine": "feminine",
                "neuter": "neutro",
            }.get(word.features["gender"])
            if gender_pt:
                features.append(gender_pt)

        if word.features.get("tense"):
            tense_pt = {
                "present": "presente",
                "past": "passado",
                "future": "futuro",
            }.get(word.features["tense"])
            if tense_pt:
                features.append(tense_pt)

    return f"{pos_pt}, {', '.join(features)}" if features else pos_pt


def extract_word_translation(word: Word) -> Optional[str]:
    """Extract PT-BR translation from Word.features.pt_translation."""
    if word.features and isinstance(word.features, dict):
        translation = word.features.get("pt_translation")
        if translation and isinstance(translation, str) and translation.strip():
            return translation.strip()
    return None


def get_micro_progress(db: Session, user_id: str, user: User) -> MicroProgress:
    """Calculate micro-progress from UserSessionStats and User for today."""
    stats = db.query(UserSessionStats).filter(
        UserSessionStats.user_id == user_id,
        UserSessionStats.date == date.today(),
    ).first()

    if not stats:
        return MicroProgress(current=0, total=user.daily_new_limit, new_words=0)

    current = min(stats.cards_shown, user.daily_new_limit)
    total = user.daily_new_limit
    new_words = min(stats.new_cards_shown, user.daily_new_limit)

    return MicroProgress(current=current, total=total, new_words=new_words)


def build_lingvist_card_response(
    db: Session,
    user_id: str,
    user: User,
    card_context: dict,
    autofill_translations,
) -> LingvistCardResponse:
    """Build the enriched Lingvist payload from a base card context."""
    card, word, sentence = get_lingvist_entities_from_context(db, card_context)

    autofill_translations(db, word, sentence, card)

    grammar_tag_pt = build_grammar_tag_pt(word)
    word_translation_pt = extract_word_translation(word)
    sentence_translation_pt = (sentence.translation or "").strip() or None
    micro_progress = get_micro_progress(db, user_id, user)
    lang_code = get_user_target_language_code(db, user_id)
    audio_word_url, audio_sentence_url = build_relative_audio_urls(card, word, sentence, lang_code)

    return LingvistCardResponse(
        card_id=str(card.id),
        word_id=str(word.id),
        sentence_id=str(sentence.id),
        word=word.text,
        sentence=sentence.text or "",
        gap={"start": card.gap_start or 0, "end": card.gap_end or 0},
        correct_answer=word.text,
        grammar_tag_pt=grammar_tag_pt,
        word_translation_pt=word_translation_pt,
        sentence_translation_pt=sentence_translation_pt,
        sentence_source=sentence.source_title if sentence.source_title else None,
        is_new=card_context["is_new"],
        micro_progress=micro_progress,
        audio_word_url=audio_word_url,
        audio_sentence_url=audio_sentence_url,
    )
