#!/usr/bin/env python3
"""Test 'hi, how are ioy?' with fresh conversation."""

import asyncio
import websockets
import json
import requests

API_URL = "http://localhost:8000/api/v1/chat/conversations"
WS_BASE = "ws://localhost:8000/api/v1/chat/ws"
TEST_TEXT = "hi, how are ioy?"

async def test_ioy():
    print("\n" + "="*70)
    print(f"Testing: '{TEST_TEXT}'")
    print("="*70)

    # Step 1: Create conversation
    print("\n1. Creating conversation...")
    try:
        response = requests.post(API_URL, json={"user_id": "test-ioy-validation"})
        response.raise_for_status()
        conversation_data = response.json()
        conversation_id = conversation_data.get("id")
        print(f"   ✓ Created: {conversation_id}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return

    # Step 2: Connect WebSocket
    print("\n2. Connecting WebSocket...")
    ws_url = f"{WS_BASE}/{conversation_id}"
    try:
        async with websockets.connect(ws_url) as ws:
            print(f"   ✓ Connected")

            # Step 3: Send draft_update
            print(f"\n3. Sending draft_update: '{TEST_TEXT}'")
            await ws.send(json.dumps({
                "type": "draft_update",
                "conversation_id": conversation_id,
                "draft_text": TEST_TEXT
            }))

            # Step 4: Receive feedback
            response = await ws.recv()
            data = json.loads(response)

            if data.get("type") == "draft_feedback":
                issues = data.get("issues", [])
                draft = data.get("draft", "")

                print(f"\n✅ Received draft_feedback")
                print(f"   Draft text: '{draft}'")
                print(f"   Issues found: {len(issues)}")

                for i, issue in enumerate(issues):
                    category = issue.get("category")
                    title = issue.get("title")
                    highlights = issue.get("highlight_spans", [])
                    suggestions = issue.get("suggestions", [])

                    # Get highlighted text
                    highlighted_text = ""
                    if highlights and draft:
                        start = highlights[0].get("start", 0)
                        end = highlights[0].get("end", 0)
                        highlighted_text = draft[start:end]

                    print(f"\n  Issue {i+1}:")
                    print(f"    Category: {category}")
                    print(f"    Title: {title}")
                    print(f"    Highlight: {highlights} -> '{highlighted_text}'")
                    print(f"    Suggestions: {suggestions}")

                # Check for "ioy"
                ioy_found = False
                for issue in issues:
                    highlights = issue.get("highlight_spans", [])
                    for span in highlights:
                        start = span.get("start", 0)
                        end = span.get("end", 0)
                        highlighted_text = draft[start:end]
                        if "ioy" in highlighted_text.lower():
                            ioy_found = True
                            print(f"\n✅✅✅ SUCCESS: 'ioy' detected!")
                            break

                if not ioy_found:
                    print(f"\n❌ FAILED: 'ioy' NOT detected")
                    print(f"   Expected: Issue with 'ioy' highlighted")
                    print(f"   Got: {len(issues)} issues")

            else:
                print(f"\n⚠️  Unexpected response: {data.get('type')}")

    except Exception as e:
        print(f"\n❌ WebSocket error: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*70)

if __name__ == "__main__":
    asyncio.run(test_ioy())
