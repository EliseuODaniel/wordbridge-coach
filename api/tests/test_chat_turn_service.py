import asyncio
from types import SimpleNamespace

from app.services.chat_turn_service import ChatUserMessageTurnHelpers, process_user_message_turn


def test_process_user_message_turn_orchestrates_steps_in_order():
    websocket = object()
    db = object()
    conversation = SimpleNamespace(id="conv-1")
    user_message = SimpleNamespace(id="msg-1")
    calls = []

    async def freeze_feedback(**kwargs):
        calls.append(("freeze_feedback", kwargs["content"]))
        return {"type": "draft_feedback"}

    def persist_user_message(local_db, local_conversation, content):
        assert local_db is db
        assert local_conversation is conversation
        calls.append(("persist_user_message", content))
        return user_message

    def build_generation_inputs(local_conversation, local_db):
        assert local_conversation is conversation
        assert local_db is db
        calls.append(("build_generation_inputs", None))
        return ([{"role": "user", "content": "hello"}], "system-prompt", {"stop": ["\nUser:"]})

    async def stream_assistant_response(**kwargs):
        calls.append(("stream_assistant_response", kwargs["conversation_id"]))
        assert kwargs["messages"][-1]["content"] == "hello"
        return "assistant raw"

    async def finalize_assistant_turn(**kwargs):
        calls.append(("finalize_assistant_turn", kwargs["full_response"]))
        return "assistant clean"

    def build_teacher_analysis_context(local_conversation, local_db):
        assert local_conversation is conversation
        assert local_db is db
        calls.append(("build_teacher_analysis_context", None))
        return "teacher-context"

    async def generate_teacher_analysis_with_fallback(**kwargs):
        calls.append(("generate_teacher_analysis_with_fallback", kwargs["content"]))
        assert kwargs["teacher_context"] == "teacher-context"
        return ({"teacher_summary": "ok"}, False)

    async def persist_and_emit_teacher_analysis(**kwargs):
        calls.append(("persist_and_emit_teacher_analysis", kwargs["teacher_analysis"]["teacher_summary"]))
        assert kwargs["user_message"] is user_message

    helpers = ChatUserMessageTurnHelpers(
        freeze_feedback=freeze_feedback,
        persist_user_message=persist_user_message,
        build_generation_inputs=build_generation_inputs,
        stream_assistant_response=stream_assistant_response,
        finalize_assistant_turn=finalize_assistant_turn,
        build_teacher_analysis_context=build_teacher_analysis_context,
        generate_teacher_analysis_with_fallback=generate_teacher_analysis_with_fallback,
        persist_and_emit_teacher_analysis=persist_and_emit_teacher_analysis,
    )

    asyncio.run(
        process_user_message_turn(
            websocket=websocket,
            data={"content": "hello"},
            conversation=conversation,
            db=db,
            chat_provider=object(),
            teacher_provider=object(),
            helpers=helpers,
        )
    )

    assert calls == [
        ("freeze_feedback", "hello"),
        ("persist_user_message", "hello"),
        ("build_generation_inputs", None),
        ("stream_assistant_response", "conv-1"),
        ("finalize_assistant_turn", "assistant raw"),
        ("build_teacher_analysis_context", None),
        ("generate_teacher_analysis_with_fallback", "hello"),
        ("persist_and_emit_teacher_analysis", "ok"),
    ]
