import asyncio
from types import SimpleNamespace

from app.services.chat_delivery_service import (
    attach_teacher_analysis_metadata,
    build_assistant_done_payload,
    build_teacher_analysis_event_payload,
    finalize_assistant_turn,
    persist_and_emit_teacher_analysis,
)


def test_attach_teacher_analysis_metadata_initializes_payload():
    user_message = SimpleNamespace(metadata_json=None)
    teacher_analysis = {"rewrite": "I went", "corrections": []}

    attach_teacher_analysis_metadata(user_message, teacher_analysis)

    assert user_message.metadata_json == {"teacher_analysis": teacher_analysis}


def test_build_teacher_analysis_event_payload_uses_expected_schema():
    payload = build_teacher_analysis_event_payload(
        conversation_id="conv-1",
        user_message_id="msg-1",
        analysis={"teacher_summary": "Good job", "corrections": []},
    )

    assert payload["type"] == "teacher_analysis"
    assert payload["conversation_id"] == "conv-1"
    assert payload["user_message_id"] == "msg-1"
    assert payload["analysis"]["teacher_summary"] == "Good job"


def test_build_assistant_done_payload_uses_sanitized_content():
    payload = build_assistant_done_payload(
        conversation_id="conv-1",
        full_content="Hello there!",
        lesson_frame={"topic": "travel"},
    )

    assert payload["type"] == "assistant_done"
    assert payload["conversation_id"] == "conv-1"
    assert payload["full_content"] == "Hello there!"
    assert payload["lesson_frame"]["topic"] == "travel"
    assert payload["summary_update"] == "Student sent a message."


def test_finalize_assistant_turn_sanitizes_and_emits_final_payload():
    class FakeWebSocket:
        def __init__(self):
            self.payloads = []

        async def send_json(self, payload):
            self.payloads.append(payload)

    class FakeDb:
        def __init__(self):
            self.added = []
            self.commit_count = 0

        def add(self, item):
            self.added.append(item)

        def commit(self):
            self.commit_count += 1

    conversation = SimpleNamespace(
        id="conv-1",
        lesson_frame_json={"topic": "travel"},
        updated_at=None,
    )
    websocket = FakeWebSocket()
    db = FakeDb()

    sanitized = asyncio.run(
        finalize_assistant_turn(
            websocket=websocket,
            db=db,
            conversation=conversation,
            full_response='Nice! What happened next?\n\n"I went home."',
            sanitize_response=lambda response: "Nice! What happened next?",
        )
    )

    assert sanitized == "Nice! What happened next?"
    assert db.commit_count == 1
    assert len(db.added) == 1
    assert db.added[0].role == "assistant"
    assert db.added[0].content == "Nice! What happened next?"
    assert websocket.payloads[0]["type"] == "assistant_done"


def test_persist_and_emit_teacher_analysis_persists_metadata_when_not_fallback():
    class FakeDb:
        def __init__(self):
            self.commit_count = 0

        def commit(self):
            self.commit_count += 1

    user_message = SimpleNamespace(id="msg-1", metadata_json=None)
    conversation = SimpleNamespace(id="conv-1")
    db = FakeDb()
    captured = {}

    async def send_event(**kwargs):
        captured.update(kwargs)

    asyncio.run(
        persist_and_emit_teacher_analysis(
            websocket=object(),
            db=db,
            conversation=conversation,
            user_message=user_message,
            teacher_analysis={"teacher_summary": "Good attempt"},
            used_fallback=False,
            send_event=send_event,
        )
    )

    assert db.commit_count == 1
    assert user_message.metadata_json["teacher_analysis"]["teacher_summary"] == "Good attempt"
    assert captured["conversation_id"] == "conv-1"
    assert captured["user_message_id"] == "msg-1"


def test_persist_and_emit_teacher_analysis_skips_db_commit_for_fallback():
    class FakeDb:
        def __init__(self):
            self.commit_count = 0

        def commit(self):
            self.commit_count += 1

    user_message = SimpleNamespace(id="msg-1", metadata_json=None)
    conversation = SimpleNamespace(id="conv-1")
    db = FakeDb()
    captured = {}

    async def send_event(**kwargs):
        captured.update(kwargs)

    asyncio.run(
        persist_and_emit_teacher_analysis(
            websocket=object(),
            db=db,
            conversation=conversation,
            user_message=user_message,
            teacher_analysis={"teacher_summary": "Fallback", "debug_reason": "offline"},
            used_fallback=True,
            send_event=send_event,
        )
    )

    assert db.commit_count == 0
    assert user_message.metadata_json is None
    assert captured["analysis"]["teacher_summary"] == "Fallback"
