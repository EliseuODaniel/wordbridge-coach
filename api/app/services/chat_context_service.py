"""Context-building helpers for Chat Coach generation and analysis."""

import logging
from typing import Callable, List, Optional

from sqlalchemy.orm import Session

from app.models import ChatMessage

logger = logging.getLogger(__name__)


def build_context_messages(
    conversation_id: str,
    db: Session,
    limit: int = 10,
    exclude_system: bool = False,
) -> List[dict]:
    """Build chat context messages with recent non-system turns in chronological order."""
    system_msg = None
    if not exclude_system:
        system_msg = db.query(ChatMessage).filter(
            ChatMessage.conversation_id == conversation_id,
            ChatMessage.role == "system",
        ).first()

    last_non_system = db.query(ChatMessage).filter(
        ChatMessage.conversation_id == conversation_id,
        ChatMessage.role != "system",
    ).order_by(ChatMessage.created_at.desc()).limit(limit).all()

    last_non_system.reverse()
    logger.info(f"[CONTEXT_BUILDER] chat_context: {len(last_non_system)} messages (user+assistant)")

    messages = []
    if system_msg:
        messages.append({"role": system_msg.role, "content": system_msg.content})

    messages.extend(
        {"role": message.role, "content": message.content}
        for message in last_non_system
    )
    return messages


def build_teacher_context(
    conversation_id: str,
    db: Session,
    limit: int = 10,
) -> List[dict]:
    """Build teacher-only context with recent user messages in chronological order."""
    last_user_messages = db.query(ChatMessage).filter(
        ChatMessage.conversation_id == conversation_id,
        ChatMessage.role == "user",
    ).order_by(ChatMessage.created_at.desc()).limit(limit).all()

    last_user_messages.reverse()
    logger.info(f"[CONTEXT_BUILDER] teacher_context: {len(last_user_messages)} user messages (assistant excluded)")

    return [
        {"role": message.role, "content": message.content}
        for message in last_user_messages
    ]


def build_chat_generation_inputs(
    conversation,
    db: Session,
    build_context: Callable[[str, Session, int, bool], List[dict]],
    build_system_prompt: Callable[[dict], str],
    build_generation_config: Callable[[], dict],
) -> tuple[List[dict], str, dict]:
    """Build generation inputs for assistant streaming."""
    messages = build_context(str(conversation.id), db, limit=10, exclude_system=True)
    system_prompt = build_system_prompt(conversation.lesson_frame_json)
    generation_config = build_generation_config()
    return messages, system_prompt, generation_config


def build_teacher_analysis_context(
    conversation,
    db: Session,
    build_teacher_context_fn: Callable[[str, Session, int], List[dict]],
    limit: int = 10,
) -> str:
    """Build teacher-analysis context, falling back to session summary when needed."""
    teacher_messages = build_teacher_context_fn(str(conversation.id), db, limit=limit)
    if teacher_messages:
        return "\n".join(message["content"] for message in teacher_messages if message.get("content"))

    return conversation.session_summary
