"""Event-handler helpers for Chat Coach websocket sessions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable

from fastapi import WebSocket
from sqlalchemy.orm import Session

from app.models import ChatConversation, ChatMessage
from app.services.chat_draft_service import (
    ChatDraftFeedbackHelpers,
    ChatDraftFeedbackState,
    process_draft_update,
    process_request_autocomplete,
)
from app.services.chat_draft_state_service import ChatDraftStateStore
from app.services.chat_runtime_service import ChatWebSocketHandlers
from app.services.chat_turn_service import (
    ChatUserMessageTurnHelpers,
    process_user_message_turn,
)


@dataclass
class ChatHandlerDeps:
    """Dependencies used to build websocket event handlers."""

    draft_state_store: ChatDraftStateStore
    micro_eval_min_interval_ms: int
    llm_provider: object
    evaluate_draft_feedback: Callable[..., Awaitable[dict]]
    cache_draft_feedback: Callable[[str, str, dict], None]
    build_throttled_feedback: Callable[[dict, str, int], dict]
    freeze_user_message_feedback: Callable[[WebSocket, ChatConversation, str, object], Awaitable[dict]]
    persist_user_message: Callable[[Session, ChatConversation, str], ChatMessage]
    build_chat_generation_inputs: Callable[..., tuple[list[dict], str, dict]]
    stream_assistant_response: Callable[..., Awaitable[str]]
    finalize_assistant_turn: Callable[[WebSocket, Session, ChatConversation, str], Awaitable[str]]
    build_teacher_analysis_context: Callable[[ChatConversation, Session], str]
    generate_teacher_analysis_with_fallback: Callable[..., Awaitable[tuple[dict, bool]]]
    persist_and_emit_teacher_analysis: Callable[
        [WebSocket, Session, ChatConversation, ChatMessage, dict, bool],
        Awaitable[None],
    ]
    now_ms_factory: Callable[[], int]


def build_chat_handler_deps(
    draft_state_store: ChatDraftStateStore,
    micro_eval_min_interval_ms: int,
    llm_provider,
    evaluate_draft_feedback: Callable[..., Awaitable[dict]],
    cache_draft_feedback: Callable[[str, str, dict], None],
    build_throttled_feedback: Callable[[dict, str, int], dict],
    freeze_user_message_feedback: Callable[[WebSocket, ChatConversation, str, object], Awaitable[dict]],
    persist_user_message: Callable[[Session, ChatConversation, str], ChatMessage],
    build_chat_generation_inputs: Callable[..., tuple[list[dict], str, dict]],
    stream_assistant_response: Callable[..., Awaitable[str]],
    finalize_assistant_turn: Callable[[WebSocket, Session, ChatConversation, str], Awaitable[str]],
    build_teacher_analysis_context: Callable[[ChatConversation, Session], str],
    generate_teacher_analysis_with_fallback: Callable[..., Awaitable[tuple[dict, bool]]],
    persist_and_emit_teacher_analysis: Callable[
        [WebSocket, Session, ChatConversation, ChatMessage, dict, bool],
        Awaitable[None],
    ],
    now_ms_factory: Callable[[], int],
) -> ChatHandlerDeps:
    """Build the dependency bundle used by websocket event handlers."""
    return ChatHandlerDeps(
        draft_state_store=draft_state_store,
        micro_eval_min_interval_ms=micro_eval_min_interval_ms,
        llm_provider=llm_provider,
        evaluate_draft_feedback=evaluate_draft_feedback,
        cache_draft_feedback=cache_draft_feedback,
        build_throttled_feedback=build_throttled_feedback,
        freeze_user_message_feedback=freeze_user_message_feedback,
        persist_user_message=persist_user_message,
        build_chat_generation_inputs=build_chat_generation_inputs,
        stream_assistant_response=stream_assistant_response,
        finalize_assistant_turn=finalize_assistant_turn,
        build_teacher_analysis_context=build_teacher_analysis_context,
        generate_teacher_analysis_with_fallback=generate_teacher_analysis_with_fallback,
        persist_and_emit_teacher_analysis=persist_and_emit_teacher_analysis,
        now_ms_factory=now_ms_factory,
    )


def build_chat_websocket_handlers(deps: ChatHandlerDeps) -> ChatWebSocketHandlers:
    """Build the websocket event-handler bundle for a chat session."""
    return ChatWebSocketHandlers(
        draft_update=lambda websocket, data, conversation, now_ms, db: handle_draft_update_event(
            websocket=websocket,
            data=data,
            conversation=conversation,
            now_ms=now_ms,
            db=db,
            deps=deps,
        ),
        request_autocomplete=lambda websocket, data, conversation, db: handle_request_autocomplete_event(
            websocket=websocket,
            data=data,
            conversation=conversation,
            db=db,
            deps=deps,
        ),
        user_message=lambda websocket, data, conversation, db, chat_provider, teacher_provider: handle_user_message_event(
            websocket=websocket,
            data=data,
            conversation=conversation,
            db=db,
            chat_provider=chat_provider,
            teacher_provider=teacher_provider,
            deps=deps,
        ),
    )


def build_chat_draft_feedback_state(deps: ChatHandlerDeps) -> ChatDraftFeedbackState:
    """Build shared throttle state for draft feedback events."""
    return ChatDraftFeedbackState(
        micro_eval_timestamps=deps.draft_state_store.micro_eval_timestamps,
        feedback_cache=deps.draft_state_store.feedback_cache,
        last_draft_texts=deps.draft_state_store.last_draft_texts,
        min_interval_ms=deps.micro_eval_min_interval_ms,
    )


def build_chat_draft_feedback_helpers(deps: ChatHandlerDeps) -> ChatDraftFeedbackHelpers:
    """Build the draft-feedback helper bundle."""
    return ChatDraftFeedbackHelpers(
        evaluate_draft_feedback=deps.evaluate_draft_feedback,
        cache_draft_feedback=deps.cache_draft_feedback,
        build_throttled_feedback=deps.build_throttled_feedback,
        autocomplete=deps.llm_provider.autocomplete,
    )


def build_chat_user_message_turn_helpers(deps: ChatHandlerDeps) -> ChatUserMessageTurnHelpers:
    """Build the helper bundle for a submitted user message turn."""
    return ChatUserMessageTurnHelpers(
        freeze_feedback=deps.freeze_user_message_feedback,
        persist_user_message=deps.persist_user_message,
        build_generation_inputs=deps.build_chat_generation_inputs,
        stream_assistant_response=deps.stream_assistant_response,
        finalize_assistant_turn=deps.finalize_assistant_turn,
        build_teacher_analysis_context=deps.build_teacher_analysis_context,
        generate_teacher_analysis_with_fallback=deps.generate_teacher_analysis_with_fallback,
        persist_and_emit_teacher_analysis=deps.persist_and_emit_teacher_analysis,
    )


async def handle_draft_update_event(
    websocket: WebSocket,
    data: dict,
    conversation: ChatConversation,
    now_ms: int,
    db: Session,
    deps: ChatHandlerDeps,
) -> None:
    """Handle `draft_update` using shared state and helper builders."""
    await process_draft_update(
        websocket=websocket,
        data=data,
        conversation=conversation,
        now_ms=now_ms,
        db=db,
        state=build_chat_draft_feedback_state(deps),
        helpers=build_chat_draft_feedback_helpers(deps),
    )


async def handle_request_autocomplete_event(
    websocket: WebSocket,
    data: dict,
    conversation: ChatConversation,
    db: Session,
    deps: ChatHandlerDeps,
) -> None:
    """Handle `request_autocomplete` with endpoint-level timestamp injection."""
    request_data = dict(data)
    request_data["now_ms"] = deps.now_ms_factory()

    await process_request_autocomplete(
        websocket=websocket,
        data=request_data,
        conversation=conversation,
        db=db,
        helpers=build_chat_draft_feedback_helpers(deps),
    )


async def handle_user_message_event(
    websocket: WebSocket,
    data: dict,
    conversation: ChatConversation,
    db: Session,
    chat_provider,
    teacher_provider,
    deps: ChatHandlerDeps,
) -> None:
    """Handle `user_message` using the shared turn-orchestration helpers."""
    await process_user_message_turn(
        websocket=websocket,
        data=data,
        conversation=conversation,
        db=db,
        chat_provider=chat_provider,
        teacher_provider=teacher_provider,
        helpers=build_chat_user_message_turn_helpers(deps),
    )
