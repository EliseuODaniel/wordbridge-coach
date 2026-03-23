"""Policy helpers for Spec4 and Lingvist card-mix decisions."""

from app.services.vocabulary_progression import TARGET_NEW_SHARE


def calculate_session_new_share(cards_shown: int, new_cards_shown: int) -> float:
    """Return the share of new cards shown in the current session."""
    if cards_shown <= 0:
        return 0.0
    return new_cards_shown / cards_shown


def should_try_new_card_spec4(current_new_share: float) -> bool:
    """Spec4 introduces new cards while current share stays below the target."""
    return current_new_share < TARGET_NEW_SHARE


def calculate_adaptive_new_share(accuracy_last_20, reviews_due_count: int) -> float:
    """Calculate Lingvist adaptive new-card share."""
    if reviews_due_count > 50:
        return 0.0

    if accuracy_last_20 is not None:
        if accuracy_last_20 < 0.7:
            return 0.10
        if accuracy_last_20 > 0.9:
            return 0.25
        return 0.15

    return 0.15


def should_try_new_card_lingvist(
    *,
    current_new_share: float,
    adaptive_new_share: float,
    reviews_due_count: int,
) -> bool:
    """Lingvist only tries new cards below backlog threshold and below adaptive share."""
    return reviews_due_count < 50 and adaptive_new_share > 0 and current_new_share < adaptive_new_share
