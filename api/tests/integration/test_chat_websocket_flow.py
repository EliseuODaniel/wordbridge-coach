import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.api_v1.endpoints import chat as chat_endpoint
from app.services import chat_runtime_service
from app.main import app
from app.models import ChatConversation, ChatLessonHistory, ChatMessage, Language, User


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

    async def generate_teacher_analysis(self, user_message, context, lesson_frame, student_profile):
        assert user_message == "I go to school yesterday"
        assert "I go to school yesterday" in context
        assert lesson_frame["topic"] == "travel"
        assert student_profile["feedback_language"] == "Portuguese"
        return {
            "teacher_summary": "Good attempt. Watch the past tense.",
            "rewrite": "I went to school yesterday.",
            "corrections": [{"mistake": "go", "fix": "went", "why": "Use the past form after 'yesterday'."}],
            "strengths": ["The message is easy to understand."],
            "focus_areas": ["Switch irregular verbs to past tense in past-time sentences."],
            "next_practice": ["past simple"],
            "reflection_question": "Which word in your sentence signals that the action happened in the past?",
            "encouragement": "You are very close. Try the same idea once more with the corrected verb.",
        }


def test_chat_websocket_user_message_flow(db_session, monkeypatch):
    session = db_session
    code_seed = uuid.uuid4().hex
    native_suffix = code_seed[0]
    target_suffix = next(char for char in code_seed[1:] if char != native_suffix)
    native_code = f"q{native_suffix}"
    target_code = f"q{target_suffix}"

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
        student_profile_json={"cefr_level": "A2", "feedback_language": "Portuguese"},
        lesson_frame_json={"cefr_target": "A2", "topic": "travel", "learning_goal": "past_simple"},
        session_summary="session-summary",
    )
    session.add_all([native_language, target_language, user, conversation])
    session.commit()
    conversation_id = conversation.id

    def test_session_factory():
        return Session(bind=db_session.connection())

    monkeypatch.setattr(chat_endpoint, "websocket_session_factory", test_session_factory)

    monkeypatch.setattr(
        chat_runtime_service,
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
        chat_runtime_service,
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
        assert teacher_analysis["student_profile"]["feedback_language"] == "Portuguese"
        assert teacher_analysis["student_profile"]["pedagogical_metrics"]["recommended_pace"] in {
            "stabilize",
            "balance",
            "accelerate",
        }
        assert teacher_analysis["lesson_frame"]["primary_focus"] == (
            "Switch irregular verbs to past tense in past-time sentences."
        )
        assert teacher_analysis["lesson_frame"]["diagnostics"]["difficulty_signal"] in {
            "support_needed",
            "on_target",
            "ready_to_push",
        }
        assert "Longitudinal learner profile" in teacher_analysis["session_summary"]

        verify_session = test_session_factory()
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
            refreshed_conversation = verify_session.query(ChatConversation).filter(
                ChatConversation.id == conversation_id
            ).first()
            assert refreshed_conversation.student_profile_json["recent_topics"][0] == "travel"
            lesson_history = (
                verify_session.query(ChatLessonHistory)
                .filter(ChatLessonHistory.conversation_id == conversation_id)
                .all()
            )
            assert len(lesson_history) == 1
            assert lesson_history[0].lesson_frame_json["topic"] == "travel"
        finally:
            verify_session.close()
    finally:
        client.close()
