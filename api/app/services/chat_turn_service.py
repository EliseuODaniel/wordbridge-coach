"""Turn-orchestration helpers for Chat Coach user messages."""

from dataclasses import dataclass
import logging
from typing import Awaitable, Callable, List

from fastapi import WebSocket
from sqlalchemy.orm import Session

from app.models import ChatConversation, ChatMessage

logger = logging.getLogger(__name__)


@dataclass
class ChatUserMessageTurnHelpers:
    """Dependencies needed to process a full `user_message` turn."""

    freeze_feedback: Callable[[WebSocket, ChatConversation, str, object], Awaitable[dict]]
    persist_user_message: Callable[[Session, ChatConversation, str], ChatMessage]
    build_generation_inputs: Callable[[ChatConversation, Session], tuple[List[dict], str, dict]]
    stream_assistant_response: Callable[[WebSocket, str, object, List[dict], str, dict], Awaitable[str]]
    finalize_assistant_turn: Callable[[WebSocket, Session, ChatConversation, str], Awaitable[str]]
    build_teacher_analysis_context: Callable[[ChatConversation, Session], str]
    generate_teacher_analysis_with_fallback: Callable[[object, ChatConversation, str, str], Awaitable[tuple[dict, bool]]]
    persist_and_emit_teacher_analysis: Callable[
        [WebSocket, Session, ChatConversation, ChatMessage, dict, bool],
        Awaitable[None],
    ]


async def process_user_message_turn(
    websocket: WebSocket,
    data: dict,
    conversation: ChatConversation,
    db: Session,
    chat_provider,
    teacher_provider,
    helpers: ChatUserMessageTurnHelpers,
) -> None:
    """Run the full Chat Coach turn for a submitted user message."""
    content = data.get("content", "")
    conversation_id = str(conversation.id)

    logger.info(
        "chat_turn_started conversation_id=%s user_id=%s content_length=%s",
        conversation_id,
        str(getattr(conversation, "user_id", "unknown")),
        len(content),
    )

    user_message = helpers.persist_user_message(db, conversation, content)
    messages, system_prompt, generation_config = helpers.build_generation_inputs(conversation, db)

    full_response = await helpers.stream_assistant_response(
        websocket=websocket,
        conversation_id=conversation_id,
        chat_provider=chat_provider,
        messages=messages,
        system_prompt=system_prompt,
        generation_config=generation_config,
    )

    await helpers.finalize_assistant_turn(
        websocket=websocket,
        db=db,
        conversation=conversation,
        full_response=full_response,
    )

    teacher_analysis_context = helpers.build_teacher_analysis_context(conversation, db)
    teacher_analysis, used_fallback = await helpers.generate_teacher_analysis_with_fallback(
        teacher_provider=teacher_provider,
        conversation=conversation,
        teacher_context=teacher_analysis_context,
        content=content,
    )

    await helpers.persist_and_emit_teacher_analysis(
        websocket=websocket,
        db=db,
        conversation=conversation,
        user_message=user_message,
        teacher_analysis=teacher_analysis,
        used_fallback=used_fallback,
    )
    logger.info(
        "chat_turn_completed conversation_id=%s user_message_id=%s used_teacher_fallback=%s response_length=%s",
        conversation_id,
        str(user_message.id),
        used_fallback,
        len(full_response),
    )
