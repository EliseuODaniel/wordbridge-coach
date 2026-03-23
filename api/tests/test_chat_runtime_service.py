import asyncio
from types import SimpleNamespace

from app.services import chat_runtime_service
from app.services.chat_runtime_service import (
    ChatWebSocketHandlers,
    ChatWebSocketRuntime,
    build_chat_websocket_runtime,
    build_ws_error_payload,
    route_websocket_event,
)


class FakeWebSocket:
    def __init__(self):
        self.sent = []

    async def send_json(self, payload):
        self.sent.append(payload)


def test_build_ws_error_payload_uses_expected_schema():
    payload = build_ws_error_payload("Conversation not found", "NOT_FOUND")

    assert payload == {
        "type": "error",
        "message": "Conversation not found",
        "code": "NOT_FOUND",
    }


def test_build_chat_websocket_runtime_returns_none_when_conversation_is_missing(monkeypatch):
    monkeypatch.setattr(
        chat_runtime_service,
        "get_websocket_conversation",
        lambda db, conversation_id: None,
    )

    runtime = build_chat_websocket_runtime(db=object(), conversation_id="missing")

    assert runtime is None


def test_build_chat_websocket_runtime_loads_conversation_and_providers(monkeypatch):
    conversation = SimpleNamespace(id="conv-1", user_id="user-1")
    chat_provider = object()
    teacher_provider = object()

    monkeypatch.setattr(
        chat_runtime_service,
        "get_websocket_conversation",
        lambda db, conversation_id: conversation,
    )
    monkeypatch.setattr(
        chat_runtime_service,
        "load_chat_providers_for_conversation",
        lambda db, loaded_conversation: (chat_provider, teacher_provider),
    )

    runtime = build_chat_websocket_runtime(db=object(), conversation_id="conv-1")

    assert runtime == ChatWebSocketRuntime(
        conversation=conversation,
        chat_provider=chat_provider,
        teacher_provider=teacher_provider,
    )


def test_route_websocket_event_dispatches_user_message():
    websocket = FakeWebSocket()
    runtime = ChatWebSocketRuntime(
        conversation=SimpleNamespace(id="conv-1"),
        chat_provider=object(),
        teacher_provider=object(),
    )
    calls = []

    async def draft_update(*args):
        calls.append(("draft_update", args))

    async def request_autocomplete(*args):
        calls.append(("request_autocomplete", args))

    async def user_message(*args):
        calls.append(("user_message", args))

    handlers = ChatWebSocketHandlers(
        draft_update=draft_update,
        request_autocomplete=request_autocomplete,
        user_message=user_message,
    )

    async def send_error(*args, **kwargs):
        raise AssertionError("send_error should not be called for user_message")

    async def run():
        await route_websocket_event(
            websocket=websocket,
            data={"type": "user_message", "content": "hello"},
            runtime=runtime,
            now_ms=123,
            db=object(),
            handlers=handlers,
            send_error=send_error,
        )

    asyncio.run(run())

    assert len(calls) == 1
    assert calls[0][0] == "user_message"
    assert calls[0][1][1]["content"] == "hello"
    assert calls[0][1][2] is runtime.conversation


def test_route_websocket_event_returns_pong():
    websocket = FakeWebSocket()
    runtime = ChatWebSocketRuntime(
        conversation=SimpleNamespace(id="conv-1"),
        chat_provider=object(),
        teacher_provider=object(),
    )

    async def noop(*args):
        return None

    handlers = ChatWebSocketHandlers(
        draft_update=noop,
        request_autocomplete=noop,
        user_message=noop,
    )

    async def send_error(*args, **kwargs):
        raise AssertionError("send_error should not be called for ping")

    async def run():
        await route_websocket_event(
            websocket=websocket,
            data={"type": "ping", "ts": 987},
            runtime=runtime,
            now_ms=123,
            db=object(),
            handlers=handlers,
            send_error=send_error,
        )

    asyncio.run(run())

    assert websocket.sent == [{"type": "pong", "ts": 987}]


def test_route_websocket_event_reports_unknown_event():
    websocket = FakeWebSocket()
    runtime = ChatWebSocketRuntime(
        conversation=SimpleNamespace(id="conv-1"),
        chat_provider=object(),
        teacher_provider=object(),
    )
    captured = {}

    async def noop(*args):
        return None

    handlers = ChatWebSocketHandlers(
        draft_update=noop,
        request_autocomplete=noop,
        user_message=noop,
    )

    async def send_error(_websocket, message, code):
        captured["message"] = message
        captured["code"] = code

    async def run():
        await route_websocket_event(
            websocket=websocket,
            data={"type": "mystery"},
            runtime=runtime,
            now_ms=123,
            db=object(),
            handlers=handlers,
            send_error=send_error,
        )

    asyncio.run(run())

    assert captured == {
        "message": "Unknown event type: mystery",
        "code": "UNKNOWN_EVENT",
    }
