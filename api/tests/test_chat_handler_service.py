import asyncio
from types import SimpleNamespace

from app.services.chat_draft_state_service import ChatDraftStateStore
from app.services.chat_handler_service import (
    ChatHandlerDeps,
    build_chat_handler_deps,
    build_chat_draft_feedback_state,
    build_chat_user_message_turn_helpers,
    handle_draft_update_event,
    handle_request_autocomplete_event,
)


class FakeWebSocket:
    def __init__(self):
        self.payloads = []

    async def send_json(self, payload):
        self.payloads.append(payload)


def _build_handler_deps(**overrides):
    store = overrides.pop("draft_state_store", ChatDraftStateStore())

    async def evaluate_draft_feedback(**kwargs):
        return {
            "type": "draft_feedback",
            "draft": kwargs["draft_text"],
            "server_ts_ms": kwargs.get("now_ms"),
            "ghost_suggestion": kwargs.get("ghost_suggestion", ""),
        }

    async def freeze_user_message_feedback(*args, **kwargs):
        return {"type": "draft_feedback"}

    async def stream_assistant_response(*args, **kwargs):
        return "assistant reply"

    async def finalize_assistant_turn(*args, **kwargs):
        return "assistant reply"

    async def generate_teacher_analysis_with_fallback(*args, **kwargs):
        return ({"teacher_summary": "ok"}, False)

    async def persist_and_emit_teacher_analysis(*args, **kwargs):
        return None

    defaults = {
        "draft_state_store": store,
        "micro_eval_min_interval_ms": 90,
        "llm_provider": SimpleNamespace(
            autocomplete=lambda **kwargs: {"ghost_suggestion": "fallback"}
        ),
        "evaluate_draft_feedback": evaluate_draft_feedback,
        "cache_draft_feedback": lambda conversation_id, draft_text, feedback: None,
        "build_throttled_feedback": lambda last_feedback, draft_text, now_ms: {
            **last_feedback,
            "draft": draft_text,
            "server_ts_ms": now_ms,
        },
        "freeze_user_message_feedback": freeze_user_message_feedback,
        "persist_user_message": lambda db, conversation, content: SimpleNamespace(id="msg-1"),
        "build_chat_generation_inputs": lambda conversation, db: ([], "prompt", {}),
        "stream_assistant_response": stream_assistant_response,
        "finalize_assistant_turn": finalize_assistant_turn,
        "build_teacher_analysis_context": lambda conversation, db: "context",
        "generate_teacher_analysis_with_fallback": generate_teacher_analysis_with_fallback,
        "persist_and_emit_teacher_analysis": persist_and_emit_teacher_analysis,
        "now_ms_factory": lambda: 777,
    }
    defaults.update(overrides)
    return ChatHandlerDeps(**defaults)


def test_build_chat_draft_feedback_state_reuses_store_dicts():
    store = ChatDraftStateStore()
    deps = _build_handler_deps(draft_state_store=store, micro_eval_min_interval_ms=123)

    state = build_chat_draft_feedback_state(deps)

    assert state.micro_eval_timestamps is store.micro_eval_timestamps
    assert state.feedback_cache is store.feedback_cache
    assert state.last_draft_texts is store.last_draft_texts
    assert state.min_interval_ms == 123


def test_build_chat_handler_deps_returns_dataclass_with_bound_fields():
    deps = _build_handler_deps(micro_eval_min_interval_ms=123)

    built = build_chat_handler_deps(
        draft_state_store=deps.draft_state_store,
        micro_eval_min_interval_ms=deps.micro_eval_min_interval_ms,
        llm_provider=deps.llm_provider,
        evaluate_draft_feedback=deps.evaluate_draft_feedback,
        cache_draft_feedback=deps.cache_draft_feedback,
        build_throttled_feedback=deps.build_throttled_feedback,
        freeze_user_message_feedback=deps.freeze_user_message_feedback,
        persist_user_message=deps.persist_user_message,
        build_chat_generation_inputs=deps.build_chat_generation_inputs,
        stream_assistant_response=deps.stream_assistant_response,
        finalize_assistant_turn=deps.finalize_assistant_turn,
        build_teacher_analysis_context=deps.build_teacher_analysis_context,
        generate_teacher_analysis_with_fallback=deps.generate_teacher_analysis_with_fallback,
        persist_and_emit_teacher_analysis=deps.persist_and_emit_teacher_analysis,
        now_ms_factory=deps.now_ms_factory,
    )

    assert isinstance(built, ChatHandlerDeps)
    assert built.draft_state_store is deps.draft_state_store
    assert built.micro_eval_min_interval_ms == 123
    assert built.llm_provider is deps.llm_provider
    assert built.now_ms_factory is deps.now_ms_factory


def test_handle_draft_update_event_updates_shared_store_and_sends_feedback():
    websocket = FakeWebSocket()
    store = ChatDraftStateStore()
    cached = []

    async def evaluate_draft_feedback(**kwargs):
        assert kwargs["include_grammar_check"] is True
        return {"type": "draft_feedback", "draft": kwargs["draft_text"]}

    def cache_draft_feedback(conversation_id, draft_text, feedback):
        store.feedback_cache[conversation_id] = feedback
        store.last_draft_texts[conversation_id] = draft_text
        cached.append((conversation_id, draft_text))

    deps = _build_handler_deps(
        draft_state_store=store,
        evaluate_draft_feedback=evaluate_draft_feedback,
        cache_draft_feedback=cache_draft_feedback,
    )

    asyncio.run(
        handle_draft_update_event(
            websocket=websocket,
            data={"draft_text": "hello"},
            conversation=SimpleNamespace(id="conv-1"),
            now_ms=321,
            db=object(),
            deps=deps,
        )
    )

    assert store.micro_eval_timestamps["conv-1"] == 321
    assert cached == [("conv-1", "hello")]
    assert websocket.payloads == [{"type": "draft_feedback", "draft": "hello"}]


def test_handle_request_autocomplete_event_injects_timestamp_and_ghost_suggestion():
    websocket = FakeWebSocket()

    async def autocomplete(**kwargs):
        assert kwargs["draft"] == "I go"
        return {"ghost_suggestion": "to school"}

    async def evaluate_draft_feedback(**kwargs):
        assert kwargs["now_ms"] == 456
        assert kwargs["ghost_suggestion"] == "to school"
        return {"type": "draft_feedback", "ghost_suggestion": "to school"}

    deps = _build_handler_deps(
        llm_provider=SimpleNamespace(autocomplete=autocomplete),
        evaluate_draft_feedback=evaluate_draft_feedback,
        now_ms_factory=lambda: 456,
    )

    asyncio.run(
        handle_request_autocomplete_event(
            websocket=websocket,
            data={"draft_text": "I go"},
            conversation=SimpleNamespace(
                id="conv-1",
                session_summary="summary",
                lesson_frame_json={"topic": "travel"},
                student_profile_json={"cefr_level": "A2"},
            ),
            db=object(),
            deps=deps,
        )
    )

    assert websocket.payloads == [
        {"type": "draft_feedback", "ghost_suggestion": "to school"}
    ]


def test_build_chat_user_message_turn_helpers_preserves_injected_callables():
    deps = _build_handler_deps()

    helpers = build_chat_user_message_turn_helpers(deps)

    assert helpers.freeze_feedback is deps.freeze_user_message_feedback
    assert helpers.persist_user_message is deps.persist_user_message
    assert helpers.build_generation_inputs is deps.build_chat_generation_inputs
    assert helpers.stream_assistant_response is deps.stream_assistant_response
    assert helpers.finalize_assistant_turn is deps.finalize_assistant_turn
    assert helpers.build_teacher_analysis_context is deps.build_teacher_analysis_context
    assert (
        helpers.generate_teacher_analysis_with_fallback
        is deps.generate_teacher_analysis_with_fallback
    )
    assert (
        helpers.persist_and_emit_teacher_analysis
        is deps.persist_and_emit_teacher_analysis
    )
