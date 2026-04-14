"""Card resolution helpers extracted from CardSelectionService."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy import and_, func

from app.models import Word, WordFrequency
from app.services.card_selection_fallback_service import (
    find_any_eligible_card as _find_any_eligible_card_service,
    get_card_review_state as _get_card_review_state_service,
)
from app.services.card_selection_query_service import (
    get_due_relearn_candidate as _get_due_relearn_candidate_service,
)

if TYPE_CHECKING:
    from app.models import UserFrequencyProgress
    from app.services.card_selection import CardSelectionService


def build_selected_card(
    selector: 'CardSelectionService',
    user_id: str,
    word: Word,
    *,
    is_new: bool,
    exclude_card_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Resolve sentence, build payload, and record the card in session stats."""
    sentence = selector.progression_service.get_sentence_for_word(
        user_id,
        word.id,
        exclude_card_id,
    )
    card_context = selector._build_card_context(user_id, word, sentence, is_new=is_new)
    selector.progression_service.record_card_shown(user_id, is_new_card=is_new)
    return card_context


def get_random_new_card(
    selector: 'CardSelectionService',
    user_id: str,
    progress: 'UserFrequencyProgress',
    exclude_card_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Get a random new card within the user's active window."""
    user, target_lang = selector._get_user_and_target_language(user_id)
    if not target_lang:
        return None

    max_rank = min(progress.current_window_end_rank, progress.word_goal_rank)

    query = selector.db.query(Word).join(
        WordFrequency,
        and_(
            func.lower(Word.lemma) == func.lower(WordFrequency.word),
            WordFrequency.language_code == target_lang.code,
            WordFrequency.rank <= max_rank,
        ),
    )

    excluded_word_id = selector._get_excluded_word_id(exclude_card_id)
    recent_word_ids = selector._get_recent_correct_word_ids(user_id, days=7, limit=50)

    exclusions = set(recent_word_ids)
    if excluded_word_id:
        exclusions.add(excluded_word_id)

    words_without_recent = query.filter(~Word.id.in_(exclusions)).all()

    if len(words_without_recent) >= 10:
        word = random.choice(words_without_recent)
    else:
        if excluded_word_id:
            words_without_current = query.filter(Word.id != excluded_word_id).all()
            if words_without_current:
                word = random.choice(words_without_current)
            else:
                words = query.all()
                if not words:
                    return None
                word = random.choice(words)
        else:
            words = query.all()
            if not words:
                return None
            word = random.choice(words)

    return build_selected_card(
        selector,
        user_id,
        word,
        is_new=True,
        exclude_card_id=exclude_card_id,
    )


def get_review_card(
    selector: 'CardSelectionService',
    user_id: str,
    review_candidates,
    exclude_card_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Pick the best review candidate and return its payload."""
    if not review_candidates:
        return None

    review_words = [candidate[0] for candidate in review_candidates]
    word = selector.progression_service.pick_best_review_word(user_id, review_words)
    return build_selected_card(
        selector,
        user_id,
        word,
        is_new=False,
        exclude_card_id=exclude_card_id,
    )


def get_any_eligible_card(
    selector: 'CardSelectionService',
    user_id: str,
    progress: 'UserFrequencyProgress',
    exclude_card_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Fallback to any eligible card to avoid empty seeded environments."""
    user, target_lang = selector._get_user_and_target_language(user_id)
    if not target_lang:
        return None

    max_rank = min(progress.current_window_end_rank, progress.word_goal_rank)
    card = _find_any_eligible_card_service(
        selector.db,
        target_language_id=user.target_language_id,
        target_language_code=target_lang.code,
        max_rank=max_rank,
        user_id=user_id,
        exclude_card_id=exclude_card_id,
    )
    if not card:
        return None

    word = card.sentence.word
    ucs = _get_card_review_state_service(
        selector.db,
        user_id=user_id,
        card_id=card.id,
    )
    is_new = ucs is None or ucs.status.value == 'NEW'
    return build_selected_card(
        selector,
        user_id,
        word,
        is_new=is_new,
        exclude_card_id=exclude_card_id,
    )


def get_due_relearn_card(
    selector: 'CardSelectionService',
    user_id: str,
    exclude_card_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Return the highest-priority relearn card for Lingvist mode."""
    result = _get_due_relearn_candidate_service(
        selector.db,
        user_id=user_id,
        exclude_card_id=exclude_card_id,
    )
    if not result:
        return None

    _, word = result
    return build_selected_card(selector, user_id, word, is_new=False)
