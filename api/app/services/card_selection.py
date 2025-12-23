"""Card selection service implementing Spec4 intelligent mixing"""

from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_
from datetime import datetime, timedelta
import random

from app.models import (
    User, Word, Sentence, Card, UserFrequencyProgress, UserSessionStats, ReviewEvent,
    UserCardState, WordFrequency, Language
)
from app.services.vocabulary_progression import VocabularyProgressionService


class CardSelectionService:
    """Service for intelligent card selection with new/review mixing"""

    def __init__(self, db: Session):
        self.db = db
        self.progression_service = VocabularyProgressionService(db)

    def _get_recent_word_ids(self, user_id: str, days: int = 7, limit: int = 50) -> set:
        """
        Get distinct word IDs seen by user in recent days.

        Args:
            user_id: User ID
            days: Look back period in days (default 7)
            limit: Maximum number of word IDs to return (default 50)

        Returns:
            Set of word IDs recently seen
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Get distinct word IDs from recent review events
        # Explicitly specify FROM ReviewEvent and JOIN with Card and Sentence
        recent_words = self.db.query(ReviewEvent)\
            .join(Card, ReviewEvent.card_id == Card.id)\
            .join(Sentence, Card.sentence_id == Sentence.id)\
            .filter(
                and_(
                    ReviewEvent.user_id == user_id,
                    ReviewEvent.created_at >= cutoff_date
                )
            )\
            .distinct(Sentence.word_id)\
            .limit(limit)\
            .all()

        # Extract word IDs from ReviewEvent->Sentence->word_id
        return {review_event.card.sentence.word_id for review_event in recent_words if review_event.card and review_event.card.sentence}

    def get_next_card_for_user(self, user_id: str, exclude_card_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get next card for user implementing Spec4's getNextCardForUser algorithm
        Mixes new words (25%) with reviews (75%) and reinforces errors

        NEVER returns 404 if DB is seeded - always tries to find an eligible card.

        Args:
            user_id: User identifier
            exclude_card_id: Optional card ID to exclude from selection (avoids immediate repetition)
        """
        # Get user progress and session stats
        progress = self.progression_service.get_or_create_user_progress(user_id)
        session_stats = self.progression_service.get_session_stats_for_today(user_id)

        # Calculate new share for today
        new_share = 0
        if session_stats.cards_shown > 0:
            new_share = session_stats.new_cards_shown / session_stats.cards_shown

        # Get review candidates (only from unlocked prefix)
        review_candidates = self.get_due_review_words(
            self.db, user_id, max_count=50, exclude_card_id=exclude_card_id
        )

        # Check if we can introduce a new word
        from app.services.vocabulary_progression import TARGET_NEW_SHARE
        can_introduce_new = (
            new_share < TARGET_NEW_SHARE
        )

        if can_introduce_new:
            # T1: Try new card (random selection)
            new_card = self._get_random_new_card(user_id, progress, exclude_card_id)
            if new_card:
                return new_card

        # T2: Try review card
        if review_candidates:
            review_card = self._get_review_card(user_id, review_candidates, exclude_card_id)
            if review_card:
                return review_card

        # T3: Fallback - try ANY eligible card (even if not "due" yet)
        fallback_card = self._get_any_eligible_card(user_id, progress, exclude_card_id)
        if fallback_card:
            return fallback_card

        # T4: Only return None if DB is truly empty
        print(f"DEBUG: No cards available for user {user_id} - DB may be empty")
        return None

    def _get_random_new_card(self, user_id: str, progress: UserFrequencyProgress,
                             exclude_card_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get a random new card within the user's goal/window

        Args:
            user_id: User identifier
            progress: User's frequency progress
            exclude_card_id: Optional card ID to exclude (soft preference)
        """
        # Get user's target language
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.target_language_id:
            return None

        target_lang = self.db.query(Language).filter(Language.id == user.target_language_id).first()
        if not target_lang:
            return None

        max_rank = min(progress.current_window_end_rank, progress.word_goal_rank)

        # Build query for eligible words
        query = self.db.query(Word).join(WordFrequency,
            and_(
                func.lower(Word.lemma) == func.lower(WordFrequency.word),
                WordFrequency.language_code == target_lang.code,
                WordFrequency.rank <= max_rank
            )
        )

        # Soft exclusion: prefer other words if possible
        excluded_word_id = None
        if exclude_card_id:
            excluded_card = self.db.query(Card).filter(Card.id == exclude_card_id).first()
            if excluded_card and excluded_card.sentence:
                excluded_word_id = excluded_card.sentence.word_id

        # Anti-repetition: get recently seen words (last 7 days, max 50)
        recent_word_ids = self._get_recent_word_ids(user_id, days=7, limit=50)

        # Build exclusions: current card + recent words
        exclusions = set()
        if excluded_word_id:
            exclusions.add(excluded_word_id)

        # Try without excluded/recent words first
        words_without_recent = query.filter(
            ~Word.id.in_(exclusions | recent_word_ids)
        ).all()

        # Use words without recent if we have enough alternatives (threshold: 10)
        if len(words_without_recent) >= 10:
            word = random.choice(words_without_recent)
        else:
            # Fallback: include recent words (but still exclude current card)
            if excluded_word_id:
                words_without_current = query.filter(Word.id != excluded_word_id).all()
                if words_without_current:
                    word = random.choice(words_without_current)
                else:
                    # Last resort: include current card (will show different sentence)
                    words = query.all()
                    if not words:
                        return None
                    word = random.choice(words)
            else:
                words = query.all()
                if not words:
                    return None
                word = random.choice(words)

        # Get sentence (variety K=10 handled by get_sentence_for_word)
        sentence = self.progression_service.get_sentence_for_word(user_id, word.id, exclude_card_id)
        card_context = self._build_card_context(user_id, word, sentence, is_new=True)

        # Record the new card in session stats
        self.progression_service.record_card_shown(user_id, is_new_card=True)

        return card_context

    def get_due_review_words(self, db: Session, user_id: str, max_count: int = 50,
                            exclude_card_id: Optional[str] = None) -> List[Tuple[Word, UserCardState]]:
        """Get words due for review with proper gating

        Args:
            db: Database session
            user_id: User identifier
            max_count: Maximum number of candidates to return
            exclude_card_id: Optional specific card to exclude (by Card.id, NOT Word.id)
        """
        from sqlalchemy import desc
        from app.models.user_card_state import MemoryStage

        # Get user's progress for gating
        progress = self.progression_service.get_or_create_user_progress(user_id)
        user = db.query(User).filter(User.id == user_id).first()

        if not user or not user.target_language_id:
            return []

        # Get user's target language code for WordFrequency join
        from app.models import Language
        target_lang = db.query(Language).filter(Language.id == user.target_language_id).first()
        if not target_lang:
            return []
        target_lang_code = target_lang.code

        # Build query for due cards
        # Note: We filter by Card.id in exclude_card_id, NOT by Word.id
        query = db.query(UserCardState, Word).join(
            Card, UserCardState.card_id == Card.id
        ).join(
            Sentence, Card.sentence_id == Sentence.id
        ).join(
            Word, Sentence.word_id == Word.id
        ).filter(
            UserCardState.user_id == user_id,
            Word.language_id == user.target_language_id,
            UserCardState.next_review_at <= datetime.utcnow(),
            UserCardState.status.in_([MemoryStage.LEARNING, MemoryStage.REVIEW, MemoryStage.MATURE])
        )

        # Apply max_contiguous_mastered_rank gating (prefix)
        if progress.max_contiguous_mastered_rank > 0:
            # Allow words within mastered prefix + reasonable range for sparse data
            max_allowed_rank = progress.max_contiguous_mastered_rank + 100  # Generous range
            query = query.join(WordFrequency,
                and_(
                    func.lower(Word.lemma) == func.lower(WordFrequency.word),
                    WordFrequency.language_code == target_lang_code  # Use user's target language
                )
            ).filter(WordFrequency.rank <= max_allowed_rank)

        # Exclude specific card if provided (by Card.id, NOT Word.id)
        if exclude_card_id:
            query = query.filter(UserCardState.card_id != exclude_card_id)

        # Order by priority (errors first, then interval, then random)
        # For now, simple ordering by next_review_at
        query = query.order_by(UserCardState.next_review_at).limit(max_count)

        results = query.all()

        # Convert to tuples of (Word, UserCardState)
        return [(word, ucs) for ucs, word in results]

    def _get_review_card(self, user_id: str, review_candidates, exclude_card_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get a review card from candidates

        Args:
            user_id: User identifier
            review_candidates: Available review candidates (tuples of Word, UserCardState)
            exclude_card_id: Optional card ID to exclude (already filtered in get_due_review_words)
        """
        if not review_candidates:
            return None

        # Pick best review word (favoring problematic words)
        review_words = [candidate[0] for candidate in review_candidates]

        word = self.progression_service.pick_best_review_word(user_id, review_words)
        sentence = self.progression_service.get_sentence_for_word(user_id, word.id)
        card_context = self._build_card_context(user_id, word, sentence, is_new=False)

        # Record the review card in session stats
        self.progression_service.record_card_shown(user_id, is_new_card=False)

        return card_context

    def _get_any_eligible_card(self, user_id: str, progress: UserFrequencyProgress,
                               exclude_card_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Fallback: Get ANY eligible card (even if not "due" yet)

        This is the final fallback to prevent 404 errors in seeded environments.

        Args:
            user_id: User identifier
            progress: User's frequency progress
            exclude_card_id: Optional card ID to exclude
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.target_language_id:
            return None

        target_lang = self.db.query(Language).filter(Language.id == user.target_language_id).first()
        if not target_lang:
            return None

        max_rank = min(progress.current_window_end_rank, progress.word_goal_rank)

        # Query ANY active card within constraints
        query = self.db.query(Card).join(Sentence).join(Word).filter(
            Card.is_active == True,
            Word.language_id == user.target_language_id
        ).join(WordFrequency,
            and_(
                func.lower(Word.lemma) == func.lower(WordFrequency.word),
                WordFrequency.language_code == target_lang.code,
                WordFrequency.rank <= max_rank
            )
        )

        # Exclude specific card if provided
        if exclude_card_id:
            query = query.filter(Card.id != exclude_card_id)

        # Random selection to avoid repetition
        card = query.order_by(func.random()).first()

        if not card:
            return None

        # Get word and build context
        word = card.sentence.word
        sentence = self.progression_service.get_sentence_for_word(user_id, word.id, exclude_card_id)

        # Determine if this is new or review based on UserCardState
        ucs = self.db.query(UserCardState).filter(
            UserCardState.user_id == user_id,
            UserCardState.card_id == card.id
        ).first()

        is_new = (ucs is None or ucs.status.value == 'NEW')

        card_context = self._build_card_context(user_id, word, sentence, is_new=is_new)

        # Record in session stats
        self.progression_service.record_card_shown(user_id, is_new_card=is_new)

        return card_context

    def _get_word_by_rank(self, rank: int, user_id: str = None, exclude_card_id: Optional[str] = None) -> Optional[Word]:
        """Get word by frequency rank (DEPRECATED - kept for compatibility)

        NOTE: This method is kept for backwards compatibility but is no longer used
        in the main flow. Use _get_random_new_card instead.
        """
        from app.models import WordFrequency
        from app.models.user_frequency_progress import UserFrequencyProgress
        from app.models import Language

        # Get user's target language for proper filtering
        target_language_code = "en"  # Default fallback
        max_allowed_rank = None

        if user_id:
            # Get user's language and gating constraints
            user = self.db.query(User).filter(User.id == user_id).first()
            if user and user.target_language_id:
                target_lang = self.db.query(Language).filter(Language.id == user.target_language_id).first()
                if target_lang:
                    target_language_code = target_lang.code

            progress = self.db.query(UserFrequencyProgress).filter(UserFrequencyProgress.user_id == user_id).first()
            if progress:
                max_allowed_rank = min(progress.current_window_end_rank, progress.word_goal_rank)
                max_unlocked_rank = progress.max_contiguous_mastered_rank

                # Critical gating: only allow access to words within unlocked prefix
                # For new users (max_contiguous_mastered_rank = 0), allow access to first available word
                # For users with progress, allow access to words within reasonable range of mastered prefix
                if max_unlocked_rank > 0:
                    # Allow access to words within the mastered prefix AND a reasonable range for sparse data
                    # This handles cases where we have sparse data (e.g., words at ranks 38, 49, 50, etc.)
                    if rank > max_unlocked_rank + 50:  # Allow up to 50 ranks ahead for sparse data
                        print(f"DEBUG: Gating blocked rank {rank} (max_unlocked_rank={max_unlocked_rank}, range limit=50)")
                        return None

        # Try exact rank match first (using lemma like Insights API for consistency)
        query = self.db.query(Word).join(WordFrequency,
            and_(
                func.lower(Word.lemma) == func.lower(WordFrequency.word),
                WordFrequency.language_code == target_language_code
            )
        ).filter(
            WordFrequency.rank == rank
        )

        word = query.first()

        if word:
            # Verificação adicional: garantir que o rank corresponde ao esperado
            # Isso previne problemas de dados inconsistentes no banco
            if user_id and max_allowed_rank and rank > max_allowed_rank:
                print(f"DEBUG: Rank {rank} > max_allowed_rank {max_allowed_rank}, violação de gating!")
                return None

            # Check if this is the excluded word (convert exclude_card_id to word_id)
            if exclude_card_id:
                from app.models import Card as CardModel
                excluded_card = self.db.query(CardModel).filter(CardModel.id == exclude_card_id).first()
                if excluded_card and excluded_card.sentence and excluded_card.sentence.word_id:
                    if str(word.id) == str(excluded_card.sentence.word_id):
                        print(f"DEBUG: Excluded word {word.id} found (from card {exclude_card_id}), returning None")
                        return None

            return word

        # If exact rank not found, try deterministic fallback within allowed window
        if user_id and max_allowed_rank:
            # Find the next available rank within the window
            next_available = self.db.query(WordFrequency).filter(
                and_(
                    WordFrequency.rank >= rank,
                    WordFrequency.rank <= max_allowed_rank,
                    WordFrequency.language_code == target_language_code
                )
            ).order_by(WordFrequency.rank).first()

            if next_available:
                # Find corresponding word (using lemma for consistency)
                word = self.db.query(Word).join(WordFrequency,
                    and_(
                        func.lower(Word.lemma) == func.lower(WordFrequency.word),
                        WordFrequency.language_code == target_language_code
                    )
                ).filter(
                    WordFrequency.rank == next_available.rank
                ).first()
                return word

        # No suitable word found within constraints
        return None

    def _build_card_context(
        self,
        user_id: str,
        word: Word,
        sentence: Optional[Sentence],
        is_new: bool
    ) -> Dict[str, Any]:
        """Build card context dictionary for API response

        Args:
            user_id: User identifier (needed for target language)
            word: The word being studied
            sentence: The sentence for this card
            is_new: Whether this is a new card or review

        Returns:
            Dictionary with card data for API response
        """
        from app.models import Card, User, Language

        # Find or create card for this sentence
        card = self.db.query(Card).filter(
            Card.sentence_id == sentence.id,
            Card.is_active == True
        ).first()

        if not card:
            # Auto-create Card on-the-fly (Spec4 requirement - never return None)
            print(f"INFO: Auto-creating card for sentence {sentence.id}, word {word.text}")

            from app.models import Deck

            # Find or create default deck for this language
            deck = self.db.query(Deck).filter(
                Deck.language_id == word.language_id,
                Deck.is_active == True
            ).first()

            if not deck:
                # Create default deck if none exists
                deck = Deck(
                    name=f"Default {word.language_id}",
                    language_id=word.language_id,
                    difficulty_level=1,
                    description="Auto-created default deck",
                    is_active=True
                )
                self.db.add(deck)
                self.db.flush()

            # Calculate gap positions from sentence text
            text = sentence.text or ""
            gap_start = text.find("___")
            gap_end = gap_start + 3 if gap_start >= 0 else len(text)

            # Create card
            card = Card(
                sentence_id=sentence.id,
                deck_id=deck.id,
                grammar_hint="",  # Can be enhanced later with word.part_of_speech
                gap_start=gap_start,
                gap_end=gap_end,
                is_active=True
            )
            self.db.add(card)
            self.db.flush()

            print(f"INFO: Created card {card.id} for sentence {sentence.id}")

        # Get user's target language code for audio URLs
        user = self.db.query(User).filter(User.id == user_id).first()
        lang_code = 'en'  # Default fallback
        if user and user.target_language_id:
            target_lang = self.db.query(Language).filter(Language.id == user.target_language_id).first()
            if target_lang:
                lang_code = target_lang.code

        # Build audio URLs using TTS service endpoints (via nginx proxy)
        from urllib.parse import quote

        # Word audio URL
        word_text_encoded = quote(word.text or "")
        audio_word_url = f"/api/tts/word/{card.id}?text={word_text_encoded}&lang={lang_code}"

        # Sentence audio URL - replace ___ with actual word
        sentence_with_gap = sentence.text or ""
        sentence_with_word = sentence_with_gap.replace("___", word.text, 1)
        sentence_text_encoded = quote(sentence_with_word)
        audio_sentence_url = f"/api/tts/sentence/{card.id}?text={sentence_text_encoded}&lang={lang_code}"

        return {
            "card_id": str(card.id),
            "word_id": str(word.id),
            "sentence_id": str(sentence.id),
            "word": word.text,
            "sentence": sentence.text or "",
            "gap": {
                "start": card.gap_start or 0,
                "end": card.gap_end or 0
            },
            "sentence_translation": sentence.translation or "",
            "grammar_hint": card.grammar_hint or "",
            "memory_stage": "NEW" if is_new else "REVIEW",
            "is_new": is_new,
            "audio_word_url": audio_word_url,
            "audio_sentence_url": audio_sentence_url
        }

    def record_answer(self, user_id: str, word_id: str, sentence_id: str,
                     was_correct: bool, response_time_ms: int, quality: int) -> Dict[str, Any]:
        """Record answer and update Spec4 vocabulary progression

        Args:
            user_id: User identifier
            word_id: Word identifier (from card.sentence.word_id)
            sentence_id: Sentence identifier
            was_correct: Whether answer was correct
            response_time_ms: Response time in milliseconds
            quality: SM-2 quality score (0-5)

        Returns:
            Dictionary with result
        """
        # Update vocabulary progression only for correct answers (Spec4)
        if was_correct:
            try:
                # Get user's target language
                from app.models.user import User
                user = self.db.query(User).filter(User.id == user_id).first()
                if not user or not user.target_language_obj:
                    print(f"DEBUG: No user or target_language found for user_id={user_id}")
                    return {"success": False, "error": "User not found"}

                # Get language code from target_language_obj
                target_lang_code = user.target_language_obj.code

                # Get word rank from WordFrequency
                from app.models.word import Word
                from app.models.word_frequency import WordFrequency
                from sqlalchemy import func

                word = self.db.query(Word).filter(Word.id == word_id).first()
                if not word:
                    print(f"DEBUG: Word not found for word_id={word_id}")
                    return {"success": False, "error": "Word not found"}

                # Match WordFrequency by word (case-insensitive)
                wf = self.db.query(WordFrequency).filter(
                    func.lower(WordFrequency.word) == func.lower(word.lemma),
                    WordFrequency.language_code == target_lang_code
                ).first()

                if not wf:
                    print(f"DEBUG: WordFrequency not found for word={word.lemma}, lang={target_lang_code}")
                    return {"success": False, "error": "WordFrequency not found"}

                # Update contiguous mastered rank
                print(f"DEBUG: Updating progression for user={user_id}, rank={wf.rank}")
                self.progression_service.update_contiguous_mastered_rank(user_id, wf.rank)
                print(f"DEBUG: Updated max_contiguous_mastered_rank for user={user_id} to rank {wf.rank}")
                return {"success": True, "rank": wf.rank}

            except Exception as e:
                print(f"DEBUG: Error updating progression: {e}")
                import traceback
                traceback.print_exc()
                return {"success": False, "error": str(e)}

        return {"success": True, "message": "Incorrect answer, progression not updated"}
