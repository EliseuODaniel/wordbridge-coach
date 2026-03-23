import uuid

from fastapi.testclient import TestClient

from app.api.api_v1.endpoints import chat as chat_endpoint
from app.core.database import SessionLocal
from app.main import app
from app.models import ChatConversation, ChatMessage, Language, User


class FakeChatProvider:
    model = "fake-chat"

    async def micro_eval(self, context, lesson_frame, draft, student_profile):
        assert context == "session-summary"
        assert lesson_frame["topic"] == "travel"
        assert draft == "I go to school yesterday"
        assert student_profile["cefr_level"] == "A2"
        return {
            "spelling_score": 95,
            "grammar_score": 70,
            "lesson_alignment_score": 88,
            "naturalness_score": 82,
            "top_issues": [
                {
                    "category": "grammar",
                    "title": "Verb tense",
                    "explanation": "Use past simple with yesterday.",
                    "highlight_spans": [{"start": 2, "end": 4}],
                    "suggestions": ["went"],
                }
            ],
            "suggested_next_words": ["to"],
            "topic": "travel",
            "intent": "past_experience",
        }

    async def chat_stream(self, messages, system_prompt, generation_config):
        assert messages[-1]["role"] == "user"
        assert messages[-1]["content"] == "I go to school yesterday"
        assert "Always ask a follow-up question" in system_prompt
        assert "\nUser:" in generation_config["stop"]

        yield "Nice! What happened next?"
        yield "\n\n\"I went home.\""


class FakeTeacherProvider:
    model = "fake-teacher"

    async def generate_teacher_analysis(self, user_message, context, lesson_frame):
        assert user_message == "I go to school yesterday"
        assert context == "I go to school yesterday"
        assert lesson_frame["topic"] == "travel"
        return {
            "teacher_summary": "Good attempt. Watch the past tense.",
            "rewrite": "I went to school yesterday.",
            "corrections": [{"mistake": "go", "correction": "went"}],
            "next_practice": ["past simple"],
        }


def test_chat_websocket_user_message_flow(db, monkeypatch):
    session = SessionLocal()
    code_seed = uuid.uuid4().hex
    native_code = f"q{code_seed[0]}"
    target_code = f"q{code_seed[1] if code_seed[1] != code_seed[0] else code_seed[2]}"

    native_language = Language(
        code=native_code,
        name="QA Native",
        voice_model="lessac-glow_tts",
        voice_type="female",
        is_active=True,
    )
    target_language = Language(
        code=target_code,
        name="QA Target",
        voice_model="lessac-glow_tts",
        voice_type="female",
        is_active=True,
    )
    user = User(
        username=f"chat_ws_{uuid.uuid4().hex[:8]}",
        email=f"chat_ws_{uuid.uuid4().hex[:8]}@example.com",
        language_preference="pt",
        native_language_obj=native_language,
        target_language_obj=target_language,
        daily_new_limit=10,
        easiness_factor=2.5,
        word_goal_rank=100,
    )
    conversation = ChatConversation(
        user=user,
        title="WebSocket Chat",
        student_profile_json={"cefr_level": "A2"},
        lesson_frame_json={"cefr_target": "A2", "topic": "travel", "learning_goal": "past_simple"},
        session_summary="session-summary",
    )
    session.add_all([native_language, target_language, user, conversation])
    session.commit()
    conversation_id = conversation.id
    session.close()

    monkeypatch.setattr(
        chat_endpoint,
        "get_user_model_profiles",
        lambda db, user_id: {
            "chat_model_profile": "chat-profile",
            "teacher_model_profile": "teacher-profile",
        },
    )

    def fake_get_provider_for_profile(profile_id):
        if profile_id == "chat-profile":
            return FakeChatProvider()
        if profile_id == "teacher-profile":
            return FakeTeacherProvider()
        raise AssertionError(f"Unexpected profile id: {profile_id}")

    monkeypatch.setattr(
        chat_endpoint,
        "get_llm_provider_for_profile",
        fake_get_provider_for_profile,
    )

    client = TestClient(app)

    try:
        with client.websocket_connect(f"/api/v1/chat/ws/{conversation_id}") as websocket:
            websocket.send_json({
                "type": "user_message",
                "conversation_id": str(conversation_id),
                "content": "I go to school yesterday",
                "client_ts_ms": 123456,
            })

            events = []
            while len(events) < 5:
                event = websocket.receive_json()
                events.append(event)
                if event["type"] == "teacher_analysis":
                    break

        assert [event["type"] for event in events] == [
            "draft_feedback",
            "assistant_stream_token",
            "assistant_stream_token",
            "assistant_done",
            "teacher_analysis",
        ]

        draft_feedback = events[0]
        assistant_done = events[3]
        teacher_analysis = events[4]

        assert draft_feedback["draft"] == "I go to school yesterday"
        assert draft_feedback["issues"][0]["suggestions"] == ["went"]
        assert assistant_done["full_content"] == "Nice! What happened next?"
        assert teacher_analysis["analysis"]["rewrite"] == "I went to school yesterday."

        verify_session = SessionLocal()
        try:
            persisted_messages = (
                verify_session.query(ChatMessage)
                .filter(ChatMessage.conversation_id == conversation_id)
                .order_by(ChatMessage.created_at.asc())
                .all()
            )

            assert [message.role for message in persisted_messages] == ["user", "assistant"]
            assert persisted_messages[1].content == "Nice! What happened next?"
            assert (
                persisted_messages[0].metadata_json["teacher_analysis"]["teacher_summary"]
                == "Good attempt. Watch the past tense."
            )
        finally:
            verify_session.close()
    finally:
        client.close()
