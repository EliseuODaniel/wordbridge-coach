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
from app.services.card_selection import CardSelectionService
from app.services.card_submission_service import submit_card_answer as _submit_card_answer_service
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
from app.services.card_response_service import (
    format_card_response as _format_card_response_service,
    resolve_request_user_id as _resolve_request_user_id_service,
)
from app.models import Language, Word, Sentence, Card, Deck, User, UserCardState, ReviewEvent
from app.models.user_card_state import MemoryStage

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
    return _resolve_request_user_id_service(db, user_id)


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
    return _format_card_response_service(card, memory_stage)


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
        return _submit_card_answer_service(
            db,
            card_id=card_id,
            answer_data=answer_data,
            user_id=user_id,
        )
        
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
