"""Tests for chat conversation management helpers."""

from types import SimpleNamespace

from app.services import chat_conversation_service


class FakeQuery:
    def __init__(self, result=None, results=None):
        self.result = result
        self.results = list(results or [])

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def offset(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def first(self):
        return self.result

    def all(self):
        return list(self.results)


class FakeDb:
    def __init__(self):
        self.added = []
        self.deleted = []
        self.commit_count = 0
        self.refreshed = []
        self.query_results = {}

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        self.commit_count += 1

    def refresh(self, obj):
        self.refreshed.append(obj)
        if not getattr(obj, "id", None):
            obj.id = "conv-1"

    def delete(self, obj):
        self.deleted.append(obj)

    def query(self, model):
        return self.query_results[model]


def test_default_lesson_frame_contains_expected_baseline():
    payload = chat_conversation_service.get_default_lesson_frame()

    assert payload["cefr_target"] == "A2"
    assert payload["topic"] == "getting_started"
    assert "friendly" in payload["rubric"]["style"]


def test_default_student_profile_contains_expected_baseline():
    payload = chat_conversation_service.get_default_student_profile()

    assert payload == {
        "cefr_level": "A2",
        "common_errors": [],
        "strengths": [],
        "weaknesses": [],
    }


def test_create_chat_conversation_creates_conversation_and_system_message(monkeypatch):
    db = FakeDb()
    request = SimpleNamespace(user_id="user-1", title="Travel practice")

    monkeypatch.setattr(chat_conversation_service, "get_user_or_404", lambda db, user_id: SimpleNamespace(id=user_id))
    monkeypatch.setattr(
        chat_conversation_service,
        "build_seed_chat_state",
        lambda db, user, base_lesson_frame: (
            {"cefr_level": "B1", "feedback_language": "Portuguese"},
            {"cefr_target": "B1", "topic": "travel"},
            "Longitudinal learner profile",
        ),
    )
    monkeypatch.setattr(
        chat_conversation_service,
        "serialize_conversation",
        lambda conversation: {"id": conversation.id, "title": conversation.title},
    )

    payload = chat_conversation_service.create_chat_conversation(db, request)

    assert payload == {"id": "conv-1", "title": "Travel practice"}
    assert len(db.added) == 3
    assert db.added[0].title == "Travel practice"
    assert db.added[0].student_profile_json["feedback_language"] == "Portuguese"
    assert db.added[0].session_summary == "Longitudinal learner profile"
    assert db.added[1].lesson_frame_json["topic"] == "travel"
    assert db.added[2].role == "system"
    assert "B1 level student" in db.added[2].content
    assert "Portuguese" in db.added[2].content
    assert db.commit_count == 2
    assert db.refreshed == [db.added[0]]


def test_list_chat_conversations_serializes_all_results(monkeypatch):
    db = FakeDb()
    conversations = [
        SimpleNamespace(id="conv-1"),
        SimpleNamespace(id="conv-2"),
    ]
    db.query_results[chat_conversation_service.ChatConversation] = FakeQuery(results=conversations)

    monkeypatch.setattr(chat_conversation_service, "get_user_or_404", lambda db, user_id: object())
    monkeypatch.setattr(
        chat_conversation_service,
        "serialize_conversation_list_item",
        lambda db, conversation: {"id": conversation.id},
    )

    payload = chat_conversation_service.list_chat_conversations(db, "user-1")

    assert payload == [{"id": "conv-1"}, {"id": "conv-2"}]


def test_list_chat_messages_serializes_paginated_results(monkeypatch):
    db = FakeDb()
    messages = [
        SimpleNamespace(id="msg-1"),
        SimpleNamespace(id="msg-2"),
    ]
    db.query_results[chat_conversation_service.ChatMessage] = FakeQuery(results=messages)

    monkeypatch.setattr(chat_conversation_service, "get_conversation_or_404", lambda db, conversation_id: object())
    monkeypatch.setattr(
        chat_conversation_service,
        "serialize_message",
        lambda message: {"id": message.id},
    )

    payload = chat_conversation_service.list_chat_messages(db, "conv-1", limit=2, offset=0)

    assert payload == [{"id": "msg-1"}, {"id": "msg-2"}]


def test_delete_chat_conversation_deletes_and_commits(monkeypatch):
    db = FakeDb()
    conversation = SimpleNamespace(id="conv-1")

    monkeypatch.setattr(
        chat_conversation_service,
        "get_conversation_or_404",
        lambda db, conversation_id: conversation,
    )

    payload = chat_conversation_service.delete_chat_conversation(db, "conv-1")

    assert payload == {"message": "Conversation deleted successfully"}
    assert db.deleted == [conversation]
    assert db.commit_count == 1
