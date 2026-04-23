from types import SimpleNamespace

from app.services.chat_context_service import (
    build_chat_generation_inputs,
    build_teacher_analysis_context,
)


def test_build_chat_generation_inputs_uses_injected_dependencies():
    conversation = SimpleNamespace(
        id="conv-1",
        lesson_frame_json={"topic": "travel"},
        student_profile_json={"feedback_language": "Portuguese"},
        session_summary="Longitudinal learner profile",
    )
    calls = []

    def fake_build_context(conversation_id, db, limit=10, exclude_system=False):
        calls.append(("context", conversation_id, limit, exclude_system))
        return [{"role": "user", "content": "hello"}]

    def fake_build_system_prompt(lesson_frame, student_profile, session_summary):
        calls.append(("prompt", lesson_frame["topic"], student_profile["feedback_language"], session_summary))
        return "system-prompt"

    def fake_build_generation_config():
        calls.append(("config", None))
        return {"stop": ["\nUser:"]}

    result = build_chat_generation_inputs(
        conversation=conversation,
        db=object(),
        build_context=fake_build_context,
        build_system_prompt=fake_build_system_prompt,
        build_generation_config=fake_build_generation_config,
    )

    assert result == ([{"role": "user", "content": "hello"}], "system-prompt", {"stop": ["\nUser:"]})
    assert calls == [
        ("context", "conv-1", 10, True),
        ("prompt", "travel", "Portuguese", "Longitudinal learner profile"),
        ("config", None),
    ]


def test_build_teacher_analysis_context_prefers_user_messages():
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
    conversation = SimpleNamespace(id="conv-1", session_summary="summary fallback")

    context = build_teacher_analysis_context(
        conversation=conversation,
        db=object(),
        build_teacher_context_fn=lambda conversation_id, db, limit=10: [],
    )

    assert context == "summary fallback"
