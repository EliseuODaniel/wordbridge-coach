#!/usr/bin/env python3
"""Simple test for LanguageTool via existing conversation."""

import asyncio
import websockets
import json

WS_URL = "ws://localhost:8000/api/v1/chat/ws/117ff80d-bcb7-4356-a0c9-7fedca019237"

async def test_lt():
    print("\n" + "="*60)
    print("LanguageTool Simple Test")
    print("="*60)

    try:
        print("\n1. Connecting to WebSocket...")
        async with websockets.connect(WS_URL) as ws:
            print("✓ Connected")

            # Test "lets go"
            print("\n2. Testing 'lets go'...")
            await ws.send(json.dumps({
                "type": "draft_update",
                "conversation_id": "117ff80d-bcb7-4356-a0c9-7fedca019237",
                "draft_text": "lets go"
            }))

            response = await ws.recv()
            data = json.loads(response)

            if data.get("type") == "draft_feedback":
                print("✓ Received draft_feedback")
                issues = data.get("issues", [])
                print(f"   Issues found: {len(issues)}")

                for i, issue in enumerate(issues):
                    category = issue.get("category")
                    title = issue.get("title")
                    highlights = issue.get("highlight_spans", [])
                    suggestions = issue.get("suggestions", [])

                    print(f"\n   Issue {i+1}:")
                    print(f"     Category: {category}")
                    print(f"     Title: {title}")
                    print(f"     Highlights: {highlights}")
                    print(f"     Suggestions: {suggestions}")

                    if highlights and suggestions:
                        print(f"     ✓✓✓ PASS: Has highlights AND suggestions!")
                    else:
                        print(f"     ✗✗✗ FAIL: Missing highlights or suggestions")

            print("\n" + "="*60)
            print("✅ Test complete!")
            print("="*60)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_lt())
