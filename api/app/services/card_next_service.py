"""Legacy `/cards/next` selection flow extracted from the cards endpoint."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.models import Card, ReviewEvent, User, UserCardState
from app.models.user_card_state import MemoryStage
from app.services.card_bootstrap_service import create_sample_data_if_needed
from app.services.card_response_service import format_card_response, resolve_request_user_id
from app.schemas.card import CardResponse


def get_card_user_or_404(db: Session, user_id: str) -> User:
    """Load the user required by the legacy study flow."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "User not found", "message": "User setup required"},
        )
    return user


def count_new_cards_today(db: Session, user_id: str) -> int:
    """Count cards first seen today by the user."""
    cards_seen_today = db.query(func.distinct(ReviewEvent.card_id)).filter(
        and_(
            ReviewEvent.user_id == user_id,
            func.date(ReviewEvent.created_at) == func.current_date(),
        )
    ).subquery()

    cards_seen_before_today = db.query(func.distinct(ReviewEvent.card_id)).filter(
        and_(
            ReviewEvent.user_id == user_id,
            func.date(ReviewEvent.created_at) < func.current_date(),
        )
    ).subquery()

    return (
        db.query(Card.id)
        .filter(
            and_(
                Card.id.in_(select(cards_seen_today.c[0])),
                ~Card.id.in_(select(cards_seen_before_today.c[0])),
            )
        )
        .count()
        or 0
    )


def get_due_card_state(db: Session, user_id: str):
    """Return the next due card state for the user."""
    now = utc_now()
    return (
        db.query(UserCardState)
        .join(Card)
        .filter(
            and_(
                UserCardState.user_id == user_id,
                UserCardState.next_review_at <= now,
                Card.is_active == True,
            )
        )
        .order_by(UserCardState.next_review_at)
        .first()
    )


def get_new_card_state(db: Session, user_id: str):
    """Return the next new card state for the user."""
    return (
        db.query(UserCardState)
        .join(Card)
        .filter(
            and_(
                UserCardState.user_id == user_id,
                UserCardState.status == MemoryStage.NEW,
                Card.is_active == True,
            )
        )
        .first()
    )


def get_learning_card_state(db: Session, user_id: str):
    """Return the next learning card state for the user."""
    return (
        db.query(UserCardState)
        .join(Card)
        .filter(
            and_(
                UserCardState.user_id == user_id,
                UserCardState.status == MemoryStage.LEARNING,
                Card.is_active == True,
            )
        )
        .first()
    )


def get_next_card_response(db: Session, *, user_id: str | None = None) -> CardResponse:
    """Run the legacy study selection flow and build the stable API response."""
    create_sample_data_if_needed(db)

    resolved_user_id = resolve_request_user_id(db, user_id)
    user = get_card_user_or_404(db, resolved_user_id)

    due_card = get_due_card_state(db, resolved_user_id)
    if due_card:
        return format_card_response(due_card.card, due_card.status)

    can_give_new_cards = count_new_cards_today(db, resolved_user_id) < user.daily_new_limit
    if can_give_new_cards:
        new_card_state = get_new_card_state(db, resolved_user_id)
        if new_card_state:
            return format_card_response(new_card_state.card, new_card_state.status)

    learning_card_state = get_learning_card_state(db, resolved_user_id)
    if learning_card_state:
        return format_card_response(learning_card_state.card, learning_card_state.status)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "error": "No cards available",
            "message": "Todos os cartões foram revisados hoje!",
        },
    )
