"""
Test for Chat Endpoint Utilities

This test ensures that:
1. _sanitize_assistant_response removes quoted user simulation
2. _sanitize_assistant_response truncates at role labels
3. _sanitize_assistant_response handles edge cases
"""

import asyncio
import sys
import os
from types import SimpleNamespace

# Add parent directory to path to import from app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.api.api_v1.endpoints.chat import (
    _sanitize_assistant_response,
    _merge_issues,
    _build_ws_error_payload,
    _build_throttled_feedback,
    _build_chat_system_prompt,
    _build_chat_generation_config,
    _build_teacher_analysis_fallback,
    _build_teacher_analysis_context,
    _attach_teacher_analysis_metadata,
    _build_teacher_analysis_event_payload,
    _build_assistant_done_payload,
    _generate_teacher_analysis_with_fallback,
    _freeze_user_message_feedback,
    _finalize_assistant_turn,
    _persist_and_emit_teacher_analysis,
)


def test_sanitize_removes_quoted_user_simulation():
    """Test that quoted paragraphs at the end are removed."""
    # Case 1: Quoted text after blank line
    response1 = "That's great! How was your experience?\n\n\"I went to the beach and it was fun.\""
    sanitized1 = _sanitize_assistant_response(response1)

    assert "I went to the beach" not in sanitized1, \
        f"Should remove quoted user simulation. Got: {sanitized1}"
    assert sanitized1 == "That's great! How was your experience?", \
        f"Should keep only assistant response. Got: {sanitized1}"

    # Case 2: Multiple quoted paragraphs
    response2 = "Nice! What did you do?\n\n\"I played tennis.\"\n\n\"It was very fun.\""
    sanitized2 = _sanitize_assistant_response(response2)

    assert "I played tennis" not in sanitized2, \
        f"Should remove all quoted paragraphs. Got: {sanitized2}"
    assert sanitized2 == "Nice! What did you do?", \
        f"Should keep only assistant response. Got: {sanitized2}"

    print(f"\n✅ Quoted user simulation removal test passed")
    print(f"   Input 1: '{response1}'")
    print(f"   Output 1: '{sanitized1}'")
    print(f"   Input 2: '{response2}'")
    print(f"   Output 2: '{sanitized2}'")


def test_sanitize_truncates_at_role_labels():
    """Test that text after role labels is removed."""
    # Case 1: User: label
    response1 = "That's interesting! Tell me more.\nUser: I went to the park yesterday."
    sanitized1 = _sanitize_assistant_response(response1)

    assert "I went to the park" not in sanitized1, \
        f"Should truncate at 'User:'. Got: {sanitized1}"
    assert sanitized1 == "That's interesting! Tell me more.", \
        f"Should keep only text before role label. Got: {sanitized1}"

    # Case 2: STUDENT: label (uppercase)
    response2 = "Great question!\nSTUDENT: I don't understand."
    sanitized2 = _sanitize_assistant_response(response2)

    assert "I don't understand" not in sanitized2, \
        f"Should truncate at 'STUDENT:'. Got: {sanitized2}"
    assert sanitized2 == "Great question!", \
        f"Should keep only text before role label. Got: {sanitized2}"

    # Case 3: Student: label (mixed case)
    response3 = "Hello! How are you?\nStudent: I'm fine, thank you."
    sanitized3 = _sanitize_assistant_response(response3)

    assert "I'm fine" not in sanitized3, \
        f"Should truncate at 'Student:'. Got: {sanitized3}"
    assert sanitized3 == "Hello! How are you?", \
        f"Should keep only text before role label. Got: {sanitized3}"

    print(f"\n✅ Role label truncation test passed")
    print(f"   Input 1: '{response1}'")
    print(f"   Output 1: '{sanitized1}'")
    print(f"   Input 2: '{response2}'")
    print(f"   Output 2: '{sanitized2}'")
    print(f"   Input 3: '{response3}'")
    print(f"   Output 3: '{sanitized3}'")


def test_sanitize_combined_patterns():
    """Test that both quoted text and role labels are handled."""
    # Case 1: Both quoted text and role label (should handle role label first)
    response1 = "Nice day!\n\n\"It's sunny.\"\nUser: Yes, very sunny."
    sanitized1 = _sanitize_assistant_response(response1)

    # Should truncate at User: before quoted text processing
    assert "Yes, very sunny" not in sanitized1, \
        f"Should truncate at role label. Got: {sanitized1}"

    # Case 2: Role label followed by quoted text
    response2 = "Tell me more.\nStudent: \"I like tennis.\""
    sanitized2 = _sanitize_assistant_response(response2)

    assert "I like tennis" not in sanitized2, \
        f"Should truncate at role label. Got: {sanitized2}"
    assert sanitized2 == "Tell me more.", \
        f"Should keep only assistant response. Got: {sanitized2}"

    print(f"\n✅ Combined patterns test passed")
    print(f"   Input 1: '{response1}'")
    print(f"   Output 1: '{sanitized1}'")
    print(f"   Input 2: '{response2}'")
    print(f"   Output 2: '{sanitized2}'")


def test_sanitize_edge_cases():
    """Test edge cases and normal responses."""
    # Case 1: Clean response (no sanitization needed)
    response1 = "That's great! How was your experience?"
    sanitized1 = _sanitize_assistant_response(response1)

    assert sanitized1 == response1, \
        f"Clean response should pass through unchanged. Got: {sanitized1}"

    # Case 2: Empty response
    response2 = ""
    sanitized2 = _sanitize_assistant_response(response2)

    assert sanitized2 == "", \
        f"Empty response should remain empty. Got: '{sanitized2}'"

    # Case 3: Response with quotes in middle (not at end)
    response3 = 'He said "hello" and then left.'
    sanitized3 = _sanitize_assistant_response(response3)

    assert sanitized3 == response3, \
        f"Quotes in middle should not be removed. Got: {sanitized3}"

    # Case 4: Response with normal quotes but no blank line before
    response4 = 'The word is "important" for learning.'
    sanitized4 = _sanitize_assistant_response(response4)

    assert sanitized4 == response4, \
        f"Quotes without blank line should not trigger removal. Got: {sanitized4}"

    print(f"\n✅ Edge cases test passed")
    print(f"   Clean response: '{response1}' → '{sanitized1}'")
    print(f"   Empty response: '{response2}' → '{sanitized2}'")
    print(f"   Quotes in middle: '{response3}' → '{sanitized3}'")
    print(f"   Normal quotes: '{response4}' → '{sanitized4}'")


def test_sanitize_multiline_responses():
    """Test responses with multiple lines."""
    # Case 1: Multiline assistant response followed by user simulation
    response1 = """That's interesting!
Can you tell me more about it?

"I went to the beach with my family.
We had a great time playing in the sand."
"""
    sanitized1 = _sanitize_assistant_response(response1)

    assert "I went to the beach" not in sanitized1, \
        f"Should remove quoted multiline user simulation. Got: {sanitized1}"
    assert "Can you tell me more about it?" in sanitized1, \
        f"Should keep assistant's multiline response. Got: {sanitized1}"

    # Case 2: Assistant response with multiple paragraphs, no user sim
    response2 = """Hello! How are you today?
I hope you are having a great time learning English.

Do you have any questions for me?"""

    sanitized2 = _sanitize_assistant_response(response2)

    assert sanitized2 == response2, \
        f"Clean multiline response should pass through unchanged. Got: {sanitized2}"

    print(f"\n✅ Multiline responses test passed")
    print(f"   Input 1 (multiline with sim):\n{response1}")
    print(f"   Output 1:\n{sanitized1}")
    print(f"   Input 2 (clean multiline):\n{response2}")
    print(f"   Output 2:\n{sanitized2}")


def test_merge_issues_deduplicates_overlapping_heuristic_items():
    """LanguageTool issues should win when spans overlap with heuristic ones."""
    lt_issues = [
        {
            "category": "grammar",
            "title": "Verb tense",
            "highlight_spans": [{"start": 2, "end": 6}],
            "suggestions": ["went"],
        }
    ]
    heuristic_issues = [
        {
            "category": "grammar",
            "title": "Verb tense",
            "highlight_spans": [{"start": 2, "end": 6}],
            "suggestions": ["gone"],
        },
        {
            "category": "style",
            "title": "Word choice",
            "highlight_spans": [{"start": 10, "end": 14}],
            "suggestions": ["nice"],
        },
    ]

    merged = _merge_issues(lt_issues, heuristic_issues)

    assert len(merged) == 2
    assert merged[0]["suggestions"] == ["went"]
    assert merged[1]["category"] == "style"


def test_build_throttled_feedback_preserves_cached_payload():
    """Throttle reuse should update timestamp/draft without mutating the cache."""
    cached_feedback = {
        "conversation_id": "conv-1",
        "draft": "old text",
        "server_ts_ms": 1000,
        "issues": [{"category": "grammar"}],
    }

    updated = _build_throttled_feedback(cached_feedback, "new text", 2000)

    assert updated["draft"] == "new text"
    assert updated["server_ts_ms"] == 2000
    assert updated["issues"] == cached_feedback["issues"]
    assert cached_feedback["draft"] == "old text"
    assert cached_feedback["server_ts_ms"] == 1000


def test_build_ws_error_payload_uses_expected_schema():
    """WebSocket errors should use the shared payload shape."""
    payload = _build_ws_error_payload("Conversation not found", "NOT_FOUND")

    assert payload["type"] == "error"
    assert payload["message"] == "Conversation not found"
    assert payload["code"] == "NOT_FOUND"


def test_build_chat_system_prompt_uses_lesson_frame_defaults():
    """Prompt should reflect the lesson frame while keeping the tutor constraints."""
    prompt = _build_chat_system_prompt({
        "cefr_target": "B1",
        "topic": "travel",
        "learning_goal": "asking_for_directions",
    }, {
        "feedback_language": "Portuguese",
        "strengths": ["Clear openings"],
        "weaknesses": ["Past tense"],
        "scaffolding_level": "guided_practice",
    }, "Longitudinal learner profile")

    assert "B1" in prompt
    assert "travel" in prompt
    assert "asking_for_directions" in prompt
    assert "Always ask a follow-up question" in prompt
    assert "Portuguese" in prompt
    assert "Longitudinal learner profile" in prompt
    assert "No examples, quotes, or meta-commentary" in prompt


def test_build_teacher_analysis_context_prefers_user_messages():
    """Teacher analysis should prefer user-only message history over session summary."""
    from app.services.chat_context_service import build_teacher_analysis_context

    conversation = SimpleNamespace(id="conv-1", session_summary="summary fallback")

    context = build_teacher_analysis_context(
        conversation=conversation,
        db=object(),
        build_teacher_context_fn=lambda conversation_id, db, limit=10: [
            {"role": "user", "content": "First message"},
            {"role": "user", "content": "Second message"},
        ],
    )

    assert context == "summary fallback\n\nRecent student messages:\nFirst message\nSecond message"


def test_build_teacher_analysis_context_falls_back_to_session_summary():
    """Teacher analysis should still work when no persisted user history exists."""
    from app.services.chat_context_service import build_teacher_analysis_context

    conversation = SimpleNamespace(id="conv-1", session_summary="summary fallback")

    context = build_teacher_analysis_context(
        conversation=conversation,
        db=object(),
        build_teacher_context_fn=lambda conversation_id, db, limit=10: [],
    )

    assert context == "summary fallback"


def test_build_chat_generation_config_filters_stop_sequences():
    """Generation config should expose the expected safe chat stop markers."""
    config = _build_chat_generation_config()

    assert config["temperature"] == 0.5
    assert config["max_tokens"] == 300
    assert "\nUser:" in config["stop"]
    assert "\nSystem:" in config["stop"]
    assert all(isinstance(stop, str) and stop.strip() for stop in config["stop"])


def test_build_teacher_analysis_fallback_truncates_error_reason():
    """Fallback analysis should expose a bounded debug reason and safe defaults."""
    long_error = RuntimeError("x" * 150)
    fallback = _build_teacher_analysis_fallback(long_error)

    assert fallback["rewrite"] is None
    assert fallback["corrections"] == []
    assert fallback["next_practice"] == []
    assert len(fallback["debug_reason"]) == 100
    assert fallback["teacher_summary"].startswith("Teacher analysis failed:")


def test_attach_teacher_analysis_metadata_initializes_payload():
    """Teacher analysis should be written into metadata even when it starts empty."""
    user_message = SimpleNamespace(metadata_json=None)
    teacher_analysis = {"rewrite": "I went", "corrections": []}

    _attach_teacher_analysis_metadata(user_message, teacher_analysis)

    assert user_message.metadata_json["teacher_analysis"]["rewrite"] == "I went"
    assert user_message.metadata_json["teacher_analysis"]["teacher_summary"] == "Analysis unavailable."


def test_build_teacher_analysis_event_payload_uses_expected_schema():
    """Teacher analysis websocket payload should preserve ids and analysis content."""
    payload = _build_teacher_analysis_event_payload(
        conversation_id="conv-1",
        user_message_id="msg-1",
        analysis={"teacher_summary": "Good job", "corrections": []},
        student_profile={"feedback_language": "Portuguese"},
        lesson_frame={"topic": "travel"},
        session_summary="Longitudinal learner profile",
    )

    assert payload["type"] == "teacher_analysis"
    assert payload["conversation_id"] == "conv-1"
    assert payload["user_message_id"] == "msg-1"
    assert payload["analysis"]["teacher_summary"] == "Good job"
    assert payload["student_profile"]["feedback_language"] == "Portuguese"
    assert payload["lesson_frame"]["topic"] == "travel"
    assert payload["session_summary"] == "Longitudinal learner profile"


def test_build_assistant_done_payload_uses_sanitized_content():
    """assistant_done payload should preserve the final sanitized response."""
    payload = _build_assistant_done_payload(
        conversation_id="conv-1",
        full_content="Hello there!",
        lesson_frame={"topic": "travel"},
    )

    assert payload["type"] == "assistant_done"
    assert payload["conversation_id"] == "conv-1"
    assert payload["full_content"] == "Hello there!"
    assert payload["lesson_frame"]["topic"] == "travel"
    assert payload["summary_update"] == "Student sent a message."


def test_generate_teacher_analysis_with_fallback_returns_generated_payload():
    """Successful teacher analysis should not fall back."""

    class FakeTeacherProvider:
        model = "fake-teacher"

        async def generate_teacher_analysis(self, user_message, context, lesson_frame, student_profile):
            assert user_message == "I go to school"
            assert context == "teacher-only context"
            assert lesson_frame["topic"] == "school"
            assert student_profile["feedback_language"] == "Portuguese"
            return {"teacher_summary": "Nice work", "corrections": []}

    conversation = SimpleNamespace(
        id="conv-1",
        session_summary="session-summary",
        lesson_frame_json={"topic": "school"},
        student_profile_json={"feedback_language": "Portuguese"},
    )

    analysis, used_fallback = asyncio.run(
        _generate_teacher_analysis_with_fallback(
            teacher_provider=FakeTeacherProvider(),
            conversation=conversation,
            teacher_context="teacher-only context",
            content="I go to school",
        )
    )

    assert used_fallback is False
    assert analysis["teacher_summary"] == "Nice work"


def test_generate_teacher_analysis_with_fallback_uses_fallback_on_error():
    """Provider errors should be converted into the safe fallback analysis."""

    class FailingTeacherProvider:
        model = "fake-teacher"

        async def generate_teacher_analysis(self, user_message, context, lesson_frame, student_profile):
            raise RuntimeError("teacher offline")

    conversation = SimpleNamespace(
        id="conv-1",
        session_summary="session-summary",
        lesson_frame_json={"topic": "school"},
        student_profile_json={"feedback_language": "Portuguese"},
    )

    analysis, used_fallback = asyncio.run(
        _generate_teacher_analysis_with_fallback(
            teacher_provider=FailingTeacherProvider(),
            conversation=conversation,
            teacher_context="teacher-only context",
            content="I go to school",
        )
    )

    assert used_fallback is True
    assert analysis["teacher_summary"].startswith("Teacher analysis failed:")
    assert analysis["debug_reason"] == "teacher offline"


def test_freeze_user_message_feedback_sends_snapshot_payload():
    """Submitted messages should send a frozen draft_feedback snapshot."""

    class FakeChatProvider:
        async def micro_eval(self, context, lesson_frame, draft, student_profile):
            assert context == "session-summary"
            assert lesson_frame["topic"] == "travel"
            assert draft == "I travel tomorrow"
            assert student_profile["cefr_level"] == "A2"
            return {
                "spelling_score": 95,
                "grammar_score": 90,
                "lesson_alignment_score": 88,
                "naturalness_score": 85,
                "top_issues": [],
                "suggested_next_words": ["to"],
                "topic": "travel",
                "intent": "future_plan",
            }

    class FakeWebSocket:
        def __init__(self):
            self.payloads = []

        async def send_json(self, payload):
            self.payloads.append(payload)

    conversation = SimpleNamespace(
        id="conv-1",
        session_summary="session-summary",
        lesson_frame_json={"topic": "travel"},
        student_profile_json={"cefr_level": "A2"},
    )
    websocket = FakeWebSocket()

    payload = asyncio.run(
        _freeze_user_message_feedback(
            websocket=websocket,
            conversation=conversation,
            content="I travel tomorrow",
            chat_provider=FakeChatProvider(),
        )
    )

    assert payload["type"] == "draft_feedback"
    assert payload["conversation_id"] == "conv-1"
    assert payload["draft"] == "I travel tomorrow"
    assert payload["topic"] == "travel"
    assert websocket.payloads == [payload]


def test_finalize_assistant_turn_sanitizes_and_emits_final_payload():
    """Final assistant turn should sanitize content, persist it, and send assistant_done."""

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
        _finalize_assistant_turn(
            websocket=websocket,
            db=db,
            conversation=conversation,
            full_response='Nice! What happened next?\n\n"I went home."',
        )
    )

    assert sanitized == "Nice! What happened next?"
    assert db.commit_count == 1
    assert len(db.added) == 1
    assert db.added[0].role == "assistant"
    assert db.added[0].content == "Nice! What happened next?"
    assert websocket.payloads[0]["type"] == "assistant_done"
    assert websocket.payloads[0]["full_content"] == "Nice! What happened next?"


def test_persist_and_emit_teacher_analysis_persists_metadata_when_not_fallback(monkeypatch):
    """Teacher analysis should persist metadata and emit the websocket event."""

    class FakeWebSocket:
        def __init__(self):
            self.payloads = []

        async def send_json(self, payload):
            self.payloads.append(payload)

    class FakeDb:
        def __init__(self):
            self.commit_count = 0

        def commit(self):
            self.commit_count += 1

    websocket = FakeWebSocket()
    db = FakeDb()
    conversation = SimpleNamespace(
        id="conv-1",
        student_profile_json={"feedback_language": "Portuguese"},
        lesson_frame_json={"topic": "travel"},
        session_summary="old summary",
    )
    user_message = SimpleNamespace(id="msg-1", metadata_json=None)
    analysis = {"teacher_summary": "Good job", "corrections": []}

    monkeypatch.setattr(
        "app.services.chat_delivery_service.refresh_conversation_learning_state",
        lambda db, conversation, teacher_analysis: (
            {"feedback_language": "Portuguese", "strengths": ["Clear meaning"]},
            {"topic": "travel", "learning_goal": "stabilize past-time verbs"},
            "Longitudinal learner profile",
        ),
    )

    asyncio.run(
        _persist_and_emit_teacher_analysis(
            websocket=websocket,
            db=db,
            conversation=conversation,
            user_message=user_message,
            teacher_analysis=analysis,
            used_fallback=False,
        )
    )

    assert db.commit_count == 1
    assert user_message.metadata_json["teacher_analysis"]["teacher_summary"] == "Good job"
    assert websocket.payloads[0]["type"] == "teacher_analysis"
    assert websocket.payloads[0]["analysis"]["teacher_summary"] == "Good job"
    assert websocket.payloads[0]["student_profile"]["strengths"] == ["Clear meaning"]
    assert websocket.payloads[0]["lesson_frame"]["learning_goal"] == "stabilize past-time verbs"
    assert websocket.payloads[0]["session_summary"] == "Longitudinal learner profile"


def test_persist_and_emit_teacher_analysis_skips_db_commit_for_fallback():
    """Fallback teacher analysis should still emit the event without persisting metadata."""

    class FakeWebSocket:
        def __init__(self):
            self.payloads = []

        async def send_json(self, payload):
            self.payloads.append(payload)

    class FakeDb:
        def __init__(self):
            self.commit_count = 0

        def commit(self):
            self.commit_count += 1

    websocket = FakeWebSocket()
    db = FakeDb()
    conversation = SimpleNamespace(
        id="conv-1",
        student_profile_json={"feedback_language": "Portuguese"},
        lesson_frame_json={"topic": "travel"},
        session_summary="existing summary",
    )
    user_message = SimpleNamespace(id="msg-1", metadata_json=None)
    analysis = {
        "teacher_summary": "Teacher analysis failed: offline",
        "corrections": [],
        "debug_reason": "offline",
    }

    asyncio.run(
        _persist_and_emit_teacher_analysis(
            websocket=websocket,
            db=db,
            conversation=conversation,
            user_message=user_message,
            teacher_analysis=analysis,
            used_fallback=True,
        )
    )

    assert db.commit_count == 0
    assert user_message.metadata_json is None
    assert websocket.payloads[0]["type"] == "teacher_analysis"
    assert websocket.payloads[0]["analysis"]["teacher_summary"] == "Teacher analysis failed: offline"
    assert websocket.payloads[0]["student_profile"]["feedback_language"] == "Portuguese"
    assert websocket.payloads[0]["lesson_frame"]["topic"] == "travel"
    assert websocket.payloads[0]["session_summary"] == "existing summary"


if __name__ == "__main__":
    # Run tests manually
    print("=" * 60)
    print("Testing Chat Endpoint Utilities")
    print("=" * 60)

    test_sanitize_removes_quoted_user_simulation()
    test_sanitize_truncates_at_role_labels()
    test_sanitize_combined_patterns()
    test_sanitize_edge_cases()
    test_sanitize_multiline_responses()
    test_merge_issues_deduplicates_overlapping_heuristic_items()
    test_build_throttled_feedback_preserves_cached_payload()
    test_build_chat_system_prompt_uses_lesson_frame_defaults()
    test_build_chat_generation_config_filters_stop_sequences()
    test_build_teacher_analysis_fallback_truncates_error_reason()
    test_attach_teacher_analysis_metadata_initializes_payload()
    test_build_teacher_analysis_event_payload_uses_expected_schema()
    test_build_assistant_done_payload_uses_sanitized_content()
    test_generate_teacher_analysis_with_fallback_returns_generated_payload()
    test_generate_teacher_analysis_with_fallback_uses_fallback_on_error()
    test_freeze_user_message_feedback_sends_snapshot_payload()
    test_finalize_assistant_turn_sanitizes_and_emits_final_payload()
    test_persist_and_emit_teacher_analysis_persists_metadata_when_not_fallback()
    test_persist_and_emit_teacher_analysis_skips_db_commit_for_fallback()

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
