"""Draft-feedback orchestration helpers for Chat Coach websocket events."""

from dataclasses import dataclass
from typing import Awaitable, Callable

from fastapi import WebSocket
from sqlalchemy.orm import Session

from app.models import ChatConversation


@dataclass
class ChatDraftFeedbackState:
    """Mutable state used to throttle and reuse draft feedback."""

    micro_eval_timestamps: dict
    feedback_cache: dict
    last_draft_texts: dict
    min_interval_ms: int


@dataclass
class ChatDraftFeedbackHelpers:
    """Dependencies used by draft-related websocket handlers."""

    evaluate_draft_feedback: Callable[..., Awaitable[dict]]
    cache_draft_feedback: Callable[[str, str, dict], None]
    build_throttled_feedback: Callable[[dict, str, int], dict]
    autocomplete: Callable[..., Awaitable[dict]]


def should_run_micro_eval(
    last_draft_text: str,
    draft_text: str,
    now_ms: int,
    last_eval_ts: int,
    min_interval_ms: int,
) -> bool:
    """Decide whether a new micro-eval should run for the current draft."""
    text_changed = draft_text != last_draft_text
    time_passed_enough = (now_ms - last_eval_ts) >= min_interval_ms
    return text_changed and time_passed_enough


async def process_draft_update(
    websocket: WebSocket,
    data: dict,
    conversation: ChatConversation,
    now_ms: int,
    db: Session,
    state: ChatDraftFeedbackState,
    helpers: ChatDraftFeedbackHelpers,
) -> None:
    """Handle `draft_update` with throttle-aware feedback reuse."""
    del db

    draft_text = data.get("draft_text", "")
    conversation_id = str(conversation.id)
    last_draft_text = state.last_draft_texts.get(conversation_id, "")
    last_eval_ts = state.micro_eval_timestamps.get(conversation_id, 0)

    should_run = should_run_micro_eval(
        last_draft_text=last_draft_text,
        draft_text=draft_text,
        now_ms=now_ms,
        last_eval_ts=last_eval_ts,
        min_interval_ms=state.min_interval_ms,
    )

    if should_run:
        state.micro_eval_timestamps[conversation_id] = now_ms
        feedback = await helpers.evaluate_draft_feedback(
            conversation=conversation,
            draft_text=draft_text,
            now_ms=now_ms,
            include_grammar_check=True,
        )
        helpers.cache_draft_feedback(conversation_id, draft_text, feedback)
        await websocket.send_json(feedback)
        return

    last_feedback = state.feedback_cache.get(conversation_id)
    if last_feedback:
        await websocket.send_json(
            helpers.build_throttled_feedback(last_feedback, draft_text, now_ms)
        )


async def process_request_autocomplete(
    websocket: WebSocket,
    data: dict,
    conversation: ChatConversation,
    db: Session,
    helpers: ChatDraftFeedbackHelpers,
) -> None:
    """Handle `request_autocomplete` and return feedback with ghost suggestion."""
    del db

    draft_text = data.get("draft_text", "")
    autocomplete_result = await helpers.autocomplete(
        context=conversation.session_summary,
        lesson_frame=conversation.lesson_frame_json,
        draft=draft_text,
        student_profile=conversation.student_profile_json,
    )

    feedback = await helpers.evaluate_draft_feedback(
        conversation=conversation,
        draft_text=draft_text,
        now_ms=data.get("now_ms"),
        ghost_suggestion=autocomplete_result.get("ghost_suggestion", ""),
        include_grammar_check=True,
    )

    await websocket.send_json(feedback)
