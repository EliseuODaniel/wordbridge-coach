"""Orchestration for Lingvist card selection responses."""

from fastapi import HTTPException, status

from app.models import User
from app.services.card_response_service import resolve_request_user_id
from app.services.card_selection import CardSelectionService
from app.services.lingvist_payload_service import build_lingvist_card_response


LINGVIST_TARGET_NEW_WORDS = 20


def get_lingvist_user(db, user_id: str):
    """Load the user used for Lingvist selection and payload enrichment."""
    return db.query(User).filter(User.id == user_id).first()


def get_next_lingvist_card_response(
    db,
    *,
    user_id=None,
    exclude_card_id=None,
    autofill_translations=None,
):
    """Run Lingvist selection, build the enriched payload, and commit side effects."""
    resolved_user_id = resolve_request_user_id(db, user_id)
    card_service = CardSelectionService(db)
    user = get_lingvist_user(db, resolved_user_id)

    original_target_new = getattr(user, "target_new_words", None) if user else None
    if user:
        user.target_new_words = LINGVIST_TARGET_NEW_WORDS

    try:
        card_context = card_service.get_next_card_for_user(
            resolved_user_id,
            exclude_card_id=exclude_card_id,
        )
    finally:
        if user and original_target_new is not None:
            user.target_new_words = original_target_new

    if not card_context:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "No cards available",
                "message": "No cards available for study at this time",
            },
        )

    response = build_lingvist_card_response(
        db=db,
        user_id=resolved_user_id,
        user=user,
        card_context=card_context,
        autofill_translations=autofill_translations,
    )

    db.commit()
    return response
