"""Helpers for Spec4 card selection responses."""

from fastapi import HTTPException, status

from app.models import Card
from app.schemas.card import CardResponse
from app.services.card_response_service import resolve_request_user_id
from app.services.card_selection import CardSelectionService
from app.services.chat_profile_service import load_cross_mode_learning_context
from app.services.competency_service import build_card_competency_context
from app.services.content_quality_service import content_context, validate_cloze_content
from app.services.lingvist_payload_service import get_card_memory_stage


def build_spec4_card_response(db, user_id: str, card_context: dict) -> CardResponse:
    """Serialize the selected Spec4 card context into the stable API payload."""
    card = db.query(Card).filter(Card.id == card_context["card_id"]).first()
    if not card or not card.sentence or not card.sentence.word:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Card data incomplete", "message": "Missing card, sentence, or word"},
        )
    memory_stage = get_card_memory_stage(db, user_id, card_context["card_id"])
    learning_context = load_cross_mode_learning_context(db, user_id, mode="spec4")
    competency = build_card_competency_context(db, user_id=user_id, card=card)
    validation = validate_cloze_content(card.sentence, card.sentence.word)
    item_content_context = {
        **content_context(card.sentence),
        "validation_status": "valid" if validation.valid else "invalid",
        "validation_issues": list(validation.issues),
    }
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
        learning_context=learning_context,
        competency=competency,
        content_context=item_content_context,
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
