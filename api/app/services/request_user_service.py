"""Helpers for resolving request-scoped users without bootstrap side effects."""

from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import User


def require_user_id(user_id: Optional[str]) -> str:
    """Require a user_id query parameter for stateful endpoints."""
    if user_id:
        return user_id

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
            'error': 'user_id is required',
            'message': 'Pass a user_id query parameter instead of relying on implicit demo bootstrap.',
        },
    )


def get_user_or_404(db: Session, user_id: str) -> User:
    """Load a persisted user or raise a stable 404 payload."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'error': 'User not found', 'message': f'User with ID {user_id} not found'},
        )

    return user


def get_request_user(db: Session, user_id: Optional[str]) -> User:
    """Resolve the explicit request user for endpoints that must stay side-effect free."""
    return get_user_or_404(db, require_user_id(user_id))
