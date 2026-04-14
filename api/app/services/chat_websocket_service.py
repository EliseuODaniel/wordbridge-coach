"""Lifecycle helpers for the Chat Coach websocket endpoint."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable

from fastapi import WebSocket, WebSocketDisconnect

from app.core.time import utc_now


@dataclass
class ChatWebSocketSessionDeps:
    """Injected dependencies used to run a websocket chat session."""

    session_factory: Callable[[], object]
    build_runtime: Callable[[object, str], object | None]
    make_handlers: Callable[[], object]
    route_event: Callable[..., Awaitable[None]]
    send_error: Callable[[WebSocket, str, str], Awaitable[None]]
    initialize_tracking: Callable[[str], None]
    now_ms_factory: Callable[[], int]
    logger: object


def default_now_ms() -> int:
    """Return the current UTC timestamp in milliseconds."""
    return int(utc_now().timestamp() * 1000)


def build_chat_websocket_session_deps(
    session_factory: Callable[[], object],
    build_runtime: Callable[[object, str], object | None],
    make_handlers: Callable[[], object],
    route_event: Callable[..., Awaitable[None]],
    send_error: Callable[[WebSocket, str, str], Awaitable[None]],
    initialize_tracking: Callable[[str], None],
    now_ms_factory: Callable[[], int],
    logger: object,
) -> ChatWebSocketSessionDeps:
    """Build the dependency bundle used by the websocket session runner."""
    return ChatWebSocketSessionDeps(
        session_factory=session_factory,
        build_runtime=build_runtime,
        make_handlers=make_handlers,
        route_event=route_event,
        send_error=send_error,
        initialize_tracking=initialize_tracking,
        now_ms_factory=now_ms_factory,
        logger=logger,
    )


async def run_chat_websocket_session(
    websocket: WebSocket,
    conversation_id: str,
    deps: ChatWebSocketSessionDeps,
) -> None:
    """Run the full websocket lifecycle for a chat conversation."""
    await websocket.accept()
    db = deps.session_factory()

    try:
        try:
            runtime = deps.build_runtime(db, conversation_id)
        except Exception as error:
            deps.logger.error("[LLM_PROFILES] Failed to load preferences: %s", error)
            await deps.send_error(
                websocket,
                message=f"Failed to load LLM preferences: {str(error)}",
                code="PREFERENCES_ERROR",
            )
            await websocket.close()
            return

        if not runtime:
            await deps.send_error(
                websocket,
                message="Conversation not found",
                code="NOT_FOUND",
            )
            await websocket.close()
            return

        deps.initialize_tracking(str(runtime.conversation.id))
        handlers = deps.make_handlers()

        while True:
            data = await websocket.receive_json()
            event_type = data.get("type")
            deps.logger.info("[WS_RX] event_type=%s, data_keys=%s", event_type, list(data.keys()))

            await deps.route_event(
                websocket=websocket,
                data=data,
                runtime=runtime,
                now_ms=deps.now_ms_factory(),
                db=db,
                handlers=handlers,
                send_error=deps.send_error,
            )

    except WebSocketDisconnect:
        deps.logger.info("WebSocket disconnected: conversation_id=%s", conversation_id)
    except Exception as error:
        deps.logger.exception("WebSocket error: %s", error)
        try:
            await deps.send_error(
                websocket,
                message=str(error),
                code="INTERNAL_ERROR",
            )
        except Exception:
            pass
    finally:
        db.close()
