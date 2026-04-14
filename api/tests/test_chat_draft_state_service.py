from app.services.chat_draft_state_service import (
    ChatDraftStateStore,
    build_throttled_feedback,
    cache_draft_feedback,
    initialize_micro_eval_tracking,
)


def test_initialize_micro_eval_tracking_sets_default_once():
    store = ChatDraftStateStore()

    initialize_micro_eval_tracking(store, "conv-1")
    initialize_micro_eval_tracking(store, "conv-1")

    assert store.micro_eval_timestamps == {"conv-1": 0}


def test_cache_draft_feedback_updates_store():
    store = ChatDraftStateStore()
    feedback = {"draft": "hello", "server_ts_ms": 1}

    cache_draft_feedback(store, "conv-1", "hello", feedback)

    assert store.feedback_cache == {"conv-1": feedback}
    assert store.last_draft_texts == {"conv-1": "hello"}


def test_build_throttled_feedback_preserves_cached_payload():
    cached_feedback = {
        "conversation_id": "conv-1",
        "draft": "old text",
        "server_ts_ms": 1000,
        "issues": [{"category": "grammar"}],
    }

    updated = build_throttled_feedback(cached_feedback, "new text", 2000)

    assert updated["draft"] == "new text"
    assert updated["server_ts_ms"] == 2000
    assert updated["issues"] == cached_feedback["issues"]
    assert cached_feedback["draft"] == "old text"
    assert cached_feedback["server_ts_ms"] == 1000
