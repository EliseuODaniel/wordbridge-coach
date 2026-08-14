"""Card selection service implementing Spec4 intelligent mixing"""

from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session

from app.models import (
    User, Word, Sentence, Card, UserFrequencyProgress, UserCardState, Language
)
from app.services.card_selection_payload_service import (
    build_card_context_payload as _build_card_context_payload_service,
)
from app.services.card_selection_policy_service import (
    calculate_adaptive_new_share as _calculate_adaptive_new_share_service,
    should_try_new_card_lingvist as _should_try_new_card_lingvist_service,
    should_try_new_card_spec4 as _should_try_new_card_spec4_service,
)
from app.services.card_selection_query_service import (
    count_reviews_due as _count_reviews_due_service,
    get_due_review_candidates as _get_due_review_candidates_service,
    get_recent_correct_word_ids as _get_recent_correct_word_ids_service,
)
from app.services.card_selection_mode_service import (
    select_next_card_lingvist as _select_next_card_lingvist_service,
    select_next_card_spec4 as _select_next_card_spec4_service,
)
from app.services.card_selection_resolution_service import (
    build_selected_card as _build_selected_card_service,
    get_any_eligible_card as _get_any_eligible_card_service,
    get_due_relearn_card as _get_due_relearn_card_service,
    get_random_new_card as _get_random_new_card_service,
    get_review_card as _get_review_card_service,
)
from app.services.vocabulary_progression import VocabularyProgressionService


class CardSelectionService:
    """Service for intelligent card selection with new/review mixing"""

    def __init__(self, db: Session):
        self.db = db
        self.progression_service = VocabularyProgressionService(db)
        self.user_model = User

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

    def _build_selected_card(
        self,
        user_id: str,
        word: Word,
        *,
        is_new: bool,
        exclude_card_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Proxy card payload assembly for extracted resolution services."""
        return _build_selected_card_service(
            self,
            user_id,
            word,
            is_new=is_new,
            exclude_card_id=exclude_card_id,
        )

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
        """Run the Spec4 mode orchestration."""
        return _select_next_card_spec4_service(self, user_id, exclude_card_id)

    def _get_next_card_lingvist(self, user_id: str, exclude_card_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Run the Lingvist mode orchestration."""
        return _select_next_card_lingvist_service(self, user_id, exclude_card_id)

    def _get_random_new_card(
        self,
        user_id: str,
        progress: UserFrequencyProgress,
        exclude_card_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Proxy new-card selection for extracted resolution services."""
        return _get_random_new_card_service(self, user_id, progress, exclude_card_id)

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

    def _get_review_card(
        self,
        user_id: str,
        review_candidates,
        exclude_card_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Proxy review-card selection for extracted resolution services."""
        return _get_review_card_service(self, user_id, review_candidates, exclude_card_id)

    def _get_any_eligible_card(
        self,
        user_id: str,
        progress: UserFrequencyProgress,
        exclude_card_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Proxy fallback-card selection for extracted resolution services."""
        return _get_any_eligible_card_service(self, user_id, progress, exclude_card_id)

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

    def _get_due_relearn_card(
        self,
        user_id: str,
        exclude_card_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Proxy relearn-card lookup for extracted resolution services."""
        return _get_due_relearn_card_service(self, user_id, exclude_card_id)

    def _count_reviews_due(self, user_id: str) -> int:
        """Count cards due for review (excluding new cards)"""
        return _count_reviews_due_service(self.db, user_id)

    def _should_try_new_card_spec4(self, new_share: float) -> bool:
        """Proxy Spec4 new-card policy for extracted mode services."""
        return _should_try_new_card_spec4_service(new_share)

    def _should_try_new_card_lingvist(
        self,
        *,
        current_new_share: float,
        adaptive_new_share: float,
        reviews_due_count: int,
    ) -> bool:
        """Proxy Lingvist adaptive new-card policy for extracted mode services."""
        return _should_try_new_card_lingvist_service(
            current_new_share=current_new_share,
            adaptive_new_share=adaptive_new_share,
            reviews_due_count=reviews_due_count,
        )

    def _calculate_adaptive_new_share(self, user: User) -> float:
        """Calculate adaptive new card share based on user accuracy"""
        reviews_due_count = self._count_reviews_due(user.id)
        return _calculate_adaptive_new_share_service(
            user.accuracy_last_20,
            reviews_due_count,
        )
