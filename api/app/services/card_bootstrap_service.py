"""Bootstrap helpers for local demo card data."""

from __future__ import annotations

import uuid

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.models import Card, Deck, Language, Sentence, User, UserCardState, Word
from app.models.user_card_state import MemoryStage


def create_sample_data_if_needed(db: Session) -> None:
    """Ensure the local demo user has at least one card state to study."""
    try:
        demo_user = db.query(User).filter(User.username == "demo").first()
        has_demo_user_state = False
        if demo_user:
            has_demo_user_state = (
                db.query(UserCardState)
                .filter(UserCardState.user_id == demo_user.id)
                .first()
                is not None
            )

        if demo_user and has_demo_user_state:
            return

        print("Creating/updating sample data...")

        en_lang = db.query(Language).filter(Language.code == "en").first()
        if not en_lang:
            en_lang = Language(
                id=str(uuid.uuid4()),
                code="en",
                name="English",
                voice_model="lessac-glow_tts",
                voice_type="female",
                is_active=True,
            )
            db.add(en_lang)
            db.flush()

        pt_lang = db.query(Language).filter(Language.code == "pt").first()
        if not pt_lang:
            pt_lang = Language(
                id=str(uuid.uuid4()),
                code="pt",
                name="Portuguese",
                voice_model="lessac-glow_tts",
                voice_type="female",
                is_active=True,
            )
            db.add(pt_lang)
            db.flush()

        demo_user = db.query(User).filter(User.username == "demo").first()
        if not demo_user:
            demo_user = User(
                id=str(uuid.uuid4()),
                username="demo",
                email="demo@wordbridge.coach",
                native_language_id=pt_lang.id,
                target_language_id=en_lang.id,
                language_preference="pt",
                daily_new_limit=10,
                easiness_factor=2.5,
            )
            db.add(demo_user)
            db.flush()

        card_count = db.query(Card).count()
        if card_count == 0:
            print("Creating minimal card data...")

            deck = Deck(
                id=str(uuid.uuid4()),
                name="Daily English",
                language_id=en_lang.id,
                difficulty_level=1,
                description="Common everyday vocabulary",
                is_active=True,
            )
            db.add(deck)
            db.flush()

            word = Word(
                id=str(uuid.uuid4()),
                lemma="book",
                text="book",
                part_of_speech="noun",
                language_id=en_lang.id,
                pronunciation="/bʊk/",
                frequency_rank=1,
                difficulty=1,
            )
            db.add(word)
            db.flush()

            sentence = Sentence(
                id=str(uuid.uuid4()),
                text="The ___ is on the table.",
                translation="O livro está na mesa.",
                word_id=word.id,
                language_id=en_lang.id,
                type="example",
                difficulty=1,
                gap_start=4,
                gap_end=7,
                quality_status="approved",
                license_name="MIT (project-authored)",
                content_version="bootstrap-v1",
                is_contemporary=True,
            )
            db.add(sentence)
            db.flush()

            card = Card(
                id=str(uuid.uuid4()),
                sentence_id=sentence.id,
                deck_id=deck.id,
                grammar_hint="Use the word for the object you read",
                difficulty=1,
                gap_start=4,
                gap_end=7,
                is_active=True,
            )
            db.add(card)
            db.flush()
        else:
            card = db.query(Card).first()

        existing_state = db.query(UserCardState).filter(
            and_(
                UserCardState.user_id == demo_user.id,
                UserCardState.card_id == card.id,
            )
        ).first()

        if not existing_state:
            user_card_state = UserCardState(
                id=str(uuid.uuid4()),
                user_id=demo_user.id,
                card_id=card.id,
                repetitions=0,
                easiness_factor=2.5,
                interval_days=1,
                next_review_at=utc_now(),
                status=MemoryStage.NEW,
                total_reviews=0,
                correct_reviews=0,
            )
            db.add(user_card_state)

        db.commit()
        print("Sample data created successfully")

    except Exception as error:
        db.rollback()
        print(f"Error creating sample data: {error}")
