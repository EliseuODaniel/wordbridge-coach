"""Card selection service implementing Spec4 intelligent mixing"""

from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_
from datetime import timedelta
import random

from app.models import (
    User, Word, Sentence, Card, UserFrequencyProgress, UserSessionStats, ReviewEvent,
    UserCardState, WordFrequency, Language
)
from app.core.time import utc_now
from app.services.card_selection_payload_service import (
    build_card_context_payload as _build_card_context_payload_service,
)
from app.services.card_selection_policy_service import (
    calculate_adaptive_new_share as _calculate_adaptive_new_share_service,
    calculate_session_new_share as _calculate_session_new_share_service,
    should_try_new_card_lingvist as _should_try_new_card_lingvist_service,
    should_try_new_card_spec4 as _should_try_new_card_spec4_service,
)
from app.services.card_selection_query_service import (
    count_reviews_due as _count_reviews_due_service,
    get_due_relearn_candidate as _get_due_relearn_candidate_service,
    get_due_review_candidates as _get_due_review_candidates_service,
    get_recent_correct_word_ids as _get_recent_correct_word_ids_service,
)
from app.services.card_selection_fallback_service import (
    find_any_eligible_card as _find_any_eligible_card_service,
    get_card_review_state as _get_card_review_state_service,
    get_word_by_rank as _get_word_by_rank_service,
)
from app.services.vocabulary_progression import VocabularyProgressionService


class CardSelectionService:
    """Service for intelligent card selection with new/review mixing"""

    def __init__(self, db: Session):
        self.db = db
        self.progression_service = VocabularyProgressionService(db)

    def _get_user_and_target_language(self, user_id: str) -> Tuple[Optional[User], Optional[Language]]:
        """Load user and target language together for card selection decisions."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.target_language_id:
            return user, None

        target_lang = self.db.query(Language).filter(Language.id == user.target_language_id).first()
        return user, target_lang

    def _get_excluded_word_id(self, exclude_card_id: Optional[str]) -> Optional[str]:
        """Resolve excluded card to its underlying word_id when available."""
        if not exclude_card_id:
            return None

        excluded_card = self.db.query(Card).filter(Card.id == exclude_card_id).first()
        if not excluded_card or not excluded_card.sentence:
            return None

        return excluded_card.sentence.word_id

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
        cutoff_date = utc_now() - timedelta(days=days)

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
        # Get user mode
        user_mode = self._get_user_mode(user_id)

        if user_mode == 'lingvist':
            return self._get_next_card_lingvist(user_id, exclude_card_id)
        else:
            return self._get_next_card_spec4(user_id, exclude_card_id)

    def _get_next_card_spec4(self, user_id: str, exclude_card_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Spec4 mode: Fixed 25% new / 75% review mix (original behavior)
        """
        # Get user progress and session stats
        progress = self.progression_service.get_or_create_user_progress(user_id)
        session_stats = self.progression_service.get_session_stats_for_today(user_id)

        # Calculate new share for today
        new_share = _calculate_session_new_share_service(
            session_stats.cards_shown,
            session_stats.new_cards_shown,
        )

        # Get review candidates (only from unlocked prefix)
        review_candidates = self.get_due_review_words(
            self.db, user_id, max_count=50, exclude_card_id=exclude_card_id
        )

        # Check if we can introduce a new word
        can_introduce_new = _should_try_new_card_spec4_service(new_share)

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

    def _get_next_card_lingvist(self, user_id: str, exclude_card_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Lingvist mode: Prioritize relearn queue, use adaptive new_share
        """
        # T1: Check relearn queue (highest priority)
        relearn_card = self._get_due_relearn_card(user_id, exclude_card_id)
        if relearn_card:
            return relearn_card

        # T2: Calculate adaptive new_share based on accuracy
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        new_share = self._calculate_adaptive_new_share(user)

        # Get review count for backlog check
        reviews_due_count = self._count_reviews_due(user_id)

        # T3: Try new card if below adaptive share and below threshold
        can_introduce_new = reviews_due_count < 50 and new_share > 0

        if can_introduce_new:
            progress = self.progression_service.get_or_create_user_progress(user_id)

            # Check current new share
            session_stats = self.progression_service.get_session_stats_for_today(user_id)
            current_new_share = _calculate_session_new_share_service(
                session_stats.cards_shown,
                session_stats.new_cards_shown,
            )

            if _should_try_new_card_lingvist_service(
                current_new_share=current_new_share,
                adaptive_new_share=new_share,
                reviews_due_count=reviews_due_count,
            ):
                new_card = self._get_random_new_card(user_id, progress, exclude_card_id)
                if new_card:
                    return new_card

        # T4: Try review card
        review_candidates = self.get_due_review_words(self.db, user_id, max_count=50, exclude_card_id=exclude_card_id)
        if review_candidates:
            review_card = self._get_review_card(user_id, review_candidates, exclude_card_id)
            if review_card:
                return review_card

        # T5: Fallback
        progress = self.progression_service.get_or_create_user_progress(user_id)
        fallback_card = self._get_any_eligible_card(user_id, progress, exclude_card_id)
        if fallback_card:
            return fallback_card

        # T6: Only return None if DB is truly empty
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
        user, target_lang = self._get_user_and_target_language(user_id)
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
        excluded_word_id = self._get_excluded_word_id(exclude_card_id)

        # Anti-repetition: get recently seen words answered CORRECTLY (last 7 days, max 50)
        recent_word_ids = self._get_recent_correct_word_ids(user_id, days=7, limit=50)

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
        progress = self.progression_service.get_or_create_user_progress(user_id)
        user, target_lang = self._get_user_and_target_language(user_id)
        if not target_lang:
            return []
        return _get_due_review_candidates_service(
            db,
            user_id=user_id,
            target_language_id=user.target_language_id,
            target_language_code=target_lang.code,
            max_contiguous_mastered_rank=progress.max_contiguous_mastered_rank,
            max_count=max_count,
            exclude_card_id=exclude_card_id,
        )

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
        user, target_lang = self._get_user_and_target_language(user_id)
        if not target_lang:
            return None

        max_rank = min(progress.current_window_end_rank, progress.word_goal_rank)
        card = _find_any_eligible_card_service(
            self.db,
            target_language_id=user.target_language_id,
            target_language_code=target_lang.code,
            max_rank=max_rank,
            user_id=user_id,
            exclude_card_id=exclude_card_id,
        )

        if not card:
            return None

        # Get word and build context
        word = card.sentence.word
        sentence = self.progression_service.get_sentence_for_word(user_id, word.id, exclude_card_id)

        # Determine if this is new or review based on UserCardState
        ucs = _get_card_review_state_service(
            self.db,
            user_id=user_id,
            card_id=card.id,
        )

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
        from app.models.user_frequency_progress import UserFrequencyProgress

        # Get user's target language for proper filtering
        target_language_code = "en"  # Default fallback
        max_allowed_rank = None

        if user_id:
            # Get user's language and gating constraints
            _, target_lang = self._get_user_and_target_language(user_id)
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

        return _get_word_by_rank_service(
            self.db,
            rank=rank,
            target_language_code=target_language_code,
            max_allowed_rank=max_allowed_rank,
            max_unlocked_rank=max_unlocked_rank if user_id else None,
            excluded_word_id=self._get_excluded_word_id(exclude_card_id),
        )

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
        return _build_card_context_payload_service(
            self.db,
            user_id=user_id,
            word=word,
            sentence=sentence,
            is_new=is_new,
        )

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

    def _get_user_mode(self, user_id: str) -> str:
        """Get user's learning mode ('spec4' or 'lingvist')"""
        user = self.db.query(User).filter(User.id == user_id).first()
        return user.mode if user else 'spec4'

    def _get_recent_correct_word_ids(self, user_id: str, days: int = 7, limit: int = 50) -> set:
        """
        Get distinct word IDs from CORRECT answers in recent days (anti-repetition fix).

        Only excludes words that were answered CORRECTLY, allowing wrong answers to repeat.

        Args:
            user_id: User ID
            days: Look back period in days (default 7)
            limit: Maximum number of word IDs to return (default 50)

        Returns:
            Set of word IDs recently answered correctly
        """
        return _get_recent_correct_word_ids_service(
            self.db,
            user_id=user_id,
            days=days,
            limit=limit,
        )

    def _get_due_relearn_card(self, user_id: str, exclude_card_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get next due relearn card (highest priority in Lingvist mode)"""
        result = _get_due_relearn_candidate_service(
            self.db,
            user_id=user_id,
            exclude_card_id=exclude_card_id,
        )

        if not result:
            return None

        ucs, word = result
        sentence = self.progression_service.get_sentence_for_word(user_id, word.id)
        card_context = self._build_card_context(user_id, word, sentence, is_new=False)

        # Record as review card
        self.progression_service.record_card_shown(user_id, is_new_card=False)

        return card_context

    def _count_reviews_due(self, user_id: str) -> int:
        """Count cards due for review (excluding new cards)"""
        return _count_reviews_due_service(self.db, user_id)

    def _calculate_adaptive_new_share(self, user: User) -> float:
        """Calculate adaptive new card share based on user accuracy"""
        reviews_due_count = self._count_reviews_due(user.id)
        return _calculate_adaptive_new_share_service(
            user.accuracy_last_20,
            reviews_due_count,
        )
