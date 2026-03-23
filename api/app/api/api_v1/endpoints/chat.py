"""Chat Coach endpoints for real-time conversational training"""

import os
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from pydantic import BaseModel
import uuid

logger = logging.getLogger(__name__)

from app.core.database import get_db
from app.core.time import utc_now
from app.models import User, ChatConversation, ChatMessage
from app.schemas.chat import (
    ChatConversationCreate,
    ChatConversationResponse,
    ChatMessageResponse,
    DraftFeedbackOut,
    AssistantStreamTokenOut,
    AssistantDoneOut,
    TeacherAnalysisOut,
)
from app.llm.factory import get_llm_provider_from_env, get_provider_name
from app.services.chat_runtime_service import (
    ChatWebSocketHandlers,
    build_chat_websocket_runtime,
    build_ws_error_payload as _build_ws_error_payload,
    route_websocket_event,
)
from app.services.chat_draft_service import (
    ChatDraftFeedbackHelpers,
    ChatDraftFeedbackState,
    process_draft_update,
    process_request_autocomplete,
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
from app.services.chat_turn_service import (
    ChatUserMessageTurnHelpers,
    process_user_message_turn,
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

# In-memory tracking for throttling micro_eval (conversation_id -> last_eval_ts)
_micro_eval_timestamps = {}

# Cache for last feedback (conversation_id -> last_feedback_dict)
# Used to prevent "dead" panel when throttled
_feedback_cache = {}

# Cache for last processed draft text (conversation_id -> last_draft_text)
# Used to bypass throttle when text changes
_last_draft_texts = {}


async def _send_ws_error(websocket: WebSocket, message: str, code: str) -> None:
    """Send a standardized websocket error payload."""
    await websocket.send_json(_build_ws_error_payload(message=message, code=code))


def _get_user_or_404(db: Session, user_id: str) -> User:
    """Load a user or raise a standardized 404 error."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "User not found", "message": f"User '{user_id}' not found"}
        )
    return user


def _get_conversation_or_404(db: Session, conversation_id: str) -> ChatConversation:
    """Load a conversation or raise a standardized 404 error."""
    conversation = db.query(ChatConversation).filter(
        ChatConversation.id == conversation_id
    ).first()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Conversation not found", "message": f"Conversation '{conversation_id}' not found"}
        )
    return conversation


def _serialize_conversation(conversation: ChatConversation) -> ChatConversationResponse:
    """Convert a ChatConversation model into the REST response schema."""
    return ChatConversationResponse(
        id=str(conversation.id),
        user_id=str(conversation.user_id),
        title=conversation.title,
        student_profile_json=conversation.student_profile_json,
        lesson_frame_json=conversation.lesson_frame_json,
        session_summary=conversation.session_summary,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at
    )


def _serialize_message(message: ChatMessage) -> ChatMessageResponse:
    """Convert a ChatMessage model into the REST response schema."""
    return ChatMessageResponse(
        id=str(message.id),
        conversation_id=str(message.conversation_id),
        role=message.role,
        content=message.content,
        metadata_json=message.metadata_json,
        created_at=message.created_at
    )


def _serialize_conversation_list_item(db: Session, conversation: ChatConversation) -> dict:
    """Build the list payload for a conversation including message count."""
    message_count = db.query(ChatMessage).filter(
        ChatMessage.conversation_id == conversation.id
    ).count()

    return {
        "id": str(conversation.id),
        "user_id": str(conversation.user_id),
        "title": conversation.title,
        "student_profile_json": conversation.student_profile_json,
        "lesson_frame_json": conversation.lesson_frame_json,
        "session_summary": conversation.session_summary,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "message_count": message_count
    }


def _initialize_micro_eval_tracking(conversation_id: str) -> None:
    """Ensure throttle state exists for the websocket conversation."""
    if conversation_id not in _micro_eval_timestamps:
        _micro_eval_timestamps[conversation_id] = 0


def get_default_lesson_frame() -> dict:
    """Get default lesson frame for new conversations"""
    return {
        "cefr_target": "A2",
        "learning_goal": "conversation_start",
        "expected_intent": "introduction",
        "topic": "getting_started",
        "rubric": {
            "grammar": [],
            "vocab": [],
            "style": ["friendly"]
        },
        "scoring_hints": {
            "avoid": [],
            "encourage": ["complete_sentences", "clear_communication"]
        }
    }


def get_default_student_profile() -> dict:
    """Get default student profile"""
    return {
        "cefr_level": "A2",
        "common_errors": [],
        "strengths": [],
        "weaknesses": []
    }


async def _evaluate_draft_feedback(
    conversation: ChatConversation,
    draft_text: str,
    now_ms: int,
    ghost_suggestion: Optional[str] = None,
    include_grammar_check: bool = False,
) -> dict:
    """Adapt endpoint config to the shared feedback-evaluation service."""
    return await evaluate_draft_feedback(
        conversation=conversation,
        draft_text=draft_text,
        now_ms=now_ms,
        llm_provider=llm_provider,
        grammar_provider=CHAT_DRAFT_GRAMMAR_PROVIDER,
        grammar_url=CHAT_LANGUAGETOOL_URL,
        ghost_suggestion=ghost_suggestion,
        include_grammar_check=include_grammar_check,
    )


def _cache_draft_feedback(conversation_id: str, draft_text: str, feedback: dict) -> None:
    """Persist the last feedback and draft text for throttle reuse."""
    _feedback_cache[conversation_id] = feedback
    _last_draft_texts[conversation_id] = draft_text


def _build_throttled_feedback(last_feedback: dict, draft_text: str, now_ms: int) -> dict:
    """Return a shallow copy of cached feedback updated for the current draft."""
    updated_feedback = dict(last_feedback)
    updated_feedback["server_ts_ms"] = now_ms
    updated_feedback["draft"] = draft_text
    return updated_feedback


def _build_chat_system_prompt(lesson_frame: dict) -> str:
    """Build the chat tutor system prompt from the current lesson frame."""
    return f"""You are an English tutor helping a {lesson_frame.get('cefr_target', 'A2')} student.
Topic: {lesson_frame.get('topic', 'conversation')}
Goal: {lesson_frame.get('learning_goal', 'practice conversation')}

Keep it natural:
- Reply briefly (1-3 sentences) as if chatting with a friend
- Always ask a follow-up question
- Never correct grammar or explain rules
- If they write in Portuguese/Spanish, encourage them to use English
- No examples, quotes, or meta-commentary
"""


def _get_chat_stop_sequences() -> List[str]:
    """Return sanitized stop sequences for chat generation."""
    stop_sequences = [
        '\n\n"',
        '\nUser:', '\nUSER:', '\nStudent:', '\nSTUDENT:',
        '">', '<|',
        '\n\nCRITICAL INSTRUCTIONS',
        '\nNote:', '\n(Note:', '\nTeacher:', '\nAnalysis:',
        '\nExplanation:', '\nCorrection:', '\nMeta:', '\nSystem:',
    ]
    return [s for s in stop_sequences if isinstance(s, str) and s.strip()]


def _build_chat_generation_config() -> dict:
    """Return the default generation config for chat replies."""
    return {
        "temperature": 0.5,
        "max_tokens": 300,
        "top_p": 0.9,
        "stop": _get_chat_stop_sequences(),
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0
    }


def _build_teacher_analysis_fallback(error: Exception) -> dict:
    """Build the fallback payload used when teacher analysis generation fails."""
    error_reason = str(error)[:100]
    return {
        "teacher_summary": f"Teacher analysis failed: {error_reason}",
        "rewrite": None,
        "corrections": [],
        "next_practice": [],
        "debug_reason": error_reason
    }


def _build_chat_generation_inputs(conversation: ChatConversation, db: Session) -> tuple[List[dict], str, dict]:
    """Adapt endpoint-local dependencies to the shared context service."""
    return _build_chat_generation_inputs_service(
        conversation=conversation,
        db=db,
        build_context=_build_context_messages,
        build_system_prompt=_build_chat_system_prompt,
        build_generation_config=_build_chat_generation_config,
    )


def _build_teacher_analysis_context(conversation: ChatConversation, db: Session, limit: int = 10) -> str:
    """Adapt endpoint-local dependencies to the shared teacher-context service."""
    return _build_teacher_analysis_context_service(
        conversation=conversation,
        db=db,
        build_teacher_context_fn=_build_teacher_context,
        limit=limit,
    )


async def _freeze_user_message_feedback(
    websocket: WebSocket,
    conversation: ChatConversation,
    content: str,
    chat_provider,
) -> dict:
    """Adapt endpoint config to the shared frozen-feedback service."""
    return await freeze_user_message_feedback(
        websocket=websocket,
        conversation=conversation,
        content=content,
        chat_provider=chat_provider,
    )


async def _stream_assistant_response(
    websocket: WebSocket,
    conversation_id: str,
    chat_provider,
    messages: List[dict],
    system_prompt: str,
    generation_config: dict,
) -> str:
    """Stream assistant tokens to the client and return the aggregated response."""
    full_response = ""

    logger.info(
        f"[CHAT_LLM] Starting stream with profile chat_provider.model={chat_provider.model}"
    )
    async for token in chat_provider.chat_stream(messages, system_prompt, generation_config):
        full_response += token
        await websocket.send_json(AssistantStreamTokenOut(
            type="assistant_stream_token",
            conversation_id=conversation_id,
            token=token
        ).model_dump())

    return full_response


async def _generate_teacher_analysis_with_fallback(
    teacher_provider,
    conversation: ChatConversation,
    teacher_context: str,
    content: str,
) -> tuple[dict, bool]:
    """Return teacher analysis and whether it came from the fallback path."""
    conv_id_str = str(conversation.id)

    try:
        logger.info(
            f"[TEACHER_ANALYSIS] Starting generation for conv={conv_id_str[:8]} "
            f"with profile teacher_provider.model={teacher_provider.model}"
        )

        teacher_analysis = await teacher_provider.generate_teacher_analysis(
            user_message=content,
            context=teacher_context,
            lesson_frame=conversation.lesson_frame_json
        )

        logger.info(
            "[TEACHER_ANALYSIS] Generated successfully, "
            f"keys={list(teacher_analysis.keys()) if teacher_analysis else 'None'}"
        )
        return teacher_analysis, False
    except Exception as error:
        logger.error(f"[TEACHER_ANALYSIS] Failed to generate: {error}")
        import traceback
        traceback.print_exc()
        return _build_teacher_analysis_fallback(error), True


async def _send_teacher_analysis_event(
    websocket: WebSocket,
    conversation_id: str,
    user_message_id: str,
    analysis: dict,
) -> None:
    """Adapt endpoint-local callers to the shared teacher-analysis event service."""
    await _send_teacher_analysis_event_service(
        websocket=websocket,
        conversation_id=conversation_id,
        user_message_id=user_message_id,
        analysis=analysis,
    )


async def _finalize_assistant_turn(
    websocket: WebSocket,
    db: Session,
    conversation: ChatConversation,
    full_response: str,
) -> str:
    """Adapt endpoint-local callers to the shared assistant-finalization service."""
    return await _finalize_assistant_turn_service(
        websocket=websocket,
        db=db,
        conversation=conversation,
        full_response=full_response,
        sanitize_response=_sanitize_assistant_response,
    )


async def _persist_and_emit_teacher_analysis(
    websocket: WebSocket,
    db: Session,
    conversation: ChatConversation,
    user_message: ChatMessage,
    teacher_analysis: dict,
    used_fallback: bool,
) -> None:
    """Adapt endpoint-local callers to the shared teacher-analysis delivery service."""
    await _persist_and_emit_teacher_analysis_service(
        websocket=websocket,
        db=db,
        conversation=conversation,
        user_message=user_message,
        teacher_analysis=teacher_analysis,
        used_fallback=used_fallback,
        send_event=_send_teacher_analysis_event,
    )


def _sanitize_assistant_response(response: str) -> str:
    """
    Remove meta-commentary and extra user simulation from LLM response.

    PASSO 2: Sanitizer melhorado (bloqueio em 3 camadas)
    1. Remove parenthetical meta-commentary: "(Note:", "(Teacher:", etc.
    2. Remove lines starting with meta labels
    3. Truncate at "CRITICAL INSTRUCTIONS" (remove do match até o fim)
    4. Remove quoted paragraph at the end (user simulation)
    5. Truncate at role labels (User:, Student:, etc.)

    Args:
        response: Raw LLM response

    Returns:
        Sanitized response with meta-commentary and user simulation removed
    """
    import re

    # PASSO 2: Bloqueio em 3 camadas

    # Camada 1: Remove parenthetical meta-commentary at any position
    response = re.sub(r'\(Note:[^)]*\)', '', response, flags=re.IGNORECASE)
    response = re.sub(r'\(Teacher:[^)]*\)', '', response, flags=re.IGNORECASE)
    response = re.sub(r'\(Analysis:[^)]*\)', '', response, flags=re.IGNORECASE)
    response = re.sub(r'\(Correction:[^)]*\)', '', response, flags=re.IGNORECASE)

    # Camada 2: Remove non-parenthetical meta-commentary lines
    lines = response.split('\n')
    filtered_lines = []
    for line in lines:
        stripped = line.strip()
        # Skip lines that are pure meta-commentary
        if re.match(r'^(Note|Teacher|Analysis|Explanation|Correction|Meta|System):', stripped, re.IGNORECASE):
            continue
        filtered_lines.append(line)

    response = '\n'.join(filtered_lines)

    # Camada 3: PASSO 2 - Truncate se "CRITICAL INSTRUCTIONS" aparecer
    # Remove tudo a partir da linha contendo "CRITICAL INSTRUCTIONS"
    lines = response.split('\n')
    truncated_lines = []
    for line in lines:
        if 'CRITICAL INSTRUCTIONS' in line:
            break  # Truncate aqui
        truncated_lines.append(line)

    response = '\n'.join(truncated_lines)

    # Remove trailing quoted block(s) after a blank line.
    # This catches single-line and multiline user simulations at the end.
    response = re.sub(r'\n\s*\n"[\s\S]*"\s*$', '', response).strip()

    lines = response.split('\n')

    # Truncate at role labels (LLM started a second turn)
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(('User:', 'USER:', 'Student:', 'STUDENT:')):
            lines = lines[:i]
            break

    return '\n'.join(lines).strip()


def _build_context_messages(conversation_id: str, db: Session, limit: int = 10,
                          exclude_system: bool = False) -> List[dict]:
    """Wrapper kept for compatibility with existing tests and local callers."""
    return _build_context_messages_service(
        conversation_id=conversation_id,
        db=db,
        limit=limit,
        exclude_system=exclude_system,
    )


def _build_teacher_context(conversation_id: str, db: Session, limit: int = 10) -> List[dict]:
    """Wrapper kept for compatibility with existing tests and local callers."""
    return _build_teacher_context_service(
        conversation_id=conversation_id,
        db=db,
        limit=limit,
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
        _get_user_or_404(db, conversation_data.user_id)

        # Create conversation
        conversation = ChatConversation(
            user_id=conversation_data.user_id,
            title=conversation_data.title,
            student_profile_json=get_default_student_profile(),
            lesson_frame_json=get_default_lesson_frame(),
            session_summary=""
        )

        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        # Create system message (teacher prompt)
        system_message = ChatMessage(
            conversation_id=conversation.id,
            role="system",
            content=f"You are an English teacher helping a {conversation.lesson_frame_json.get('cefr_target', 'A2')} level student practice conversation."
        )
        db.add(system_message)
        db.commit()

        return _serialize_conversation(conversation)

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
        _get_user_or_404(db, user_id)

        # Get conversations
        conversations = db.query(ChatConversation).filter(
            ChatConversation.user_id == user_id
        ).order_by(ChatConversation.updated_at.desc()).all()

        return [_serialize_conversation_list_item(db, conv) for conv in conversations]

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
        _get_conversation_or_404(db, conversation_id)

        # Get messages
        messages = db.query(ChatMessage).filter(
            ChatMessage.conversation_id == conversation_id
        ).order_by(ChatMessage.created_at.asc()).offset(offset).limit(limit).all()

        return [_serialize_message(msg) for msg in messages]

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
        conversation = _get_conversation_or_404(db, conversation_id)

        # Delete conversation (messages will be CASCADE deleted)
        db.delete(conversation)
        db.commit()

        return {"message": "Conversation deleted successfully"}

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
    await websocket.accept()

    # Create database session for this WebSocket connection
    from app.core.database import SessionLocal
    db = SessionLocal()

    try:
        try:
            runtime = build_chat_websocket_runtime(db, conversation_id)
        except Exception as e:
            logger.error(f"[LLM_PROFILES] Failed to load preferences: {e}")
            await _send_ws_error(
                websocket,
                message=f"Failed to load LLM preferences: {str(e)}",
                code="PREFERENCES_ERROR"
            )
            await websocket.close()
            return

        if not runtime:
            await _send_ws_error(
                websocket,
                message="Conversation not found",
                code="NOT_FOUND"
            )
            await websocket.close()
            return

        _initialize_micro_eval_tracking(str(runtime.conversation.id))
        handlers = ChatWebSocketHandlers(
            draft_update=handle_draft_update,
            request_autocomplete=handle_request_autocomplete,
            user_message=handle_user_message,
        )

        # Main WebSocket loop
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            event_type = data.get("type")

            logger.info(f"[WS_RX] event_type={event_type}, data_keys={list(data.keys())}")

            now_ms = int(utc_now().timestamp() * 1000)

            await route_websocket_event(
                websocket=websocket,
                data=data,
                runtime=runtime,
                now_ms=now_ms,
                db=db,
                handlers=handlers,
                send_error=_send_ws_error,
            )

    except WebSocketDisconnect:
        print(f"WebSocket disconnected: conversation_id={conversation_id}")
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        import traceback
        traceback.print_exc()
        try:
            await _send_ws_error(
                websocket,
                message=str(e),
                code="INTERNAL_ERROR"
            )
        except:
            pass
    finally:
        db.close()


async def handle_draft_update(websocket: WebSocket, data: dict, conversation: ChatConversation, now_ms: int, db: Session):
    """Handle draft_update event → return draft_feedback"""
    draft_text = data.get("draft_text", "")
    conversation_id = str(conversation.id)

    logger.info(f"[DRAFT_UPDATE_START] conv={conversation_id[:8]}, draft_text='{draft_text}'")

    logger.info(f"[DRAFT_UPDATE] text='{draft_text}', len={len(draft_text)}, conv={conversation_id[:8]}")

    await process_draft_update(
        websocket=websocket,
        data=data,
        conversation=conversation,
        now_ms=now_ms,
        db=db,
        state=ChatDraftFeedbackState(
            micro_eval_timestamps=_micro_eval_timestamps,
            feedback_cache=_feedback_cache,
            last_draft_texts=_last_draft_texts,
            min_interval_ms=CHAT_MICRO_EVAL_MIN_INTERVAL_MS,
        ),
        helpers=ChatDraftFeedbackHelpers(
            evaluate_draft_feedback=_evaluate_draft_feedback,
            cache_draft_feedback=_cache_draft_feedback,
            build_throttled_feedback=_build_throttled_feedback,
            autocomplete=llm_provider.autocomplete,
        ),
    )


async def handle_request_autocomplete(websocket: WebSocket, data: dict, conversation: ChatConversation, db: Session):
    """
    Handle request_autocomplete event → return draft_feedback with ghost_suggestion

    CRITICAL FIX: Now runs micro_eval FIRST to get real issues, then adds ghost suggestion.
    This prevents the panel from clearing issues when autocomplete triggers.
    """
    request_data = dict(data)
    request_data["now_ms"] = int(utc_now().timestamp() * 1000)

    await process_request_autocomplete(
        websocket=websocket,
        data=request_data,
        conversation=conversation,
        db=db,
        helpers=ChatDraftFeedbackHelpers(
            evaluate_draft_feedback=_evaluate_draft_feedback,
            cache_draft_feedback=_cache_draft_feedback,
            build_throttled_feedback=_build_throttled_feedback,
            autocomplete=llm_provider.autocomplete,
        ),
    )


async def handle_user_message(websocket: WebSocket, data: dict, conversation: ChatConversation, db: Session,
                            chat_provider, teacher_provider):
    """Handle user_message event → stream assistant response → assistant_done"""
    await process_user_message_turn(
        websocket=websocket,
        data=data,
        conversation=conversation,
        db=db,
        chat_provider=chat_provider,
        teacher_provider=teacher_provider,
        helpers=ChatUserMessageTurnHelpers(
            freeze_feedback=_freeze_user_message_feedback,
            persist_user_message=_persist_user_message,
            build_generation_inputs=_build_chat_generation_inputs,
            stream_assistant_response=_stream_assistant_response,
            finalize_assistant_turn=_finalize_assistant_turn,
            build_teacher_analysis_context=_build_teacher_analysis_context,
            generate_teacher_analysis_with_fallback=_generate_teacher_analysis_with_fallback,
            persist_and_emit_teacher_analysis=_persist_and_emit_teacher_analysis,
        ),
    )
