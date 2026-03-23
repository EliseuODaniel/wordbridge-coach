"""Card endpoints for FillTheWord API"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, select
from datetime import timedelta
import uuid
import os
import logging

from app.core.database import get_db
from app.core.time import utc_now, utc_today
from app.core.config import settings
from app.schemas.card import CardResponse, AnswerRequest, AnswerResponse, ErrorResponse
from app.schemas.lingvist import LingvistCardResponse, MicroProgress
from app.services.sm2 import SM2Algorithm
from app.services.card_selection import CardSelectionService
from app.services.lingvist_payload_service import (
    build_grammar_tag_pt as _build_grammar_tag_pt_service,
    build_lingvist_card_response as _build_lingvist_card_response_service,
    build_relative_audio_urls as _build_relative_audio_urls_service,
    extract_word_translation as _extract_word_translation_service,
    get_card_memory_stage as _get_card_memory_stage_service,
    get_lingvist_entities_from_context as _get_lingvist_entities_from_context_service,
    get_micro_progress as _get_micro_progress_service,
    get_user_target_language_code as _get_user_target_language_code_service,
)
from app.models import Language, Word, Sentence, Card, Deck, User, UserCardState, ReviewEvent
from app.models.user_session_stats import UserSessionStats
from app.models.user_card_state import MemoryStage
from app.models.user_theme_stats import UserThemeStats
from app.models.word_theme_mapping import WordThemeMapping

router = APIRouter()
logger = logging.getLogger(__name__)

# Global cache for TSV translations (override priority over MT)
_tsv_translations_cache: Optional[dict[str, str]] = None


def _load_tsv_translations() -> dict[str, str]:
    """Load EN-PT translations from TSV file (priority over MT).

    Returns:
        Dict mapping lowercase word -> pt_translation
    """
    global _tsv_translations_cache

    if _tsv_translations_cache is not None:
        return _tsv_translations_cache

    _tsv_translations_cache = {}
    tsv_path = "/app/data/en_pt_word_translations_sample.tsv"

    if not os.path.exists(tsv_path):
        logger.info(f"TSV file not found: {tsv_path}")
        return _tsv_translations_cache

    try:
        logger.info(f"Loading TSV translations from {tsv_path}...")
        with open(tsv_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue

                parts = line.split('\t')
                if len(parts) < 2:
                    continue

                word = parts[0].strip()
                pt_translation = parts[1].strip()

                # Skip empty translations
                if not pt_translation:
                    continue

                # Store with lowercase key for matching
                _tsv_translations_cache[word.lower()] = pt_translation

        logger.info(f"✅ Loaded {len(_tsv_translations_cache)} TSV translations")
    except Exception as e:
        logger.error(f"Failed to load TSV translations: {e}")

    return _tsv_translations_cache


def _autofill_translations(db: Session, word: 'Word', sentence: 'Sentence', card: 'Card'):
    """Auto-generate translations if missing (on-demand with DB cache).

    Priority:
    1. Existing translation in DB (do nothing)
    2. TSV override (curated translations)
    3. MT (Argos Translate or Google Translate) if LINGVIST_TRANSLATIONS_AUTOFILL=true

    Args:
        db: Database session
        word: Word object
        sentence: Sentence object
        card: Card object (for sentence reconstruction)
    """
    from app.services.translation_service import get_translation_service

    # Load TSV cache (priority override)
    tsv_override = _load_tsv_translations()

    # --- Word translation ---
    word_needs_translation = (
        not word.features or
        not isinstance(word.features, dict) or
        not word.features.get("pt_translation") or
        not word.features["pt_translation"].strip()
    )

    if word_needs_translation:
        word_translation = None

        # Try TSV override first
        word_lower = word.lemma.lower() if word.lemma else ""
        if word_lower in tsv_override:
            word_translation = tsv_override[word_lower]
            logger.info(f"✅ Word translation from TSV: {word.lemma} → {word_translation}")

        # Fallback to MT if enabled
        else:
            translation_service = get_translation_service()
            if translation_service.is_enabled():
                word_translation = translation_service.translate(word.lemma or word.text)
                if word_translation:
                    logger.info(f"🤖 Word translation from {translation_service.get_provider()}: {word.lemma} → {word_translation}")

        # Save to DB if translation found
        if word_translation:
            if not word.features:
                word.features = {}
            word.features['pt_translation'] = word_translation
            db.flush()  # Flush without commit (caller commits)
            logger.debug(f"💾 Saved word translation to DB: {word.lemma}")

    # --- Sentence translation ---
    sentence_needs_translation = (
        not sentence.translation or
        not sentence.translation.strip()
    )

    if sentence_needs_translation:
        # Reconstruct sentence with word filled in
        sentence_with_gap = sentence.text or ""
        sentence_with_word = sentence_with_gap.replace("___", word.text or "", 1)

        # Try MT if enabled (no TSV for sentences)
        translation_service = get_translation_service()
        if translation_service.is_enabled():
            sentence_translation = translation_service.translate(sentence_with_word)
            if sentence_translation:
                logger.info(f"🤖 Sentence translation from {translation_service.get_provider()}: '{sentence_with_word[:50]}...' → '{sentence_translation[:50]}...'")
                sentence.translation = sentence_translation
                db.flush()  # Flush without commit (caller commits)
                logger.debug(f"💾 Saved sentence translation to DB")
        else:
            logger.debug(f"⚠️ Translation service disabled, skipping sentence translation")

def create_sample_data_if_needed(db: Session):
    """Create minimal sample data for testing"""
    try:
        # Always ensure demo user and UserCardState exist
        demo_user = db.query(User).filter(User.username == "demo").first()
        has_demo_user_state = False
        if demo_user:
            has_demo_user_state = db.query(UserCardState).filter(
                UserCardState.user_id == demo_user.id
            ).first() is not None

        # If we have demo user with card states, return
        if demo_user and has_demo_user_state:
            return

        print("Creating/updating sample data...")

        # Get or create English language
        en_lang = db.query(Language).filter(Language.code == "en").first()
        if not en_lang:
            en_lang = Language(
                id=str(uuid.uuid4()),
                code="en",
                name="English",
                voice_model="lessac-glow_tts",
                voice_type="female",
                is_active=True
            )
            db.add(en_lang)
            db.flush()  # Get the ID

        # Get or create Portuguese language
        pt_lang = db.query(Language).filter(Language.code == "pt").first()
        if not pt_lang:
            pt_lang = Language(
                id=str(uuid.uuid4()),
                code="pt",
                name="Portuguese",
                voice_model="lessac-glow_tts",
                voice_type="female",
                is_active=True
            )
            db.add(pt_lang)
            db.flush()  # Get the ID

        # Get or create demo user
        demo_user = db.query(User).filter(User.username == "demo").first()
        if not demo_user:
            demo_user = User(
                id=str(uuid.uuid4()),
                username="demo",
                email="demo@filltheword.com",
                native_language_id=pt_lang.id,  # Portuguese: native language
                target_language_id=en_lang.id,   # English: learning target
                language_preference="pt",        # UI in Portuguese
                daily_new_limit=10,
                easiness_factor=2.5
            )
            db.add(demo_user)
            db.flush()  # Get the ID

        # Check if we have any cards, if not create minimal data
        card_count = db.query(Card).count()
        if card_count == 0:
            print("Creating minimal card data...")

            # Create deck
            deck = Deck(
                id=str(uuid.uuid4()),
                name="Daily English",
                language_id=en_lang.id,
                difficulty_level=1,
                description="Common everyday vocabulary",
                is_active=True
            )
            db.add(deck)
            db.flush()

            # Create word
            word = Word(
                id=str(uuid.uuid4()),
                lemma="book",
                text="book",
                part_of_speech="noun",
                language_id=en_lang.id,
                pronunciation="/bʊk/",
                frequency_rank=1,
                difficulty=1
            )
            db.add(word)
            db.flush()

            # Create sentence
            sentence = Sentence(
                id=str(uuid.uuid4()),
                text="The ___ is on the table.",
                translation="O livro está na mesa.",
                word_id=word.id,
                language_id=en_lang.id,
                type="example",
                difficulty=1,
                gap_start=4,
                gap_end=7  # end exclusive: "___" = positions 4,5,6
            )
            db.add(sentence)
            db.flush()

            # Create card
            card = Card(
                id=str(uuid.uuid4()),
                sentence_id=sentence.id,
                deck_id=deck.id,
                grammar_hint="Use the word for the object you read",
                difficulty=1,
                gap_start=4,
                gap_end=6,
                is_active=True
            )
            db.add(card)
            db.flush()
        else:
            # Get existing card for UserCardState creation
            card = db.query(Card).first()

        # Ensure UserCardState exists for the demo user and card
        existing_state = db.query(UserCardState).filter(
            and_(
                UserCardState.user_id == demo_user.id,
                UserCardState.card_id == card.id
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
                correct_reviews=0
            )
            db.add(user_card_state)

        db.commit()
        print("Sample data created successfully")

    except Exception as e:
        db.rollback()
        print(f"Error creating sample data: {e}")


def _resolve_request_user_id(db: Session, user_id: Optional[str]) -> str:
    """Resolve omitted user_id to the local demo user."""
    if user_id:
        return user_id

    demo_user = db.query(User).filter(User.username == "demo").first()
    if not demo_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Demo user not found", "message": "User setup required"}
        )

    return demo_user.id


def _get_user_target_language_code(db: Session, user_id: str, default: str = "en") -> str:
    """Return the target language code for a user when available."""
    return _get_user_target_language_code_service(db, user_id, default=default)


def _get_card_memory_stage(db: Session, user_id: str, card_id: str) -> str:
    """Resolve the persisted memory stage for a card, defaulting to NEW."""
    return _get_card_memory_stage_service(db, user_id, card_id)


def _get_lingvist_entities_from_context(
    db: Session,
    card_context: dict
) -> tuple[Card, Word, Sentence]:
    """Load the card, word, and sentence referenced by a card context payload."""
    return _get_lingvist_entities_from_context_service(db, card_context)


def _build_relative_audio_urls(card: Card, word: Word, sentence: Sentence, lang_code: str) -> tuple[str, str]:
    """Build relative API audio URLs for a word and its filled sentence."""
    return _build_relative_audio_urls_service(card, word, sentence, lang_code)


def _build_lingvist_card_response(
    db: Session,
    user_id: str,
    user: User,
    card_context: dict
) -> LingvistCardResponse:
    """Build the enriched Lingvist payload from a base card context."""
    return _build_lingvist_card_response_service(
        db=db,
        user_id=user_id,
        user=user,
        card_context=card_context,
        autofill_translations=_autofill_translations,
    )


def _get_or_create_daily_stats(db: Session, user_id: str):
    """Load today's daily stats row, creating it when needed."""
    from app.models.user_daily_stats import UserDailyStats

    today = utc_today()
    daily_stats = db.query(UserDailyStats).filter(
        UserDailyStats.user_id == user_id,
        UserDailyStats.date == today
    ).first()

    if daily_stats:
        return daily_stats

    daily_stats = UserDailyStats(
        user_id=user_id,
        date=today,
        cards_answered=0,
        new_words_learned=0,
        reviews_done=0,
        accuracy=0.0
    )
    db.add(daily_stats)
    db.flush()
    return daily_stats


def _update_user_accuracy_last_20(db: Session, user_id: str, is_correct: bool) -> Optional[User]:
    """Recompute rolling accuracy for the user based on the latest answer."""
    from sqlalchemy import desc

    recent_20 = db.query(ReviewEvent)\
        .filter(ReviewEvent.user_id == user_id)\
        .order_by(desc(ReviewEvent.created_at))\
        .limit(19)\
        .all()

    correct_count = sum(1 for review in recent_20 if review.was_correct)
    if is_correct:
        correct_count += 1

    total_count = len(recent_20) + 1
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    user.accuracy_last_20 = correct_count / total_count if total_count > 0 else None
    print(f"DEBUG: Updated user accuracy_last_20={user.accuracy_last_20}")
    return user


def _update_relearn_state(
    db: Session,
    user: Optional[User],
    user_card_state: UserCardState,
    card_id: str,
    user_id: str,
    quality: int
) -> None:
    """Apply Lingvist relearn queue updates for the reviewed card."""
    if not user or user.mode != 'lingvist':
        return

    should_relearn = SM2Algorithm.should_enter_relearn(quality)

    if should_relearn:
        user_card_state.is_relearn = True

        relearn_count = db.query(ReviewEvent)\
            .filter(
                ReviewEvent.user_id == user_id,
                ReviewEvent.card_id == card_id,
                ReviewEvent.quality < 3
            )\
            .count()

        relearn_interval = SM2Algorithm.calculate_relearn_interval(relearn_count)
        user_card_state.relearn_due = utc_now() + relearn_interval
        print(f"DEBUG: Card entered relearn queue, due in {relearn_interval}, count={relearn_count}")
        return

    if user_card_state.is_relearn:
        user_card_state.is_relearn = False
        user_card_state.relearn_due = None
        print("DEBUG: Card exited relearn queue, returning to normal SM-2")


def _update_theme_stats(
    db: Session,
    user_id: str,
    word_id: str,
    was_correct: bool,
    response_time_ms: int
) -> None:
    """Update theme-level stats for every active theme linked to the word."""
    theme_mappings = db.query(WordThemeMapping.theme_id).filter(
        and_(
            WordThemeMapping.word_id == word_id,
            WordThemeMapping.is_active == True
        )
    ).all()

    for theme_mapping in theme_mappings:
        theme_id = theme_mapping[0]

        theme_stats = db.query(UserThemeStats).filter(
            and_(
                UserThemeStats.user_id == user_id,
                UserThemeStats.theme_id == theme_id
            )
        ).first()

        if not theme_stats:
            theme_stats = UserThemeStats(
                user_id=user_id,
                theme_id=theme_id,
                attempts=0,
                correct=0,
                accuracy=0.0,
                avg_response_time_ms=0.0
            )
            db.add(theme_stats)
            db.flush()

        theme_stats.add_attempt(
            was_correct=was_correct,
            response_time_ms=response_time_ms
        )
        print(
            f"DEBUG: Updated UserThemeStats for theme_id={theme_id}, "
            f"attempts={theme_stats.attempts}, accuracy={theme_stats.accuracy:.3f}"
        )


@router.get("/next", response_model=CardResponse)
async def get_next_card(
    user_id: Optional[str] = None,  # For MVP, we'll use a mock user
    db: Session = Depends(get_db)
):
    """
    Get next card for study based on SM-2 algorithm

    Priority:
    1. Due cards for review (next_review_at <= now)
    2. New cards (respecting daily limit)
    3. Learning cards

    Returns exact payload specification from API.md
    """
    try:
        # Ensure we have sample data
        create_sample_data_if_needed(db)

        user_id = _resolve_request_user_id(db, user_id)

        # Get user's daily new limit
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "User not found", "message": "User setup required"}
            )

        daily_new_limit = user.daily_new_limit

        # Calculate new cards today
        # Same logic as in stats endpoint
        cards_seen_today = db.query(
            func.distinct(ReviewEvent.card_id)
        ).filter(
            and_(
                ReviewEvent.user_id == user_id,
                func.date(ReviewEvent.created_at) == func.current_date()
            )
        ).subquery()

        cards_seen_before_today = db.query(
            func.distinct(ReviewEvent.card_id)
        ).filter(
            and_(
                ReviewEvent.user_id == user_id,
                func.date(ReviewEvent.created_at) < func.current_date()
            )
        ).subquery()

        # Cards seen today but never before today
        new_cards_today = db.query(Card.id).filter(
            and_(
                Card.id.in_(select(cards_seen_today.c[0])),
                ~Card.id.in_(select(cards_seen_before_today.c[0]))
            )
        ).count() or 0

        # Find next card using SM-2 priority logic with daily limit
        # Priority 1: Due cards for review
        now = utc_now()
        due_card = db.query(UserCardState).join(Card).filter(
            and_(
                UserCardState.user_id == user_id,
                UserCardState.next_review_at <= now,
                Card.is_active == True
            )
        ).order_by(UserCardState.next_review_at).first()

        if due_card:
            return format_card_response(due_card.card, due_card.status)

        # Check if we can still give new cards today
        can_give_new_cards = new_cards_today < daily_new_limit

        if can_give_new_cards:
            # Priority 2: New cards
            new_card_state = db.query(UserCardState).join(Card).filter(
                and_(
                    UserCardState.user_id == user_id,
                    UserCardState.status == MemoryStage.NEW,
                    Card.is_active == True
                )
            ).first()

            if new_card_state:
                return format_card_response(new_card_state.card, new_card_state.status)

        # Priority 3: Learning cards (if new cards limit reached or no new cards)
        learning_card_state = db.query(UserCardState).join(Card).filter(
            and_(
                UserCardState.user_id == user_id,
                UserCardState.status == MemoryStage.LEARNING,
                Card.is_active == True
            )
        ).first()

        if learning_card_state:
            return format_card_response(learning_card_state.card, learning_card_state.status)

        # No cards available
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "No cards available",
                "message": "Todos os cartões foram revisados hoje!"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_next_card: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "message": str(e)}
        )


def format_card_response(card: Card, memory_stage) -> CardResponse:
    """Format card data for API response"""

    # Normalize memory_stage to string (handle both MemoryStage enum and string)
    from app.models.user_card_state import MemoryStage
    if isinstance(memory_stage, MemoryStage):
        memory_stage_str = memory_stage.value
    else:
        memory_stage_str = memory_stage

    # Try to get sentence data, fall back to default if relationships don't work
    try:
        sentence_text = card.sentence.text
        sentence_translation = card.sentence.translation
    except:
        # Fallback when relationships are disabled
        sentence_text = "The ___ is on the table."
        sentence_translation = "O livro está na mesa."

    # Get the actual word text for TTS URLs
    try:
        word_text = card.sentence.word.text if card.sentence and card.sentence.word else "word"
        sentence_text_for_audio = sentence_text.replace("___", word_text, 1)
    except:
        word_text = "word"
        sentence_text_for_audio = sentence_text.replace("___", "word", 1)

    # Build TTS URLs for frontend consumption (localhost)
    # For production, this could be configurable
    tts_base_url = "http://localhost:8001"
    audio_word_url = f"{tts_base_url}/api/tts/word/{card.id}?text={word_text}&lang=en"
    audio_sentence_url = f"{tts_base_url}/api/tts/sentence/{card.id}?text={sentence_text_for_audio}&lang=en"

    return CardResponse(
        card_id=str(card.id),  # Convert UUID to string for API response
        word_id=str(card.sentence.word.id) if card.sentence and card.sentence.word else "",
        sentence_id=str(card.sentence_id) if card.sentence_id else "",  # Spec4: sentence variety tracking
        word=word_text,
        sentence=sentence_text,
        gap={"start": card.gap_start, "end": card.gap_end},
        sentence_translation=sentence_translation,
        grammar_hint=card.grammar_hint,
        memory_stage=memory_stage_str,  # Use normalized string value
        is_new=memory_stage_str == "NEW",  # Correct comparison with string
        audio_word_url=audio_word_url,
        audio_sentence_url=audio_sentence_url
    )


@router.post("/{card_id}/answer", response_model=AnswerResponse)
async def submit_answer(
    card_id: str,
    answer_data: AnswerRequest,
    user_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Submit answer for a card and update SM-2 progress
    
    Validates answer with tolerance and returns SM-2 feedback
    
    Validation rules:
    - Case insensitive: "Book" = "book"
    - Accent removal: "café" = "cafe"
    - Article tolerance: "book" accepts "a book"/"the book"
    - Synonym support: "color" accepts "colour"
    - Plural control based on context
    """
    try:
        # CRITICAL: Card MUST exist (Spec4 requirement - no fallback)
        card = db.query(Card).filter(Card.id == card_id).first()

        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Card not found", "message": f"No Card found with ID {card_id}"}
            )

        # Validate Card has required relationships
        if not card.sentence:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "Card data incomplete", "message": f"Card {card_id} has no sentence"}
            )

        if not card.sentence.word:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "Card data incomplete", "message": f"Card {card_id} sentence has no word"}
            )

        # Get correct answer from Card->Sentence->Word
        correct_answer = card.sentence.word.text
        sentence_full = card.sentence.text.replace("___", correct_answer, 1)
        sentence_id = str(card.sentence.id)  # CRITICAL for Spec4 variety
        
        # Validate answer using SM-2 tolerance rules
        print(f"DEBUG: Validating answer '{answer_data.answer}' against '{correct_answer}'")
        is_correct, normalized_correct = SM2Algorithm.validate_answer(
            user_answer=answer_data.answer,
            correct_answer=correct_answer,
            synonyms=["tome"]  # Example synonyms
        )

        print(f"DEBUG: SM2 validation result: is_correct={is_correct}, normalized_correct={normalized_correct}")

        # Calculate SM-2 quality
        print(f"DEBUG: Calculating quality for response_time_ms={answer_data.response_time_ms}, attempts={answer_data.attempts}, hints={answer_data.hints_used}")
        try:
            quality = SM2Algorithm.calculate_quality_from_response(
                was_correct=is_correct,
                response_time_ms=answer_data.response_time_ms,
                hints_used=answer_data.hints_used,
                attempts=answer_data.attempts
            )
            print(f"DEBUG: SM2 quality calculated: {quality}")
        except Exception as e:
            print(f"DEBUG: Error calculating SM2 quality: {e}")
            raise

        user_id = _resolve_request_user_id(db, user_id)

        # Get or create UserCardState (always required for Spec4)
        user_card_state = db.query(UserCardState).filter(
            and_(
                UserCardState.user_id == user_id,
                UserCardState.card_id == card_id
            )
        ).first()

        if not user_card_state:
            # Create new state if doesn't exist
            user_card_state = UserCardState(
                id=str(uuid.uuid4()),
                user_id=user_id,
                card_id=card_id,
                repetitions=0,
                easiness_factor=2.5,
                interval_days=1,
                next_review_at=utc_now(),
                status=MemoryStage.NEW,
                total_reviews=0,
                correct_reviews=0
            )
            db.add(user_card_state)

        # Calculate next review with SM-2
        # Capture previous values BEFORE updating UserCardState
        previous_easiness = user_card_state.easiness_factor
        previous_interval = user_card_state.interval_days

        try:
            print(f"DEBUG: Calculating SM2 next review with quality={quality}, repetitions={user_card_state.repetitions}")
            sm2_result = SM2Algorithm.calculate_next_review(
                quality=quality,
                current_repetitions=user_card_state.repetitions,
                current_easiness_factor=user_card_state.easiness_factor,
                current_interval_days=user_card_state.interval_days
            )
            print(f"DEBUG: SM2 result: {sm2_result}")
        except Exception as e:
            print(f"DEBUG: Error calculating SM2 next review: {e}")
            raise

        # CRITICAL: Create ReviewEvent with sentence_id (Spec4 requirement)
        review_event = ReviewEvent(
            user_id=user_id,
            card_id=card_id,
            sentence_id=sentence_id,  # CRITICAL: Always populated for Spec4 variety
            quality=quality,
            response_time_ms=answer_data.response_time_ms,
            user_answer=answer_data.answer,
            correct_answer=correct_answer,
            was_correct=is_correct,
            hints_used=answer_data.hints_used,
            attempts=answer_data.attempts,
            previous_easiness=previous_easiness,
            new_easiness=sm2_result["easiness_factor"],
            previous_interval=previous_interval,
            new_interval=sm2_result["interval_days"]
        )
        db.add(review_event)
        print(f"DEBUG: ReviewEvent created with sentence_id={sentence_id}, attempts={answer_data.attempts}")

        daily_stats = _get_or_create_daily_stats(db, user_id)

        # Update daily stats using the model's method
        daily_stats.update_accuracy(was_correct=is_correct)

        # Track new words learned separately (only for correct answers)
        if is_correct:
            daily_stats.add_new_word()

        # Update UserCardState with SM-2 results
        user_card_state.repetitions = sm2_result["repetitions"]
        user_card_state.easiness_factor = sm2_result["easiness_factor"]
        user_card_state.interval_days = sm2_result["interval_days"]
        user_card_state.next_review_at = sm2_result["next_review_at"]
        user_card_state.total_reviews += 1
        if is_correct:
            user_card_state.correct_reviews += 1

        # Update memory stage based on new interval
        if user_card_state.interval_days >= 21:
            user_card_state.status = MemoryStage.MATURE
        elif user_card_state.repetitions > 0:
            user_card_state.status = MemoryStage.LEARNING
        else:
            user_card_state.status = MemoryStage.NEW

        user = _update_user_accuracy_last_20(db, user_id, is_correct)
        _update_relearn_state(db, user, user_card_state, card_id, user_id, quality)

        print(f"DEBUG: UserCardState updated successfully")

        word_id = card.sentence.word_id
        _update_theme_stats(
            db=db,
            user_id=user_id,
            word_id=word_id,
            was_correct=is_correct,
            response_time_ms=answer_data.response_time_ms
        )

        # CRITICAL: Update Spec4 progression after correct answer
        if is_correct:
            try:
                card_service = CardSelectionService(db)
                card_service.record_answer(
                    user_id=user_id,
                    word_id=str(card.sentence.word_id),
                    sentence_id=sentence_id,  # CRITICAL: Always populated
                    was_correct=is_correct,
                    response_time_ms=answer_data.response_time_ms,
                    quality=quality
                )
                print(f"DEBUG: Called CardSelectionService.record_answer for word_id={card.sentence.word_id}")
            except Exception as e:
                print(f"DEBUG: Error updating Spec4 progression: {e}")
                # Continue even if progression update fails

        print(f"DEBUG: Attempting to commit database changes...")
        try:
            # Commit all changes
            db.commit()
            print(f"DEBUG: Database commit successful")
        except Exception as e:
            print(f"DEBUG: Error during database commit: {e}")
            db.rollback()
            raise

        try:
            response_data = {
                "correct": is_correct,
                "correct_answer": correct_answer,
                "sentence_full": sentence_full,
                "quality": quality,
                "next_review_at": sm2_result["next_review_at"]
            }
            print(f"DEBUG: Creating response with data: {response_data}")
            return AnswerResponse(**response_data)
        except Exception as e:
            print(f"DEBUG: Error creating response: {e}")
            raise
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/next-spec4", response_model=CardResponse)
async def get_next_card_spec4(
    user_id: Optional[str] = None,
    exclude_card_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get next card for study using Spec4 intelligent selection algorithm
    """
    try:
        user_id = _resolve_request_user_id(db, user_id)

        # Initialize Spec4 card selection service
        card_service = CardSelectionService(db)

        # Get next card using Spec4 algorithm
        print(f"DEBUG: Getting card for user_id={user_id}, exclude_card_id={exclude_card_id}")
        card_context = card_service.get_next_card_for_user(user_id, exclude_card_id=exclude_card_id)
        print(f"DEBUG: Card context returned: {card_context}")

        if not card_context:
            print(f"DEBUG: CardSelectionService returned None for user {user_id}")
            print(f"DEBUG: This usually means no words in the unlocked prefix or database issues")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "No cards available",
                    "message": "No cards available for study at this time"
                }
            )

        memory_stage = _get_card_memory_stage(db, user_id, card_context["card_id"])

        return CardResponse(
            card_id=card_context["card_id"],  # CRITICAL: Real Card.id from database
            word_id=card_context["word_id"],
            sentence_id=card_context["sentence_id"],  # Spec4: sentence variety tracking
            word=card_context["word"],
            sentence=card_context["sentence"],
            gap=card_context["gap"],
            sentence_translation=card_context["sentence_translation"],
            grammar_hint=card_context["grammar_hint"],
            memory_stage=memory_stage,  # Real SM-2 status from UserCardState or NEW
            is_new=card_context["is_new"],
            audio_word_url=card_context["audio_word_url"],
            audio_sentence_url=card_context["audio_sentence_url"],
            sentence_source=card_context.get("sentence_source")
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_next_card_spec4: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "message": str(e)}
        )


@router.get("/next-lingvist", response_model=LingvistCardResponse)
async def get_next_card_lingvist(
    user_id: Optional[str] = None,
    exclude_card_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get next card for Lingvist mode training

    Lingvist mode: Inline cloze with progressive hints, audio after correct,
    and PT-BR translations. Reuses Spec4 selection algorithm but with
    enriched payload.

    Mix: 20% new / 80% review (more conservative than Spec4).

    Auto-translation: If LINGVIST_TRANSLATIONS_AUTOFILL is enabled and
    translations are missing, generates them on-demand using Argos Translate.
    """
    try:
        user_id = _resolve_request_user_id(db, user_id)

        # Initialize Spec4 card selection service
        card_service = CardSelectionService(db)

        # Get next card using Spec4 algorithm with Lingvist mix (20% new / 80% review)
        # Override target_new_share to 0.2 (20% new words)
        original_target_new = None
        user = db.query(User).filter(User.id == user_id).first()

        if user and hasattr(user, 'target_new_words'):
            original_target_new = user.target_new_words

        # Temporarily set target_new_words to enforce 20% new / 80% review mix
        # Lingvist mode is more conservative than Spec4
        if user:
            user.target_new_words = 20  # 20% new words

        try:
            card_context = card_service.get_next_card_for_user(user_id, exclude_card_id=exclude_card_id)
        finally:
            # Restore original target_new_words
            if user and original_target_new is not None:
                user.target_new_words = original_target_new

        if not card_context:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "No cards available", "message": "No cards available for study at this time"}
            )

        response = _build_lingvist_card_response(db, user_id, user, card_context)

        # Commit database changes (including autofilled translations)
        db.commit()

        return response

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_next_card_lingvist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "message": str(e)}
        )


def _build_grammar_tag_pt(word: 'Word') -> str:
    """Build PT-BR grammar tag from word.part_of_speech and word.features"""
    return _build_grammar_tag_pt_service(word)


def _extract_word_translation(word: 'Word') -> Optional[str]:
    """Extract PT-BR translation from Word.features.pt_translation

    Returns None if translation is missing, None, empty string, or whitespace.
    """
    return _extract_word_translation_service(word)


def _get_micro_progress(db: 'Session', user_id: str, user: 'User') -> 'MicroProgress':
    """Calculate micro-progress from UserSessionStats and User for TODAY"""
    return _get_micro_progress_service(db, user_id, user)


@router.get("/health")
async def health_check():
    """Health check for cards service"""
    return {"status": "healthy", "service": "cards-api"}
