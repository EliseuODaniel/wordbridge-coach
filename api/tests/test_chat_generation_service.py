import asyncio
from types import SimpleNamespace

from app.services.chat_generation_service import (
    generate_teacher_analysis_with_fallback,
    stream_assistant_response,
)


class FakeWebSocket:
    def __init__(self):
        self.payloads = []

    async def send_json(self, payload):
        self.payloads.append(payload)


def test_stream_assistant_response_aggregates_tokens_and_emits_events():
    class FakeChatProvider:
        model = "fake-chat"

        async def chat_stream(self, messages, system_prompt, generation_config):
            assert messages[-1]["content"] == "hello"
            assert system_prompt == "system"
            assert generation_config["stop"] == ["\nUser:"]
            for token in ["Hi", " there"]:
                yield token

    websocket = FakeWebSocket()

    full_response = asyncio.run(
        stream_assistant_response(
            websocket=websocket,
            conversation_id="conv-1",
            chat_provider=FakeChatProvider(),
            messages=[{"role": "user", "content": "hello"}],
            system_prompt="system",
            generation_config={"stop": ["\nUser:"]},
        )
    )

    assert full_response == "Hi there"
    assert websocket.payloads == [
        {
            "type": "assistant_stream_token",
            "conversation_id": "conv-1",
            "token": "Hi",
        },
        {
            "type": "assistant_stream_token",
            "conversation_id": "conv-1",
            "token": " there",
        },
    ]


def test_generate_teacher_analysis_with_fallback_returns_generated_payload():
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
        lesson_frame_json={"topic": "school"},
        student_profile_json={"feedback_language": "Portuguese"},
    )

    analysis, used_fallback = asyncio.run(
        generate_teacher_analysis_with_fallback(
            teacher_provider=FakeTeacherProvider(),
            conversation=conversation,
            teacher_context="teacher-only context",
            content="I go to school",
            build_fallback=lambda error: {"teacher_summary": str(error)},
        )
    )

    assert used_fallback is False
    assert analysis["teacher_summary"] == "Nice work"


def test_generate_teacher_analysis_with_fallback_uses_fallback_on_error():
    class FailingTeacherProvider:
        model = "fake-teacher"

        async def generate_teacher_analysis(self, user_message, context, lesson_frame, student_profile):
            raise RuntimeError("teacher offline")

    conversation = SimpleNamespace(
        id="conv-1",
        lesson_frame_json={"topic": "school"},
        student_profile_json={"feedback_language": "Portuguese"},
    )

    analysis, used_fallback = asyncio.run(
        generate_teacher_analysis_with_fallback(
            teacher_provider=FailingTeacherProvider(),
            conversation=conversation,
            teacher_context="teacher-only context",
            content="I go to school",
            build_fallback=lambda error: {"teacher_summary": f"fallback:{error}"},
        )
    )

    assert used_fallback is True
    assert analysis["teacher_summary"] == "fallback:teacher offline"
