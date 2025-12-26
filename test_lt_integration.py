#!/usr/bin/env python3
"""
Quick validation script for LanguageTool integration in Chat Coach.

Tests:
1. Connects to WebSocket chat endpoint
2. Sends draft_update with "lets go"
3. Prints draft_feedback JSON
4. Verifies issues have highlight_spans and suggestions
"""

import asyncio
import websockets
import json
from typing import Dict, Any

# Configuration
WS_URL = "ws://localhost:8000/api/v1/chat/ws"
TEST_USER_ID = "test-lt-validation"


async def test_language_tool_integration():
    """Test LanguageTool integration via WebSocket."""
    print("\n" + "="*60)
    print("LanguageTool Integration Test")
    print("="*60)

    try:
        # Step 1: Create a conversation via REST API
        print("\n1. Creating conversation via REST API...")
        import aiohttp

        async with aiohttp.ClientSession() as session:
            create_response = await session.post(
                "http://localhost:8000/api/v1/chat/conversations",
                json={"user_id": TEST_USER_ID}
            )
            if create_response.status != 200:
                print(f"   ✗ Failed to create conversation: {create_response.status}")
                return

            conversation_data = await create_response.json()
            conversation_id = conversation_data.get("id")
            print(f"✓ Created conversation: {conversation_id}")

        # Step 2: Connect to WebSocket
        print("\n2. Connecting to WebSocket...")
        ws_url = f"{WS_URL}/{conversation_id}"
        async with websockets.connect(ws_url) as websocket:
            print(f"✓ Connected to {ws_url}")

            # Test cases
            test_cases = [
                ("lets go", "Should detect missing apostrophe"),
                ("i am fine", "Should detect capitalization"),
                ("hello how r u", "Should detect spelling/style errors")
            ]

            for test_text, description in test_cases:
                print(f"\n3. Testing: '{test_text}' - {description}")

                # Send draft_update
                draft_msg = {
                    "type": "draft_update",
                    "conversation_id": conversation_id,
                    "draft_text": test_text
                }
                await websocket.send(json.dumps(draft_msg))
                print(f"   Sent draft_update")

                # Wait for and parse draft_feedback
                async for message in websocket:
                    data = json.loads(message)

                    if data.get("type") == "draft_feedback":
                        print(f"   ✓ Received draft_feedback")

                        # Extract key fields
                        draft = data.get("draft", "")
                        issues = data.get("issues", [])
                        bar_score = data.get("bar_score_raw", 0)

                        print(f"   Draft: '{draft}'")
                        print(f"   Bar score: {bar_score}")
                        print(f"   Issues found: {len(issues)}")

                        # Validate issues
                        if issues:
                            for i, issue in enumerate(issues):
                                category = issue.get("category")
                                title = issue.get("title")
                                highlight_spans = issue.get("highlight_spans", [])
                                suggestions = issue.get("suggestions", [])

                                print(f"\n   Issue {i+1}:")
                                print(f"     Category: {category}")
                                print(f"     Title: {title}")

                                if highlight_spans:
                                    for span in highlight_spans:
                                        start = span.get("start")
                                        end = span.get("end")
                                        highlighted_text = draft[start:end] if draft else ""
                                        print(f"     Highlight: [{start}:{end}] '{highlighted_text}'")
                                else:
                                    print(f"     Highlight: NONE")

                                if suggestions:
                                    print(f"     Suggestions: {', '.join(suggestions[:3])}")
                                else:
                                    print(f"     Suggestions: NONE")

                                # CRITICAL CHECK: Verify highlight_spans and suggestions exist
                                if not highlight_spans:
                                    print(f"     ⚠️  WARNING: No highlight_spans found!")
                                if not suggestions:
                                    print(f"     ⚠️  WARNING: No suggestions found!")
                        else:
                            print(f"   ⚠️  No issues found (unexpected for this test case)")

                        break  # Move to next test case

                    elif data.get("type") == "error":
                        print(f"   ✗ ERROR: {data.get('message')}")
                        break

            print("\n" + "="*60)
            print("✅ Test completed!")
            print("="*60)
            print("\nNext steps:")
            print("1. If highlight_spans and suggestions are present, integration is working!")
            print("2. If not, check:")
            print("   - LanguageTool is running: docker compose ps")
            print("   - API logs: docker compose logs api --tail 50")
            print("   - Feature flag: CHAT_DRAFT_GRAMMAR_PROVIDER=languagetool")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        print("\nTroubleshooting:")
        print("1. Is API running? docker compose ps")
        print("2. Try: docker compose restart api")
        print("3. Check API health: curl http://localhost:8000/health")
        print("4. Check conversation creation: curl -X POST http://localhost:8000/api/v1/chat/conversations -H 'Content-Type: application/json' -d '{\"user_id\":\"test\"}'")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("LanguageTool Integration Validator")
    print("="*60)
    print("\nPrerequisites:")
    print("1. LanguageTool must be running: docker compose up -d languagetool")
    print("2. API must be running: docker compose restart api")
    print("\nStarting test...")

    asyncio.run(test_language_tool_integration())
