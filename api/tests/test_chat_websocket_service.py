import asyncio
from types import SimpleNamespace

from fastapi import WebSocketDisconnect

from app.services.chat_websocket_service import (
    ChatWebSocketSessionDeps,
    build_chat_websocket_session_deps,
    run_chat_websocket_session,
)


class FakeLogger:
    def __init__(self):
        self.records = []

    def info(self, message, *args):
        self.records.append(("info", message % args if args else message))

    def error(self, message, *args):
        self.records.append(("error", message % args if args else message))

    def exception(self, message, *args):
        self.records.append(("exception", message % args if args else message))


class FakeDb:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


class FakeWebSocket:
    def __init__(self, received=None):
        self.received = list(received or [])
        self.accepted = False
        self.closed = False

    async def accept(self):
        self.accepted = True

    async def close(self):
        self.closed = True

    async def receive_json(self):
        if not self.received:
            raise WebSocketDisconnect()
        next_item = self.received.pop(0)
        if isinstance(next_item, Exception):
            raise next_item
        return next_item


def test_build_chat_websocket_session_deps_preserves_injected_callables():
    session_factory = lambda: "db"
    build_runtime = lambda db, conversation_id: "runtime"
    make_handlers = lambda: "handlers"

    async def route_event(**kwargs):
        return None

    async def send_error(_websocket, message, code):
        return None

    initialize_tracking = lambda conversation_id: None
    now_ms_factory = lambda: 123
    logger = FakeLogger()

    deps = build_chat_websocket_session_deps(
        session_factory=session_factory,
        build_runtime=build_runtime,
        make_handlers=make_handlers,
        route_event=route_event,
        send_error=send_error,
        initialize_tracking=initialize_tracking,
        now_ms_factory=now_ms_factory,
        logger=logger,
    )

    assert isinstance(deps, ChatWebSocketSessionDeps)
    assert deps.session_factory is session_factory
    assert deps.build_runtime is build_runtime
    assert deps.make_handlers is make_handlers
    assert deps.route_event is route_event
    assert deps.send_error is send_error
    assert deps.initialize_tracking is initialize_tracking
    assert deps.now_ms_factory is now_ms_factory
    assert deps.logger is logger


def test_run_chat_websocket_session_closes_when_runtime_is_missing():
    logger = FakeLogger()
    db = FakeDb()
    websocket = FakeWebSocket()
    sent_errors = []

    async def send_error(_websocket, message, code):
        sent_errors.append((message, code))

    deps = ChatWebSocketSessionDeps(
        session_factory=lambda: db,
        build_runtime=lambda local_db, conversation_id: None,
        make_handlers=lambda: object(),
        route_event=lambda **kwargs: None,
        send_error=send_error,
        initialize_tracking=lambda conversation_id: None,
        now_ms_factory=lambda: 123,
        logger=logger,
    )

    asyncio.run(run_chat_websocket_session(websocket, "conv-1", deps))

    assert websocket.accepted is True
    assert websocket.closed is True
    assert sent_errors == [("Conversation not found", "NOT_FOUND")]
    assert db.closed is True


def test_run_chat_websocket_session_dispatches_events_until_disconnect():
    logger = FakeLogger()
    db = FakeDb()
    websocket = FakeWebSocket(received=[{"type": "ping", "ts": 1}])
    runtime = SimpleNamespace(conversation=SimpleNamespace(id="conv-1"))
    calls = []

    async def route_event(**kwargs):
        calls.append(kwargs)
        raise WebSocketDisconnect()

    async def send_error(_websocket, message, code):
        raise AssertionError(f"send_error should not be called: {message} {code}")

    deps = ChatWebSocketSessionDeps(
        session_factory=lambda: db,
        build_runtime=lambda local_db, conversation_id: runtime,
        make_handlers=lambda: "handlers",
        route_event=route_event,
        send_error=send_error,
        initialize_tracking=lambda conversation_id: calls.append({"tracked": conversation_id}),
        now_ms_factory=lambda: 999,
        logger=logger,
    )

    asyncio.run(run_chat_websocket_session(websocket, "conv-1", deps))

    assert calls[0] == {"tracked": "conv-1"}
    assert calls[1]["data"] == {"type": "ping", "ts": 1}
    assert calls[1]["runtime"] is runtime
    assert calls[1]["now_ms"] == 999
    assert calls[1]["handlers"] == "handlers"
    assert db.closed is True


def test_run_chat_websocket_session_reports_internal_errors():
    logger = FakeLogger()
    db = FakeDb()
    websocket = FakeWebSocket(received=[{"type": "ping"}])
    runtime = SimpleNamespace(conversation=SimpleNamespace(id="conv-1"))
    sent_errors = []

    async def route_event(**kwargs):
        raise RuntimeError("boom")

    async def send_error(_websocket, message, code):
        sent_errors.append((message, code))

    deps = ChatWebSocketSessionDeps(
        session_factory=lambda: db,
        build_runtime=lambda local_db, conversation_id: runtime,
        make_handlers=lambda: object(),
        route_event=route_event,
        send_error=send_error,
        initialize_tracking=lambda conversation_id: None,
        now_ms_factory=lambda: 999,
        logger=logger,
    )

    asyncio.run(run_chat_websocket_session(websocket, "conv-1", deps))

    assert sent_errors == [("boom", "INTERNAL_ERROR")]
    assert any(level == "exception" for level, _ in logger.records)
    assert db.closed is True
