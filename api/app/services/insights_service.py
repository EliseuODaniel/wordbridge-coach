"""Shared services for analytics word insights."""

from __future__ import annotations

from typing import List
import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Card, Language, Word, WordFrequency, WordTheme, WordThemeMapping


def parse_uuid_or_400(raw_id: str, *, entity_name: str) -> uuid.UUID:
    """Parse a UUID or raise the stable API payload for invalid IDs."""
    try:
        return uuid.UUID(raw_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                'error': f'Invalid {entity_name} ID format',
                'message': f'{entity_name.capitalize()} ID must be a valid UUID',
            },
        ) from exc


def get_word_or_404(db: Session, word_id: str) -> Word:
    word_uuid = parse_uuid_or_400(word_id, entity_name='word')
    word = db.query(Word).filter(Word.id == word_uuid).first()
    if not word:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'error': 'Word not found', 'message': f'Word with ID {word_id} not found'},
        )

    return word


def get_word_from_card_or_404(db: Session, card_id: str) -> Word:
    card_uuid = parse_uuid_or_400(card_id, entity_name='card')
    card = db.query(Card).filter(Card.id == card_uuid).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'error': 'Card not found', 'message': f'Card with ID {card_id} not found'},
        )

    if not card.sentence or not card.sentence.word:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'error': 'Word not found', 'message': f'Word for card {card_id} not found'},
        )

    return card.sentence.word


def get_language_code(db: Session, language_id: str | None, default: str = 'en') -> str:
    if not language_id:
        return default

    language = db.query(Language).filter(Language.id == language_id).first()
    return language.code if language else default


def get_frequency_metadata(db: Session, word: Word) -> WordFrequency | None:
    language_code = get_language_code(db, word.language_id)
    return db.query(WordFrequency).filter(
        WordFrequency.word == word.lemma.lower(),
        WordFrequency.language_code == language_code,
    ).first()


def get_grammar_classification(word: Word) -> str:
    if not word.features:
        return word.part_of_speech

    return word.part_of_speech


def get_frequency_description(rank: int, language_code: str = 'en') -> str:
    language_name = 'English' if language_code == 'en' else 'French' if language_code == 'fr' else 'this language'

    if rank <= 100:
        return f'This word is among the 100 most frequent words in {language_name}.'
    if rank <= 500:
        return f'This word is among the 500 most frequent words in {language_name}.'
    if rank <= 1000:
        return f'This word is among the 1,000 most frequent words in {language_name}.'
    if rank <= 2000:
        return f'This word is among the 2,000 most frequent words in {language_name}.'
    if rank <= 5000:
        return 'This word is in the top half of the 10,000 most frequent words.'
    return 'This word is in the less frequent half of your 10,000-word deck.'


def build_word_insight_payload(db: Session, word: Word) -> dict:
    language_code = get_language_code(db, word.language_id)
    word_freq = get_frequency_metadata(db, word)
    grammar_info = {
        'part_of_speech': word.part_of_speech,
        'classification': get_grammar_classification(word),
        'grammar_hint': 'Use the correct word',
    }

    if word_freq:
        rank = word_freq.rank
        coverage_pct = word_freq.coverage_pct or 0.0
        frequency_score = word_freq.frequency_score or 0.0
        band = word_freq.band
        frequency_description = get_frequency_description(rank, language_code)
        coverage_description = f'Coverage up to here: {coverage_pct:.1f}% of word usage'
    else:
        rank = None
        coverage_pct = None
        frequency_score = None
        band = None
        frequency_description = 'This word is not in the frequency database.'
        coverage_description = 'Coverage information not available.'

    return {
        'word_id': str(word.id),
        'word': word.text,
        'rank': rank,
        'coverage_pct': coverage_pct,
        'frequency_score': frequency_score,
        'band': band,
        'grammar_info': grammar_info,
        'frequency_description': frequency_description,
        'coverage_description': coverage_description,
    }


def get_word_insight_by_word_id(db: Session, word_id: str) -> dict:
    return build_word_insight_payload(db, get_word_or_404(db, word_id))


def get_word_insight_by_card_id(db: Session, card_id: str) -> dict:
    return build_word_insight_payload(db, get_word_from_card_or_404(db, card_id))


def get_word_theme_names(db: Session, word_id: str) -> List[str]:
    word_uuid = parse_uuid_or_400(word_id, entity_name='word')
    word_themes = db.query(WordTheme).join(
        WordThemeMapping, WordTheme.id == WordThemeMapping.theme_id
    ).filter(
        WordThemeMapping.word_id == word_uuid,
        WordTheme.is_active == True,
    ).all()

    return [theme.name for theme in word_themes]
