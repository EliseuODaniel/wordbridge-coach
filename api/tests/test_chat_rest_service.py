from datetime import datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.services.chat_rest_service import (
    get_conversation_or_404,
    get_user_or_404,
    serialize_conversation,
    serialize_conversation_list_item,
    serialize_message,
)


class FakeQuery:
    def __init__(self, result=None, count_result=0):
        self.result = result
        self.count_result = count_result

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.result

    def count(self):
        return self.count_result


class FakeDb:
    def __init__(self, result=None, count_result=0):
        self.result = result
        self.count_result = count_result

    def query(self, model):
        return FakeQuery(result=self.result, count_result=self.count_result)


def test_get_user_or_404_raises_when_missing():
    with pytest.raises(HTTPException) as error:
        get_user_or_404(FakeDb(result=None), "missing-user")

    assert error.value.status_code == 404
    assert error.value.detail["error"] == "User not found"


def test_get_conversation_or_404_raises_when_missing():
    with pytest.raises(HTTPException) as error:
        get_conversation_or_404(FakeDb(result=None), "missing-conversation")

    assert error.value.status_code == 404
    assert error.value.detail["error"] == "Conversation not found"


def test_serialize_conversation_maps_fields():
    conversation = SimpleNamespace(
        id="conv-1",
        user_id="user-1",
        title="Travel chat",
        student_profile_json={"cefr_level": "A2"},
        lesson_frame_json={"topic": "travel"},
        session_summary="summary",
        created_at=datetime(2026, 3, 23, 12, 0, 0),
        updated_at=datetime(2026, 3, 23, 12, 5, 0),
    )

    payload = serialize_conversation(conversation)

    assert payload.id == "conv-1"
    assert payload.user_id == "user-1"
    assert payload.title == "Travel chat"
    assert payload.lesson_frame_json["topic"] == "travel"


def test_serialize_message_maps_fields():
    message = SimpleNamespace(
        id="msg-1",
        conversation_id="conv-1",
        role="assistant",
        content="Hello there",
        metadata_json={"teacher_analysis": {}},
        created_at=datetime(2026, 3, 23, 12, 0, 0),
    )

    payload = serialize_message(message)

    assert payload.id == "msg-1"
    assert payload.conversation_id == "conv-1"
    assert payload.role == "assistant"
    assert payload.content == "Hello there"


def test_serialize_conversation_list_item_includes_message_count():
    conversation = SimpleNamespace(
        id="conv-1",
        user_id="user-1",
        title="Travel chat",
        student_profile_json={"cefr_level": "A2"},
        lesson_frame_json={"topic": "travel"},
        session_summary="summary",
        created_at=datetime(2026, 3, 23, 12, 0, 0),
        updated_at=datetime(2026, 3, 23, 12, 5, 0),
    )

    payload = serialize_conversation_list_item(FakeDb(count_result=7), conversation)

    assert payload["id"] == "conv-1"
    assert payload["message_count"] == 7
