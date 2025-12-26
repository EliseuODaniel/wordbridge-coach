#!/usr/bin/env python3
"""
Hotfix Validation Test

Tests:
1. Chat responds with non-empty text (Hotfix A - empty stop strings)
2. Draft feedback includes rich signals (Hotfix C - topic/intent/rewrite)
"""

import asyncio
import websockets
import json
from typing import Dict, Any

# Test configuration
WS_URL = "ws://localhost:8000/api/v1/chat/ws"
TEST_USER_ID = "hotfix-test-user"


async def test_chat_response_not_empty():
    """
    Test that chat responds with actual text (not empty).

    Validates Hotfix A: Empty stop strings fix.
    """
    print("\n" + "="*60)
    print("TEST 1: Chat Response Not Empty (Hotfix A)")
    print("="*60)

    try:
        async with websockets.connect(WS_URL) as websocket:
            # Connect
            connect_msg = {
                "type": "connect",
                "user_id": TEST_USER_ID,
                "mode": "chat"
            }
            await websocket.send(json.dumps(connect_msg))
            print(f"✓ Sent: {connect_msg}")

            # Receive connected confirmation
            response = await websocket.recv()
            data = json.loads(response)
            print(f"✓ Received: {data.get('type')}")

            # Send test message
            user_msg = {
                "type": "user_message",
                "content": "hello"
            }
            await websocket.send(json.dumps(user_msg))
            print(f"✓ Sent user message: '{user_msg['content']}'")

            # Collect assistant response
            full_response = ""
            async for message in websocket:
                data = json.loads(message)

                if data.get("type") == "token":
                    token = data.get("token", "")
                    full_response += token
                    print(f"  Token: '{token}'")

                elif data.get("type") == "assistant_message_end":
                    print(f"\n✓ Received assistant_message_end")
                    break

                elif data.get("type") == "error":
                    print(f"\n✗ ERROR: {data.get('message')}")
                    return False

            # Validate response is NOT empty
            print(f"\nFull response: '{full_response}'")
            if full_response.strip():
                print(f"✅ PASS: Response is not empty ({len(full_response)} chars)")
                return True
            else:
                print(f"✗ FAIL: Response is empty!")
                return False

    except Exception as e:
        print(f"✗ FAIL: Exception during test: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_draft_feedback_rich_signals():
    """
    Test that draft_feedback includes rich signals (topic/intent/rewrite).

    Validates Hotfix C: Enriched draft feedback.
    """
    print("\n" + "="*60)
    print("TEST 2: Draft Feedback Rich Signals (Hotfix C)")
    print("="*60)

    try:
        async with websockets.connect(WS_URL) as websocket:
            # Connect
            connect_msg = {
                "type": "connect",
                "user_id": TEST_USER_ID,
                "mode": "chat"
            }
            await websocket.send(json.dumps(connect_msg))
            print(f"✓ Sent: {connect_msg}")

            # Receive connected confirmation
            response = await websocket.recv()
            data = json.loads(response)
            print(f"✓ Received: {data.get('type')}")

            # Send draft update with a simple text
            draft_msg = {
                "type": "draft_update",
                "content": "I go market"
            }
            await websocket.send(json.dumps(draft_msg))
            print(f"✓ Sent draft update: '{draft_msg['content']}'")

            # Receive draft_feedback
            async for message in websocket:
                data = json.loads(message)

                if data.get("type") == "draft_feedback":
                    print(f"\n✓ Received draft_feedback")
                    print(f"  Draft: '{data.get('draft', '')}'")
                    print(f"  Bar score: {data.get('bar_score', 0)}")
                    print(f"  Issues: {len(data.get('issues', []))} found")

                    # Check for rich signals
                    has_topic = data.get('topic') is not None
                    has_intent = data.get('intent') is not None
                    has_rewrite = data.get('rewrite') is not None
                    has_next_words = data.get('suggested_next_words') is not None
                    has_micro_tip = data.get('micro_tip') is not None

                    print(f"\nRich signals:")
                    print(f"  Topic: {data.get('topic')} {'✓' if has_topic else '✗'}")
                    print(f"  Intent: {data.get('intent')} {'✓' if has_intent else '✗'}")
                    print(f"  Rewrite: {data.get('rewrite')} {'✓' if has_rewrite else '✗'}")
                    print(f"  Next words: {data.get('suggested_next_words')} {'✓' if has_next_words else '✗'}")
                    print(f"  Micro tip: {data.get('micro_tip')} {'✓' if has_micro_tip else '✗'}")

                    # Validate at least some rich signals are present
                    if has_topic or has_intent or has_rewrite or has_next_words:
                        print(f"\n✅ PASS: Rich signals present in draft_feedback")
                        return True
                    else:
                        print(f"\n✗ FAIL: No rich signals in draft_feedback")
                        return False

                elif data.get("type") == "error":
                    print(f"\n✗ ERROR: {data.get('message')}")
                    return False

    except Exception as e:
        print(f"✗ FAIL: Exception during test: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all validation tests."""
    print("\n" + "="*60)
    print("HOTFIX VALIDATION TESTS")
    print("Testing critical chat fixes")
    print("="*60)

    # Test 1: Chat response not empty
    test1_pass = await test_chat_response_not_empty()

    # Test 2: Draft feedback rich signals
    test2_pass = await test_draft_feedback_rich_signals()

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Test 1 (Chat not empty): {'✅ PASS' if test1_pass else '✗ FAIL'}")
    print(f"Test 2 (Rich signals): {'✅ PASS' if test2_pass else '✗ FAIL'}")

    if test1_pass and test2_pass:
        print("\n🎉 ALL TESTS PASSED! Hotfix is working correctly.")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED! Check logs above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
