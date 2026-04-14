import asyncio
from types import SimpleNamespace

from app.services.chat_draft_state_service import ChatDraftStateStore
from app.services.chat_endpoint_adapter_service import (
    make_build_chat_generation_inputs,
    make_build_teacher_analysis_context,
    make_cache_draft_feedback,
    make_evaluate_draft_feedback,
    make_finalize_assistant_turn,
    make_initialize_micro_eval_tracking,
    make_persist_and_emit_teacher_analysis,
)


def test_make_initialize_micro_eval_tracking_binds_store():
    store = ChatDraftStateStore()
    calls = []

    def initialize_tracking(bound_store, conversation_id):
        calls.append((bound_store, conversation_id))

    initialize = make_initialize_micro_eval_tracking(store, initialize_tracking)
    initialize("conv-1")

    assert calls == [(store, "conv-1")]


def test_make_evaluate_draft_feedback_binds_provider_and_grammar_config():
    calls = []

    async def evaluate_feedback(**kwargs):
        calls.append(kwargs)
        return {"type": "draft_feedback"}

    evaluate = make_evaluate_draft_feedback(
        llm_provider="llm-provider",
        grammar_provider="languagetool",
        grammar_url="http://lt",
        evaluate_feedback=evaluate_feedback,
    )

    result = asyncio.run(
        evaluate(
            conversation=SimpleNamespace(id="conv-1"),
            draft_text="hello",
            now_ms=123,
            ghost_suggestion="world",
            include_grammar_check=True,
        )
    )

    assert result == {"type": "draft_feedback"}
    assert calls == [{
        "conversation": SimpleNamespace(id="conv-1"),
        "draft_text": "hello",
        "now_ms": 123,
        "llm_provider": "llm-provider",
        "grammar_provider": "languagetool",
        "grammar_url": "http://lt",
        "ghost_suggestion": "world",
        "include_grammar_check": True,
    }]


def test_make_cache_draft_feedback_binds_store():
    store = ChatDraftStateStore()
    calls = []

    def cache_feedback(bound_store, conversation_id, draft_text, feedback):
        calls.append((bound_store, conversation_id, draft_text, feedback))

    cache = make_cache_draft_feedback(store, cache_feedback)
    cache("conv-1", "hello", {"type": "draft_feedback"})

    assert calls == [(store, "conv-1", "hello", {"type": "draft_feedback"})]


def test_make_build_chat_generation_inputs_binds_helper_functions():
    calls = []

    def build_generation_inputs(**kwargs):
        calls.append(kwargs)
        return ([], "prompt", {"temperature": 0.5})

    build_inputs = make_build_chat_generation_inputs(
        build_generation_inputs=build_generation_inputs,
        build_context="context-fn",
        build_system_prompt="system-prompt-fn",
        build_generation_config="generation-config-fn",
    )

    conversation = SimpleNamespace(id="conv-1")
    db = object()
    result = build_inputs(conversation, db)

    assert result == ([], "prompt", {"temperature": 0.5})
    assert calls == [{
        "conversation": conversation,
        "db": db,
        "build_context": "context-fn",
        "build_system_prompt": "system-prompt-fn",
        "build_generation_config": "generation-config-fn",
    }]


def test_make_build_teacher_analysis_context_binds_teacher_context_lookup():
    calls = []

    def build_teacher_analysis_context(**kwargs):
        calls.append(kwargs)
        return "teacher-context"

    build_context = make_build_teacher_analysis_context(
        build_teacher_analysis_context=build_teacher_analysis_context,
        build_teacher_context_fn="teacher-context-fn",
    )

    conversation = SimpleNamespace(id="conv-1")
    db = object()
    result = build_context(conversation, db, limit=5)

    assert result == "teacher-context"
    assert calls == [{
        "conversation": conversation,
        "db": db,
        "build_teacher_context_fn": "teacher-context-fn",
        "limit": 5,
    }]


def test_make_finalize_assistant_turn_binds_sanitizer():
    calls = []

    async def finalize_turn(**kwargs):
        calls.append(kwargs)
        return "sanitized"

    def sanitize_response(value):
        return value.strip()

    finalize = make_finalize_assistant_turn(finalize_turn, sanitize_response)
    websocket = object()
    db = object()
    conversation = SimpleNamespace(id="conv-1")

    result = asyncio.run(finalize(websocket, db, conversation, " hello "))

    assert result == "sanitized"
    assert calls == [{
        "websocket": websocket,
        "db": db,
        "conversation": conversation,
        "full_response": " hello ",
        "sanitize_response": sanitize_response,
    }]


def test_make_persist_and_emit_teacher_analysis_binds_send_event():
    calls = []

    async def persist_and_emit(**kwargs):
        calls.append(kwargs)

    async def send_event(*args, **kwargs):
        return None

    persist = make_persist_and_emit_teacher_analysis(persist_and_emit, send_event)
    websocket = object()
    db = object()
    conversation = SimpleNamespace(id="conv-1")
    user_message = SimpleNamespace(id="msg-1")

    asyncio.run(
        persist(
            websocket=websocket,
            db=db,
            conversation=conversation,
            user_message=user_message,
            teacher_analysis={"teacher_summary": "ok"},
            used_fallback=False,
        )
    )

    assert calls == [{
        "websocket": websocket,
        "db": db,
        "conversation": conversation,
        "user_message": user_message,
        "teacher_analysis": {"teacher_summary": "ok"},
        "used_fallback": False,
        "send_event": send_event,
    }]
