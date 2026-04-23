"""Persistence and delivery helpers for Chat Coach assistant/teacher events."""

import logging
from typing import Awaitable, Callable

from fastapi import WebSocket
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.models import ChatMessage
from app.schemas.chat import AssistantDoneOut, TeacherAnalysisOut, TeacherAnalysisPayload
from app.services.chat_profile_service import refresh_conversation_learning_state

logger = logging.getLogger(__name__)


def normalize_teacher_analysis(analysis: dict) -> dict:
    """Fill backward-compatible defaults before schema validation."""
    payload = dict(analysis or {})
    payload.setdefault("rewrite", None)
    payload.setdefault("corrections", [])
    payload.setdefault("teacher_summary", "Analysis unavailable.")
    payload.setdefault("strengths", [])
    payload.setdefault("focus_areas", [])
    payload.setdefault("next_practice", [])
    payload.setdefault("reflection_question", None)
    payload.setdefault("encouragement", None)
    return TeacherAnalysisPayload.model_validate(payload).model_dump()


def create_chat_message(conversation_id, role: str, content: str) -> ChatMessage:
    """Create a chat message model instance for a conversation turn."""
    return ChatMessage(
        conversation_id=conversation_id,
        role=role,
        content=content,
    )


def persist_user_message(db: Session, conversation, content: str) -> ChatMessage:
    """Persist a user chat turn and return the stored message model."""
    user_message = create_chat_message(conversation.id, "user", content)
    db.add(user_message)
    db.commit()
    return user_message


def persist_assistant_message(db: Session, conversation, content: str) -> ChatMessage:
    """Persist the assistant reply and refresh conversation update time."""
    assistant_message = create_chat_message(conversation.id, "assistant", content)
    db.add(assistant_message)
    conversation.updated_at = utc_now()
    db.commit()
    return assistant_message


def attach_teacher_analysis_metadata(user_message: ChatMessage, teacher_analysis: dict) -> None:
    """Store teacher analysis inside the user message metadata payload."""
    metadata = dict(user_message.metadata_json or {})
    metadata["teacher_analysis"] = normalize_teacher_analysis(teacher_analysis)
    user_message.metadata_json = metadata


def build_teacher_analysis_event_payload(
    conversation_id: str,
    user_message_id: str,
    analysis: dict,
    student_profile: dict | None = None,
    lesson_frame: dict | None = None,
    session_summary: str = "",
) -> dict:
    """Build the websocket payload for teacher analysis responses."""
    normalized_analysis = normalize_teacher_analysis(analysis)
    return TeacherAnalysisOut(
        type="teacher_analysis",
        conversation_id=conversation_id,
        user_message_id=user_message_id,
        analysis=normalized_analysis,
        student_profile=student_profile or {},
        lesson_frame=lesson_frame or {},
        session_summary=session_summary,
    ).model_dump()


def build_assistant_done_payload(conversation_id: str, full_content: str, lesson_frame: dict) -> dict:
    """Build the final assistant_done websocket payload."""
    return AssistantDoneOut(
        type="assistant_done",
        conversation_id=conversation_id,
        full_content=full_content,
        lesson_frame=lesson_frame,
        summary_update="Student sent a message.",
    ).model_dump()


async def send_teacher_analysis_event(
    websocket: WebSocket,
    conversation_id: str,
    user_message_id: str,
    analysis: dict,
    student_profile: dict | None = None,
    lesson_frame: dict | None = None,
    session_summary: str = "",
) -> None:
    """Send the teacher analysis payload to the websocket client."""
    event_payload = build_teacher_analysis_event_payload(
        conversation_id=conversation_id,
        user_message_id=user_message_id,
        analysis=analysis,
        student_profile=student_profile,
        lesson_frame=lesson_frame,
        session_summary=session_summary,
    )

    has_rewrite = bool(analysis and analysis.get("rewrite"))
    corrections_count = len(analysis.get("corrections", [])) if analysis else 0

    logger.info(
        f"[TEACHER_ANALYSIS] Sending WS event: type={event_payload['type']}, "
        f"conv={conversation_id[:8]}, payload_size={len(str(event_payload))}, "
        f"has_rewrite={has_rewrite}, corrections_count={corrections_count}"
    )
    await websocket.send_json(event_payload)
    logger.info("[TEACHER_ANALYSIS] WS event sent successfully")


async def finalize_assistant_turn(
    websocket: WebSocket,
    db: Session,
    conversation,
    full_response: str,
    sanitize_response: Callable[[str], str],
) -> str:
    """Sanitize, persist, and emit the final assistant response payload."""
    sanitized_response = sanitize_response(full_response)

    logger.info(
        f"[CHAT_SANITIZE] Original length: {len(full_response)}, "
        f"Sanitized length: {len(sanitized_response)}, "
        f"Removed: {len(full_response) - len(sanitized_response)} chars"
    )

    persist_assistant_message(db, conversation, sanitized_response)
    await websocket.send_json(
        build_assistant_done_payload(
            conversation_id=str(conversation.id),
            full_content=sanitized_response,
            lesson_frame=conversation.lesson_frame_json,
        )
    )
    return sanitized_response


async def persist_and_emit_teacher_analysis(
    websocket: WebSocket,
    db: Session,
    conversation,
    user_message: ChatMessage,
    teacher_analysis: dict,
    used_fallback: bool,
    send_event: Callable[[WebSocket, str, str, dict], Awaitable[None]] = send_teacher_analysis_event,
) -> None:
    """Persist teacher analysis when valid and emit the websocket event."""
    try:
        updated_student_profile = dict(conversation.student_profile_json or {})
        updated_lesson_frame = dict(conversation.lesson_frame_json or {})
        updated_session_summary = str(conversation.session_summary or "")
        if not used_fallback:
            attach_teacher_analysis_metadata(user_message, teacher_analysis)
            updated_student_profile, updated_lesson_frame, updated_session_summary = refresh_conversation_learning_state(
                db,
                conversation,
                teacher_analysis,
            )
            db.commit()

        await send_event(
            websocket=websocket,
            conversation_id=str(conversation.id),
            user_message_id=str(user_message.id),
            analysis=teacher_analysis,
            student_profile=updated_student_profile,
            lesson_frame=updated_lesson_frame,
            session_summary=updated_session_summary,
        )

        if used_fallback:
            logger.info(
                f"[TEACHER_ANALYSIS] Sent fallback with reason: "
                f"{teacher_analysis['debug_reason']}"
            )
    except Exception as error:
        logger.error(f"[TEACHER_ANALYSIS] Failed to send fallback: {error}")
