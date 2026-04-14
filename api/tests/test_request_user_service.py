"""Tests for explicit request user resolution helpers."""

import uuid

import pytest
from fastapi import HTTPException

from app.models import User
from app.services.request_user_service import get_request_user, require_user_id


def test_require_user_id_returns_explicit_value():
    user_id = str(uuid.uuid4())
    assert require_user_id(user_id) == user_id


def test_require_user_id_raises_when_missing():
    with pytest.raises(HTTPException) as exc_info:
        require_user_id(None)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail['error'] == 'user_id is required'


def test_get_request_user_returns_user(db_session, sample_languages):
    user = User(
        id=str(uuid.uuid4()),
        username='request-user',
        email='request@example.com',
        language_preference='pt',
        native_language_id=sample_languages['pt'].id,
        target_language_id=sample_languages['en'].id,
    )
    db_session.add(user)
    db_session.commit()

    resolved = get_request_user(db_session, str(user.id))

    assert resolved.id == user.id


def test_get_request_user_raises_when_user_missing(db_session):
    with pytest.raises(HTTPException) as exc_info:
        get_request_user(db_session, str(uuid.uuid4()))

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail['error'] == 'User not found'
