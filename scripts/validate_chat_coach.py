#!/usr/bin/env python3
"""Quick Chat Coach validation via WebSocket"""

import asyncio
import websockets
import json

CONV_ID = "c2887d30-ef4e-4415-8656-b51e4ee76114"
WS_URL = f"ws://localhost:8000/api/v1/chat/ws/{CONV_ID}"

async def test_chat():
    async with websockets.connect(WS_URL, timeout=30) as ws:
        # Send user message
        await ws.send_json({
            "type": "user_message",
            "content": "Hello! This is a validation test.",
        })

        # Receive response
        while True:
            response = await ws.recv()
            event = json.loads(response)

            if event.get("type") == "assistant_stream_token":
                token = event.get("token", "")
                print(token, end="", flush=True)

            elif event.get("type") == "assistant_done":
                print("\n\n[Done] Full response received")
                break

            elif event.get("type") == "teacher_analysis":
                print("\n\n[Teacher Analysis] Received with keys:", list(event.get("analysis", {}).keys()))
                break

            elif event.get("type") == "error":
                print(f"\n[Error] {event.get('message')}")
                break

asyncio.run(test_chat())
