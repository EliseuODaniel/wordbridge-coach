import asyncio
from types import SimpleNamespace

from app.services.chat_draft_service import (
    ChatDraftFeedbackHelpers,
    ChatDraftFeedbackState,
    process_draft_update,
    process_request_autocomplete,
    should_run_micro_eval,
)


class FakeWebSocket:
    def __init__(self):
        self.payloads = []

    async def send_json(self, payload):
        self.payloads.append(payload)


def test_should_not_run_micro_eval_when_text_changes_inside_interval():
    assert should_run_micro_eval(
        last_draft_text="old",
        draft_text="new",
        now_ms=100,
        last_eval_ts=90,
        min_interval_ms=1000,
    ) is False


def test_should_not_run_micro_eval_when_interval_passed_but_text_is_unchanged():
    assert should_run_micro_eval(
        last_draft_text="same",
        draft_text="same",
        now_ms=500,
        last_eval_ts=0,
        min_interval_ms=100,
    ) is False


def test_should_run_micro_eval_for_changed_text_after_interval():
    assert should_run_micro_eval(
        last_draft_text="old",
        draft_text="new",
        now_ms=500,
        last_eval_ts=0,
        min_interval_ms=100,
    ) is True


def test_should_run_micro_eval_false_when_throttled_and_unchanged():
    assert should_run_micro_eval(
        last_draft_text="same",
        draft_text="same",
        now_ms=50,
        last_eval_ts=0,
        min_interval_ms=100,
    ) is False


def test_process_draft_update_runs_fresh_feedback_and_updates_state():
    websocket = FakeWebSocket()
    state = ChatDraftFeedbackState(
        micro_eval_timestamps={},
        feedback_cache={},
        last_draft_texts={},
        min_interval_ms=90,
    )
    cached = []

    async def evaluate_draft_feedback(**kwargs):
        assert kwargs["include_grammar_check"] is True
        return {"type": "draft_feedback", "draft": kwargs["draft_text"]}

    def cache_draft_feedback(conversation_id, draft_text, feedback):
        state.feedback_cache[conversation_id] = feedback
        state.last_draft_texts[conversation_id] = draft_text
        cached.append((conversation_id, draft_text, feedback))

    helpers = ChatDraftFeedbackHelpers(
        evaluate_draft_feedback=evaluate_draft_feedback,
        cache_draft_feedback=cache_draft_feedback,
        build_throttled_feedback=lambda last_feedback, draft_text, now_ms: {},
        autocomplete=None,
    )

    asyncio.run(
        process_draft_update(
            websocket=websocket,
            data={"draft_text": "hello"},
            conversation=SimpleNamespace(id="conv-1"),
            now_ms=123,
            db=object(),
            state=state,
            helpers=helpers,
        )
    )

    assert state.micro_eval_timestamps["conv-1"] == 123
    assert cached[0][0] == "conv-1"
    assert websocket.payloads == [{"type": "draft_feedback", "draft": "hello"}]


def test_process_draft_update_reuses_cached_feedback_when_throttled():
    websocket = FakeWebSocket()
    state = ChatDraftFeedbackState(
        micro_eval_timestamps={"conv-1": 100},
        feedback_cache={"conv-1": {"type": "draft_feedback", "draft": "old", "server_ts_ms": 100}},
        last_draft_texts={"conv-1": "same"},
        min_interval_ms=1000,
    )

    async def evaluate_draft_feedback(**kwargs):
        raise AssertionError("fresh evaluation should not run when throttled")

    helpers = ChatDraftFeedbackHelpers(
        evaluate_draft_feedback=evaluate_draft_feedback,
        cache_draft_feedback=lambda *args: None,
        build_throttled_feedback=lambda last_feedback, draft_text, now_ms: {
            **last_feedback,
            "draft": draft_text,
            "server_ts_ms": now_ms,
        },
        autocomplete=None,
    )

    asyncio.run(
        process_draft_update(
            websocket=websocket,
            data={"draft_text": "same"},
            conversation=SimpleNamespace(id="conv-1"),
            now_ms=120,
            db=object(),
            state=state,
            helpers=helpers,
        )
    )

    assert websocket.payloads == [
        {"type": "draft_feedback", "draft": "same", "server_ts_ms": 120}
    ]


def test_process_request_autocomplete_uses_ghost_suggestion():
    websocket = FakeWebSocket()
    conversation = SimpleNamespace(
        id="conv-1",
        session_summary="summary",
        lesson_frame_json={"topic": "travel"},
        student_profile_json={"cefr_level": "A2"},
    )

    async def autocomplete(**kwargs):
        assert kwargs["draft"] == "I go"
        return {"ghost_suggestion": "to school"}

    async def evaluate_draft_feedback(**kwargs):
        assert kwargs["ghost_suggestion"] == "to school"
        assert kwargs["include_grammar_check"] is True
        return {"type": "draft_feedback", "ghost_suggestion": "to school"}

    helpers = ChatDraftFeedbackHelpers(
        evaluate_draft_feedback=evaluate_draft_feedback,
        cache_draft_feedback=lambda *args: None,
        build_throttled_feedback=lambda *args: {},
        autocomplete=autocomplete,
    )

    asyncio.run(
        process_request_autocomplete(
            websocket=websocket,
            data={"draft_text": "I go", "now_ms": 456},
            conversation=conversation,
            db=object(),
            helpers=helpers,
        )
    )

    assert websocket.payloads == [
        {"type": "draft_feedback", "ghost_suggestion": "to school"}
    ]
