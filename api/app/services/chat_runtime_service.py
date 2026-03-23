"""Runtime helpers for Chat Coach websocket sessions."""

import logging
from dataclasses import dataclass
from typing import Awaitable, Callable, Optional

from fastapi import WebSocket
from sqlalchemy.orm import Session

from app.llm.factory import get_llm_provider_for_profile
from app.models import ChatConversation
from app.schemas.chat import ErrorOut, Pong
from app.services.user_llm_preferences_service import get_user_model_profiles

logger = logging.getLogger(__name__)


@dataclass
class ChatWebSocketRuntime:
    """Resolved runtime dependencies for a chat websocket session."""

    conversation: ChatConversation
    chat_provider: object
    teacher_provider: object


@dataclass
class ChatWebSocketHandlers:
    """Collection of event handlers used by the websocket router."""

    draft_update: Callable[[WebSocket, dict, ChatConversation, int, Session], Awaitable[None]]
    request_autocomplete: Callable[[WebSocket, dict, ChatConversation, Session], Awaitable[None]]
    user_message: Callable[[WebSocket, dict, ChatConversation, Session, object, object], Awaitable[None]]


def build_ws_error_payload(message: str, code: str) -> dict:
    """Build a standardized websocket error payload."""
    return ErrorOut(type="error", message=message, code=code).model_dump()


def get_websocket_conversation(db: Session, conversation_id: str) -> Optional[ChatConversation]:
    """Load the chat conversation for a websocket connection."""
    with db.begin():
        return db.query(ChatConversation).filter(
            ChatConversation.id == conversation_id
        ).first()


def load_chat_providers_for_conversation(db: Session, conversation: ChatConversation) -> tuple[object, object]:
    """Load the chat and teacher LLM providers for a conversation."""
    profiles = get_user_model_profiles(db, conversation.user_id)
    chat_profile_id = profiles["chat_model_profile"]
    teacher_profile_id = profiles["teacher_model_profile"]

    logger.info(
        f"[LLM_PROFILES] conv={str(conversation.id)[:8]}, user={conversation.user_id} "
        f"chat={chat_profile_id}, teacher={teacher_profile_id}"
    )

    chat_provider = get_llm_provider_for_profile(chat_profile_id)
    teacher_provider = get_llm_provider_for_profile(teacher_profile_id)
    return chat_provider, teacher_provider


def build_chat_websocket_runtime(db: Session, conversation_id: str) -> Optional[ChatWebSocketRuntime]:
    """Resolve conversation and providers required to run a websocket session."""
    conversation = get_websocket_conversation(db, conversation_id)
    if not conversation:
        return None

    chat_provider, teacher_provider = load_chat_providers_for_conversation(db, conversation)
    return ChatWebSocketRuntime(
        conversation=conversation,
        chat_provider=chat_provider,
        teacher_provider=teacher_provider,
    )


async def route_websocket_event(
    websocket: WebSocket,
    data: dict,
    runtime: ChatWebSocketRuntime,
    now_ms: int,
    db: Session,
    handlers: ChatWebSocketHandlers,
    send_error: Callable[[WebSocket, str, str], Awaitable[None]],
) -> None:
    """Dispatch websocket events to the correct chat handler."""
    event_type = data.get("type")

    if event_type == "draft_update":
        await handlers.draft_update(websocket, data, runtime.conversation, now_ms, db)
    elif event_type == "request_autocomplete":
        await handlers.request_autocomplete(websocket, data, runtime.conversation, db)
    elif event_type == "user_message":
        await handlers.user_message(
            websocket,
            data,
            runtime.conversation,
            db,
            runtime.chat_provider,
            runtime.teacher_provider,
        )
    elif event_type == "ping":
        await websocket.send_json(Pong(type="pong", ts=data.get("ts", now_ms)).model_dump())
    else:
        await send_error(
            websocket,
            message=f"Unknown event type: {event_type}",
            code="UNKNOWN_EVENT",
        )
