"""Mode-specific orchestration extracted from CardSelectionService."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

from app.services.card_selection_policy_service import calculate_session_new_share

if TYPE_CHECKING:
    from app.services.card_selection import CardSelectionService

logger = logging.getLogger(__name__)


def select_next_card_spec4(
    selector: 'CardSelectionService',
    user_id: str,
    exclude_card_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Run the Spec4 review/new-card selection flow."""
    progress = selector.progression_service.get_or_create_user_progress(user_id)
    session_stats = selector.progression_service.get_session_stats_for_today(user_id)
    new_share = calculate_session_new_share(
        session_stats.cards_shown,
        session_stats.new_cards_shown,
    )

    review_candidates = selector.get_due_review_words(
        selector.db,
        user_id,
        max_count=50,
        exclude_card_id=exclude_card_id,
    )

    if selector._should_try_new_card_spec4(new_share):
        new_card = selector._get_random_new_card(user_id, progress, exclude_card_id)
        if new_card:
            return new_card

    if review_candidates:
        review_card = selector._get_review_card(user_id, review_candidates, exclude_card_id)
        if review_card:
            return review_card

    fallback_card = selector._get_any_eligible_card(user_id, progress, exclude_card_id)
    if fallback_card:
        return fallback_card

    logger.debug("No cards available for user %s - DB may be empty", user_id)
    return None


def select_next_card_lingvist(
    selector: 'CardSelectionService',
    user_id: str,
    exclude_card_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Run the Lingvist-specific relearn/adaptive share flow."""
    relearn_card = selector._get_due_relearn_card(user_id, exclude_card_id)
    if relearn_card:
        return relearn_card

    user = selector.db.query(selector.user_model).filter(selector.user_model.id == user_id).first()
    if not user:
        return None

    new_share = selector._calculate_adaptive_new_share(user)
    reviews_due_count = selector._count_reviews_due(user_id)

    can_introduce_new = reviews_due_count < 50 and new_share > 0
    if can_introduce_new:
        progress = selector.progression_service.get_or_create_user_progress(user_id)
        session_stats = selector.progression_service.get_session_stats_for_today(user_id)
        current_new_share = calculate_session_new_share(
            session_stats.cards_shown,
            session_stats.new_cards_shown,
        )

        if selector._should_try_new_card_lingvist(
            current_new_share=current_new_share,
            adaptive_new_share=new_share,
            reviews_due_count=reviews_due_count,
        ):
            new_card = selector._get_random_new_card(user_id, progress, exclude_card_id)
            if new_card:
                return new_card

    review_candidates = selector.get_due_review_words(
        selector.db,
        user_id,
        max_count=50,
        exclude_card_id=exclude_card_id,
    )
    if review_candidates:
        review_card = selector._get_review_card(user_id, review_candidates, exclude_card_id)
        if review_card:
            return review_card

    progress = selector.progression_service.get_or_create_user_progress(user_id)
    fallback_card = selector._get_any_eligible_card(user_id, progress, exclude_card_id)
    if fallback_card:
        return fallback_card

    logger.debug("No cards available for user %s - DB may be empty", user_id)
    return None
