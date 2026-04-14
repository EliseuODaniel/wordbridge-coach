"""Factory helpers for endpoint-configured Chat Coach adapters."""

from __future__ import annotations

from typing import Awaitable, Callable

from fastapi import WebSocket
from sqlalchemy.orm import Session

from app.models import ChatConversation, ChatMessage
from app.services.chat_draft_state_service import ChatDraftStateStore


def make_initialize_micro_eval_tracking(
    draft_state_store: ChatDraftStateStore,
    initialize_tracking: Callable[[ChatDraftStateStore, str], None],
) -> Callable[[str], None]:
    """Bind the draft-state store to the shared tracking initializer."""

    def _initialize_micro_eval_tracking(conversation_id: str) -> None:
        initialize_tracking(draft_state_store, conversation_id)

    return _initialize_micro_eval_tracking


def make_evaluate_draft_feedback(
    llm_provider,
    grammar_provider: str,
    grammar_url: str,
    evaluate_feedback: Callable[..., Awaitable[dict]],
) -> Callable[..., Awaitable[dict]]:
    """Bind provider/config dependencies to draft-feedback evaluation."""

    async def _evaluate_draft_feedback(
        conversation: ChatConversation,
        draft_text: str,
        now_ms: int,
        ghost_suggestion: str | None = None,
        include_grammar_check: bool = False,
    ) -> dict:
        return await evaluate_feedback(
            conversation=conversation,
            draft_text=draft_text,
            now_ms=now_ms,
            llm_provider=llm_provider,
            grammar_provider=grammar_provider,
            grammar_url=grammar_url,
            ghost_suggestion=ghost_suggestion,
            include_grammar_check=include_grammar_check,
        )

    return _evaluate_draft_feedback


def make_cache_draft_feedback(
    draft_state_store: ChatDraftStateStore,
    cache_feedback: Callable[[ChatDraftStateStore, str, str, dict], None],
) -> Callable[[str, str, dict], None]:
    """Bind the draft-state store to feedback-cache writes."""

    def _cache_draft_feedback(conversation_id: str, draft_text: str, feedback: dict) -> None:
        cache_feedback(draft_state_store, conversation_id, draft_text, feedback)

    return _cache_draft_feedback


def make_build_chat_generation_inputs(
    build_generation_inputs: Callable[..., tuple[list[dict], str, dict]],
    build_context: Callable[[str, Session, int, bool], list[dict]],
    build_system_prompt: Callable[[dict], str],
    build_generation_config: Callable[[], dict],
) -> Callable[[ChatConversation, Session], tuple[list[dict], str, dict]]:
    """Bind endpoint-local helper callables to generation input building."""

    def _build_chat_generation_inputs(
        conversation: ChatConversation,
        db: Session,
    ) -> tuple[list[dict], str, dict]:
        return build_generation_inputs(
            conversation=conversation,
            db=db,
            build_context=build_context,
            build_system_prompt=build_system_prompt,
            build_generation_config=build_generation_config,
        )

    return _build_chat_generation_inputs


def make_build_teacher_analysis_context(
    build_teacher_analysis_context: Callable[..., str],
    build_teacher_context_fn: Callable[[str, Session, int], list[dict]],
) -> Callable[[ChatConversation, Session, int], str]:
    """Bind teacher-context lookup to the shared analysis-context builder."""

    def _build_teacher_analysis_context(
        conversation: ChatConversation,
        db: Session,
        limit: int = 10,
    ) -> str:
        return build_teacher_analysis_context(
            conversation=conversation,
            db=db,
            build_teacher_context_fn=build_teacher_context_fn,
            limit=limit,
        )

    return _build_teacher_analysis_context


def make_freeze_user_message_feedback(
    freeze_feedback: Callable[..., Awaitable[dict]],
) -> Callable[[WebSocket, ChatConversation, str, object], Awaitable[dict]]:
    """Expose a stable endpoint-shaped callable for frozen feedback."""

    async def _freeze_user_message_feedback(
        websocket: WebSocket,
        conversation: ChatConversation,
        content: str,
        chat_provider,
    ) -> dict:
        return await freeze_feedback(
            websocket=websocket,
            conversation=conversation,
            content=content,
            chat_provider=chat_provider,
        )

    return _freeze_user_message_feedback


def make_stream_assistant_response(
    stream_response: Callable[..., Awaitable[str]],
) -> Callable[[WebSocket, str, object, list[dict], str, dict], Awaitable[str]]:
    """Expose a stable endpoint-shaped callable for assistant streaming."""

    async def _stream_assistant_response(
        websocket: WebSocket,
        conversation_id: str,
        chat_provider,
        messages: list[dict],
        system_prompt: str,
        generation_config: dict,
    ) -> str:
        return await stream_response(
            websocket=websocket,
            conversation_id=conversation_id,
            chat_provider=chat_provider,
            messages=messages,
            system_prompt=system_prompt,
            generation_config=generation_config,
        )

    return _stream_assistant_response


def make_generate_teacher_analysis_with_fallback(
    generate_analysis: Callable[..., Awaitable[tuple[dict, bool]]],
    build_fallback: Callable[[Exception], dict],
) -> Callable[[object, ChatConversation, str, str], Awaitable[tuple[dict, bool]]]:
    """Bind fallback creation to teacher-analysis generation."""

    async def _generate_teacher_analysis_with_fallback(
        teacher_provider,
        conversation: ChatConversation,
        teacher_context: str,
        content: str,
    ) -> tuple[dict, bool]:
        return await generate_analysis(
            teacher_provider=teacher_provider,
            conversation=conversation,
            teacher_context=teacher_context,
            content=content,
            build_fallback=build_fallback,
        )

    return _generate_teacher_analysis_with_fallback


def make_send_teacher_analysis_event(
    send_event: Callable[[WebSocket, str, str, dict], Awaitable[None]],
) -> Callable[[WebSocket, str, str, dict], Awaitable[None]]:
    """Expose a stable endpoint-shaped callable for teacher-analysis delivery."""

    async def _send_teacher_analysis_event(
        websocket: WebSocket,
        conversation_id: str,
        user_message_id: str,
        analysis: dict,
    ) -> None:
        await send_event(
            websocket=websocket,
            conversation_id=conversation_id,
            user_message_id=user_message_id,
            analysis=analysis,
        )

    return _send_teacher_analysis_event


def make_finalize_assistant_turn(
    finalize_turn: Callable[..., Awaitable[str]],
    sanitize_response: Callable[[str], str],
) -> Callable[[WebSocket, Session, ChatConversation, str], Awaitable[str]]:
    """Bind response sanitization to the assistant-turn finalizer."""

    async def _finalize_assistant_turn(
        websocket: WebSocket,
        db: Session,
        conversation: ChatConversation,
        full_response: str,
    ) -> str:
        return await finalize_turn(
            websocket=websocket,
            db=db,
            conversation=conversation,
            full_response=full_response,
            sanitize_response=sanitize_response,
        )

    return _finalize_assistant_turn


def make_persist_and_emit_teacher_analysis(
    persist_and_emit: Callable[..., Awaitable[None]],
    send_event: Callable[[WebSocket, str, str, dict], Awaitable[None]],
) -> Callable[[WebSocket, Session, ChatConversation, ChatMessage, dict, bool], Awaitable[None]]:
    """Bind the teacher-analysis event sender to the persistence helper."""

    async def _persist_and_emit_teacher_analysis(
        websocket: WebSocket,
        db: Session,
        conversation: ChatConversation,
        user_message: ChatMessage,
        teacher_analysis: dict,
        used_fallback: bool,
    ) -> None:
        await persist_and_emit(
            websocket=websocket,
            db=db,
            conversation=conversation,
            user_message=user_message,
            teacher_analysis=teacher_analysis,
            used_fallback=used_fallback,
            send_event=send_event,
        )

    return _persist_and_emit_teacher_analysis
