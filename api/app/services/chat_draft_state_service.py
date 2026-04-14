"""State store helpers for draft-feedback websocket flows."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ChatDraftStateStore:
    """Mutable in-memory store used by draft websocket handlers."""

    micro_eval_timestamps: dict[str, int] = field(default_factory=dict)
    feedback_cache: dict[str, dict] = field(default_factory=dict)
    last_draft_texts: dict[str, str] = field(default_factory=dict)


def initialize_micro_eval_tracking(store: ChatDraftStateStore, conversation_id: str) -> None:
    """Ensure a conversation has throttle state initialized."""
    if conversation_id not in store.micro_eval_timestamps:
        store.micro_eval_timestamps[conversation_id] = 0


def cache_draft_feedback(
    store: ChatDraftStateStore,
    conversation_id: str,
    draft_text: str,
    feedback: dict,
) -> None:
    """Persist the latest feedback snapshot for throttle reuse."""
    store.feedback_cache[conversation_id] = feedback
    store.last_draft_texts[conversation_id] = draft_text


def build_throttled_feedback(last_feedback: dict, draft_text: str, now_ms: int) -> dict:
    """Return a shallow copy of cached feedback updated for the current draft."""
    updated_feedback = dict(last_feedback)
    updated_feedback["server_ts_ms"] = now_ms
    updated_feedback["draft"] = draft_text
    return updated_feedback
