"""Idempotent persistence for reviewed, versioned course content."""

import re
import uuid

from sqlalchemy.orm import Session

from app.models import Card, Sentence, Word
from app.models.sentence import SourceType
from app.pedagogy.curated_content import CURATED_EN_V1


def _create_single_gap(sentence: str, word: str) -> tuple[str, int, int]:
    match = re.search(r"\b" + re.escape(word) + r"\b", sentence, re.IGNORECASE)
    if not match:
        raise ValueError(f"Curated target {word!r} is absent from sentence {sentence!r}")
    gap_start = match.start()
    return sentence[:gap_start] + "___" + sentence[match.end():], gap_start, gap_start + 3


def seed_curated_english_content(db: Session, *, language_id, deck) -> tuple[list[Sentence], list[Card]]:
    """Insert the project-authored English pack and repair missing active cards."""
    created_sentences = []
    created_cards = []
    for index, item in enumerate(CURATED_EN_V1, start=1):
        word = db.query(Word).filter(
            Word.lemma == item["word"],
            Word.language_id == language_id,
        ).first()
        if not word:
            continue

        source_ref = f"wordbridge:contemporary-en-v1:{index:03d}"
        sentence = db.query(Sentence).filter(Sentence.source_ref == source_ref).first()
        if sentence:
            existing_card = db.query(Card).filter(
                Card.sentence_id == sentence.id,
                Card.is_active == True,
            ).first()
            if not existing_card:
                card = Card(
                    id=uuid.uuid4(),
                    sentence_id=sentence.id,
                    deck_id=deck.id,
                    grammar_hint="",
                    difficulty=word.difficulty,
                    gap_start=sentence.gap_start,
                    gap_end=sentence.gap_end,
                    is_active=True,
                )
                db.add(card)
                created_cards.append(card)
            continue

        gapped_text, gap_start, gap_end = _create_single_gap(item["text"], item["word"])
        sentence = Sentence(
            id=uuid.uuid4(),
            text=gapped_text,
            translation=item["translation"],
            word_id=word.id,
            language_id=language_id,
            type="example",
            source_type=SourceType.MANUAL,
            difficulty=word.difficulty,
            gap_start=gap_start,
            gap_end=gap_end,
            source_title="WordBridge Contemporary English",
            source_author="WordBridge project",
            source_ref=source_ref,
            cefr_level=item["cefr"],
            register="neutral",
            domain=item["domain"],
            competency_codes=[item["skill"]],
            grammar_tags=[],
            quality_status="approved",
            license_name="MIT (project-authored)",
            content_version="contemporary-en-v1",
            is_contemporary=True,
        )
        card = Card(
            id=uuid.uuid4(),
            sentence_id=sentence.id,
            deck_id=deck.id,
            grammar_hint="",
            difficulty=word.difficulty,
            gap_start=gap_start,
            gap_end=gap_end,
            is_active=True,
        )
        db.add_all([sentence, card])
        created_sentences.append(sentence)
        created_cards.append(card)

    db.flush()
    return created_sentences, created_cards
