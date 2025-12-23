"""Card endpoints for FillTheWord API"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime, timedelta
import uuid

from app.core.database import get_db
from app.core.config import settings
from app.schemas.card import CardResponse, AnswerRequest, AnswerResponse, ErrorResponse
from app.services.sm2 import SM2Algorithm
from app.services.card_selection import CardSelectionService
from app.models import Language, Word, Sentence, Card, Deck, User, UserCardState, ReviewEvent
from app.models.user_card_state import MemoryStage
from app.models.user_theme_stats import UserThemeStats
from app.models.word_theme_mapping import WordThemeMapping

router = APIRouter()

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
                next_review_at=datetime.utcnow(),
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

        # Get demo user if user_id not provided
        if not user_id:
            demo_user = db.query(User).filter(User.username == "demo").first()
            if not demo_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"error": "Demo user not found", "message": "User setup required"}
                )
            user_id = demo_user.id

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
                Card.id.in_(cards_seen_today),
                ~Card.id.in_(cards_seen_before_today)
            )
        ).count() or 0

        # Find next card using SM-2 priority logic with daily limit
        # Priority 1: Due cards for review
        now = datetime.utcnow()
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
        print(f"DEBUG: Calculating quality for response_time_ms={answer_data.response_time_ms}")
        try:
            quality = SM2Algorithm.calculate_quality_from_response(
                was_correct=is_correct,
                response_time_ms=answer_data.response_time_ms,
                hints_used=0,  # TODO: Track hints usage
                attempts=1     # TODO: Track attempts
            )
            print(f"DEBUG: SM2 quality calculated: {quality}")
        except Exception as e:
            print(f"DEBUG: Error calculating SM2 quality: {e}")
            raise

        # Get or create UserCardState for demo user
        if not user_id:
            demo_user = db.query(User).filter(User.username == "demo").first()
            if not demo_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"error": "Demo user not found", "message": "User setup required"}
                )
            user_id = demo_user.id

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
                next_review_at=datetime.utcnow(),
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
            hints_used=0,
            previous_easiness=previous_easiness,
            new_easiness=sm2_result["easiness_factor"],
            previous_interval=previous_interval,
            new_interval=sm2_result["interval_days"]
        )
        db.add(review_event)
        print(f"DEBUG: ReviewEvent created with sentence_id={sentence_id}")

        # Update or create UserDailyStats
        from app.models.user_daily_stats import UserDailyStats

        today = datetime.utcnow().date()
        daily_stats = db.query(UserDailyStats).filter(
            UserDailyStats.user_id == user_id,
            UserDailyStats.date == today
        ).first()

        if not daily_stats:
            daily_stats = UserDailyStats(
                user_id=user_id,
                date=today,
                cards_answered=0,
                new_words_learned=0,
                reviews_done=0,
                accuracy=0.0
            )
            db.add(daily_stats)
            db.flush()  # Flush to ensure it's persisted before updating

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

        print(f"DEBUG: UserCardState updated successfully")

        # Update UserThemeStats for all themes associated with this word
        word_id = card.sentence.word_id
        theme_mappings = db.query(WordThemeMapping.theme_id).filter(
            and_(
                WordThemeMapping.word_id == word_id,
                WordThemeMapping.is_active == True
            )
        ).all()

        for theme_mapping in theme_mappings:
            theme_id = theme_mapping[0]  # Extract theme_id from tuple

            # Get or create UserThemeStats
            theme_stats = db.query(UserThemeStats).filter(
                and_(
                    UserThemeStats.user_id == user_id,
                    UserThemeStats.theme_id == theme_id
                )
            ).first()

            if not theme_stats:
                # Create new UserThemeStats
                theme_stats = UserThemeStats(
                    user_id=user_id,
                    theme_id=theme_id,
                    attempts=0,
                    correct=0,
                    accuracy=0.0,
                    avg_response_time_ms=0.0
                )
                db.add(theme_stats)
                db.flush()  # Flush to ensure it's persisted before updating

            # Add attempt using model's method
            theme_stats.add_attempt(
                was_correct=is_correct,
                response_time_ms=answer_data.response_time_ms
            )
            print(f"DEBUG: Updated UserThemeStats for theme_id={theme_id}, attempts={theme_stats.attempts}, accuracy={theme_stats.accuracy:.3f}")

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
        # Get demo user if user_id not provided
        if not user_id:
            demo_user = db.query(User).filter(User.username == "demo").first()
            if not demo_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"error": "Demo user not found", "message": "User setup required"}
                )
            user_id = demo_user.id

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

        # Get target language code for TTS
        user = db.query(User).filter(User.id == user_id).first()
        target_lang_code = "en"  # Default
        if user and user.target_language_id:
            target_lang = db.query(Language).filter(Language.id == user.target_language_id).first()
            if target_lang:
                target_lang_code = target_lang.code

        # Determine memory_stage from UserCardState (if exists)
        card_state = db.query(UserCardState).filter(
            and_(
                UserCardState.user_id == user_id,
                UserCardState.card_id == card_context["card_id"]
            )
        ).first()

        if card_state:
            # Use real SM-2 status from UserCardState
            memory_stage = card_state.status.value  # Convert enum to string (uppercase)
        else:
            # No state yet, it's a new card
            memory_stage = "NEW"

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
            audio_sentence_url=card_context["audio_sentence_url"]
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_next_card_spec4: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "message": str(e)}
        )


@router.get("/health")
async def health_check():
    """Health check for cards service"""
    return {"status": "healthy", "service": "cards-api"}
