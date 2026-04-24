"""Card endpoints for WordBridge Coach API."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.card import CardResponse, AnswerRequest, AnswerResponse
from app.schemas.lingvist import LingvistCardResponse
from app.services.card_next_service import get_next_card_response
from app.services.card_submission_service import submit_card_answer as _submit_card_answer_service
from app.services.card_spec4_service import get_next_spec4_card_response
from app.services.card_lingvist_service import get_next_lingvist_card_response
from app.services.lingvist_autofill_service import autofill_translations

router = APIRouter()
logger = logging.getLogger(__name__)


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
        response = get_next_card_response(
            db,
            user_id=user_id,
        )
        logger.info("card_selected mode=legacy user_id=%s card_id=%s", user_id, response.card_id)
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("card_selection_failed mode=legacy user_id=%s", user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "message": str(e)}
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
        return _submit_card_answer_service(
            db,
            card_id=card_id,
            answer_data=answer_data,
            user_id=user_id,
        )
        
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
        response = get_next_spec4_card_response(
            db,
            user_id=user_id,
            exclude_card_id=exclude_card_id,
        )
        logger.info("card_selected mode=spec4 user_id=%s card_id=%s", user_id, response.card_id)
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("card_selection_failed mode=spec4 user_id=%s", user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "message": str(e)}
        )


@router.get("/next-lingvist", response_model=LingvistCardResponse)
async def get_next_card_lingvist(
    user_id: Optional[str] = None,
    exclude_card_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get next card for Lingvist mode training

    Lingvist mode: Inline cloze with progressive hints, audio after correct,
    and PT-BR translations. Reuses Spec4 selection algorithm but with
    enriched payload.

    Mix: 20% new / 80% review (more conservative than Spec4).

    Auto-translation: If LINGVIST_TRANSLATIONS_AUTOFILL is enabled and
    translations are missing, generates them on-demand using Argos Translate.
    """
    try:
        response = get_next_lingvist_card_response(
            db,
            user_id=user_id,
            exclude_card_id=exclude_card_id,
            autofill_translations=autofill_translations,
        )
        logger.info("card_selected mode=lingvist user_id=%s card_id=%s", user_id, response.card_id)
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("card_selection_failed mode=lingvist user_id=%s", user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "message": str(e)}
        )


@router.get("/health")
async def health_check():
    """Health check for cards service"""
    return {"status": "healthy", "service": "cards-api"}
