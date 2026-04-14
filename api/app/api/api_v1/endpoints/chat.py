"""Chat Coach endpoints for real-time conversational training"""

import os
import logging
from typing import List
from fastapi import APIRouter, HTTPException, Depends, status, WebSocket
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.core.database import get_db
from app.schemas.chat import (
    ChatConversationCreate,
    ChatConversationResponse,
)
from app.llm.factory import get_llm_provider_from_env, get_provider_name
from app.services.chat_runtime_service import (
    build_chat_websocket_runtime,
    build_ws_error_payload as _build_ws_error_payload,
    route_websocket_event,
)
from app.services.chat_handler_service import (
    build_chat_handler_deps,
    build_chat_websocket_handlers,
)
from app.services.chat_websocket_service import (
    build_chat_websocket_session_deps,
    default_now_ms,
    run_chat_websocket_session,
)
from app.services.chat_draft_state_service import (
    ChatDraftStateStore,
    build_throttled_feedback as _build_throttled_feedback_service,
    cache_draft_feedback as _cache_draft_feedback_service,
    initialize_micro_eval_tracking as _initialize_micro_eval_tracking_service,
)
from app.services.chat_endpoint_adapter_service import (
    make_build_chat_generation_inputs,
    make_build_teacher_analysis_context,
    make_cache_draft_feedback,
    make_evaluate_draft_feedback,
    make_finalize_assistant_turn,
    make_freeze_user_message_feedback,
    make_generate_teacher_analysis_with_fallback,
    make_initialize_micro_eval_tracking,
    make_persist_and_emit_teacher_analysis,
    make_send_teacher_analysis_event,
    make_stream_assistant_response,
)
from app.services.chat_feedback_service import (
    build_draft_feedback as _build_draft_feedback,
    evaluate_draft_feedback,
    freeze_user_message_feedback,
    generate_micro_tip as _generate_micro_tip,
    get_grammar_issues as _get_grammar_issues,
    merge_issues as _merge_issues,
)
from app.services.chat_context_service import (
    build_chat_generation_inputs as _build_chat_generation_inputs_service,
    build_context_messages as _build_context_messages_service,
    build_teacher_analysis_context as _build_teacher_analysis_context_service,
    build_teacher_context as _build_teacher_context_service,
)
from app.services.chat_text_service import (
    build_chat_generation_config as _build_chat_generation_config_service,
    build_chat_system_prompt as _build_chat_system_prompt_service,
    build_teacher_analysis_fallback as _build_teacher_analysis_fallback_service,
    sanitize_assistant_response as _sanitize_assistant_response_service,
)
from app.services.chat_generation_service import (
    generate_teacher_analysis_with_fallback as _generate_teacher_analysis_with_fallback_service,
    stream_assistant_response as _stream_assistant_response_service,
)
from app.services.chat_delivery_service import (
    attach_teacher_analysis_metadata as _attach_teacher_analysis_metadata,
    build_assistant_done_payload as _build_assistant_done_payload,
    build_teacher_analysis_event_payload as _build_teacher_analysis_event_payload,
    finalize_assistant_turn as _finalize_assistant_turn_service,
    persist_and_emit_teacher_analysis as _persist_and_emit_teacher_analysis_service,
    persist_assistant_message as _persist_assistant_message,
    persist_user_message as _persist_user_message,
    send_teacher_analysis_event as _send_teacher_analysis_event_service,
)
from app.services.chat_conversation_service import (
    create_chat_conversation,
    delete_chat_conversation,
    list_chat_conversations,
    list_chat_messages,
)

# Feature flags (environment variables)
CHAT_LLM_PROVIDER = os.getenv("CHAT_LLM_PROVIDER", "llamacpp")
CHAT_MICRO_EVAL_MIN_INTERVAL_MS = int(os.getenv("CHAT_MICRO_EVAL_MIN_INTERVAL_MS", "90"))
CHAT_DRAFT_GRAMMAR_PROVIDER = os.getenv("CHAT_DRAFT_GRAMMAR_PROVIDER", "heuristic")
CHAT_LANGUAGETOOL_URL = os.getenv("CHAT_LANGUAGETOOL_URL", "http://languagetool:8010")

router = APIRouter()

# Initialize LLM provider from environment variables (supports Mock, OpenAI, LlamaCpp)
llm_provider = get_llm_provider_from_env()

# Log which provider is being used (for debugging)
logger.info(f"Chat Coach LLM provider: {get_provider_name(llm_provider)}")

_draft_state_store = ChatDraftStateStore()


async def _send_ws_error(websocket: WebSocket, message: str, code: str) -> None:
    """Send a standardized websocket error payload."""
    await websocket.send_json(_build_ws_error_payload(message=message, code=code))


_initialize_micro_eval_tracking = make_initialize_micro_eval_tracking(
    draft_state_store=_draft_state_store,
    initialize_tracking=_initialize_micro_eval_tracking_service,
)
_evaluate_draft_feedback = make_evaluate_draft_feedback(
    llm_provider=llm_provider,
    grammar_provider=CHAT_DRAFT_GRAMMAR_PROVIDER,
    grammar_url=CHAT_LANGUAGETOOL_URL,
    evaluate_feedback=evaluate_draft_feedback,
)
_cache_draft_feedback = make_cache_draft_feedback(
    draft_state_store=_draft_state_store,
    cache_feedback=_cache_draft_feedback_service,
)
_build_throttled_feedback = _build_throttled_feedback_service
_build_chat_system_prompt = _build_chat_system_prompt_service


def _get_chat_stop_sequences() -> List[str]:
    """Return sanitized stop sequences for chat generation."""
    return _build_chat_generation_config_service()["stop"]


_build_chat_generation_config = _build_chat_generation_config_service
_build_teacher_analysis_fallback = _build_teacher_analysis_fallback_service
_sanitize_assistant_response = _sanitize_assistant_response_service


_build_context_messages = _build_context_messages_service
_build_teacher_context = _build_teacher_context_service


_build_chat_generation_inputs = make_build_chat_generation_inputs(
    build_generation_inputs=_build_chat_generation_inputs_service,
    build_context=_build_context_messages,
    build_system_prompt=_build_chat_system_prompt,
    build_generation_config=_build_chat_generation_config,
)
_build_teacher_analysis_context = make_build_teacher_analysis_context(
    build_teacher_analysis_context=_build_teacher_analysis_context_service,
    build_teacher_context_fn=_build_teacher_context,
)
_freeze_user_message_feedback = make_freeze_user_message_feedback(
    freeze_feedback=freeze_user_message_feedback,
)
_stream_assistant_response = make_stream_assistant_response(
    stream_response=_stream_assistant_response_service,
)
_generate_teacher_analysis_with_fallback = make_generate_teacher_analysis_with_fallback(
    generate_analysis=_generate_teacher_analysis_with_fallback_service,
    build_fallback=_build_teacher_analysis_fallback,
)
_send_teacher_analysis_event = make_send_teacher_analysis_event(
    send_event=_send_teacher_analysis_event_service,
)
_finalize_assistant_turn = make_finalize_assistant_turn(
    finalize_turn=_finalize_assistant_turn_service,
    sanitize_response=_sanitize_assistant_response,
)
_persist_and_emit_teacher_analysis = make_persist_and_emit_teacher_analysis(
    persist_and_emit=_persist_and_emit_teacher_analysis_service,
    send_event=_send_teacher_analysis_event,
)


_chat_handler_deps = build_chat_handler_deps(
    draft_state_store=_draft_state_store,
    micro_eval_min_interval_ms=CHAT_MICRO_EVAL_MIN_INTERVAL_MS,
    llm_provider=llm_provider,
    evaluate_draft_feedback=_evaluate_draft_feedback,
    cache_draft_feedback=_cache_draft_feedback,
    build_throttled_feedback=_build_throttled_feedback,
    freeze_user_message_feedback=_freeze_user_message_feedback,
    persist_user_message=_persist_user_message,
    build_chat_generation_inputs=_build_chat_generation_inputs,
    stream_assistant_response=_stream_assistant_response,
    finalize_assistant_turn=_finalize_assistant_turn,
    build_teacher_analysis_context=_build_teacher_analysis_context,
    generate_teacher_analysis_with_fallback=_generate_teacher_analysis_with_fallback,
    persist_and_emit_teacher_analysis=_persist_and_emit_teacher_analysis,
    now_ms_factory=default_now_ms,
)


# ============================================================================
# REST Endpoints
# ============================================================================

@router.post("/conversations", response_model=ChatConversationResponse)
async def create_conversation(
    conversation_data: ChatConversationCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new Chat Coach conversation.

    Creates a conversation with default lesson frame and empty session summary.
    """
    try:
        return create_chat_conversation(db, conversation_data)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "message": str(e)}
        )


@router.get("/conversations")
async def list_conversations(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    List all conversations for a user (ordered by updated_at DESC).
    """
    try:
        return list_chat_conversations(db, user_id)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "message": str(e)}
        )


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get all messages for a conversation (ordered by created_at ASC).

    Query parameters:
    - limit: max messages to return (default: 100)
    - offset: pagination offset (default: 0)
    """
    try:
        return list_chat_messages(db, conversation_id, limit=limit, offset=offset)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "message": str(e)}
        )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a conversation and all its messages (CASCADE).
    """
    try:
        return delete_chat_conversation(db, conversation_id)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "message": str(e)}
        )


# ============================================================================
# WebSocket Endpoint
# ============================================================================

@router.websocket("/ws/{conversation_id}")
async def chat_websocket(websocket: WebSocket, conversation_id: str):
    """
    WebSocket endpoint for real-time Chat Coach communication.

    Supports events:
    - draft_update → draft_feedback
    - request_autocomplete → draft_feedback (with ghost_suggestion)
    - user_message → assistant_stream_token* → assistant_done
    - ping → pong
    """
    from app.core.database import SessionLocal
    await run_chat_websocket_session(
        websocket=websocket,
        conversation_id=conversation_id,
        deps=build_chat_websocket_session_deps(
            session_factory=SessionLocal,
            build_runtime=build_chat_websocket_runtime,
            make_handlers=lambda: build_chat_websocket_handlers(_chat_handler_deps),
            route_event=route_websocket_event,
            send_error=_send_ws_error,
            initialize_tracking=_initialize_micro_eval_tracking,
            now_ms_factory=default_now_ms,
            logger=logger,
        ),
    )
