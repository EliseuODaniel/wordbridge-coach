"""Helpers for Spec4 card selection responses."""

from fastapi import HTTPException, status

from app.schemas.card import CardResponse
from app.services.card_response_service import resolve_request_user_id
from app.services.card_selection import CardSelectionService
from app.services.lingvist_payload_service import get_card_memory_stage


def build_spec4_card_response(db, user_id: str, card_context: dict) -> CardResponse:
    """Serialize the selected Spec4 card context into the stable API payload."""
    memory_stage = get_card_memory_stage(db, user_id, card_context["card_id"])
    return CardResponse(
        card_id=card_context["card_id"],
        word_id=card_context["word_id"],
        sentence_id=card_context["sentence_id"],
        word=card_context["word"],
        sentence=card_context["sentence"],
        gap=card_context["gap"],
        sentence_translation=card_context["sentence_translation"],
        grammar_hint=card_context["grammar_hint"],
        memory_stage=memory_stage,
        is_new=card_context["is_new"],
        audio_word_url=card_context["audio_word_url"],
        audio_sentence_url=card_context["audio_sentence_url"],
        sentence_source=card_context.get("sentence_source"),
    )


def get_next_spec4_card_response(db, *, user_id=None, exclude_card_id=None) -> CardResponse:
    """Run the Spec4 selection flow and build the API response."""
    resolved_user_id = resolve_request_user_id(db, user_id)
    card_service = CardSelectionService(db)
    card_context = card_service.get_next_card_for_user(
        resolved_user_id,
        exclude_card_id=exclude_card_id,
    )

    if not card_context:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "No cards available",
                "message": "No cards available for study at this time",
            },
        )

    return build_spec4_card_response(db, resolved_user_id, card_context)
