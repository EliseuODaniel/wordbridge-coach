#!/usr/bin/env python3
"""
Diagnostic script for LanguageTool false negative bug.

Tests:
1. Direct LT API call with "hi, how are ioy?"
2. WebSocket draft_update with same text
3. Compare results to identify where issues are lost
"""

import requests
import asyncio
import websockets
import json

LT_URL = "http://localhost:8010/v2/check"
WS_URL = "ws://localhost:8000/api/v1/chat/ws/117ff80d-bcb7-4356-a0c9-7fedca019237"
TEST_TEXT = "hi, how are ioy?"

print("="*70)
print("LanguageTool False Negative Diagnostic")
print("="*70)

# Test 1: Direct LT API
print("\n[TEST 1] Direct LanguageTool API")
print("-" * 70)
print(f"URL: {LT_URL}")
print(f"Text: '{TEST_TEXT}'")
print(f"Language: en-US")

try:
    params = {"language": "en-US"}
    data = {"text": TEST_TEXT, "enabledOnly": "false"}

    response = requests.post(LT_URL, params=params, data=data, timeout=5)
    response.raise_for_status()

    result = response.json()
    matches = result.get("matches", [])

    print(f"\n✅ LT API Response: {len(matches)} match(es)")

    for i, match in enumerate(matches):
        msg = match.get("message", "")
        offset = match.get("offset", 0)
        length = match.get("length", 0)
        context = match.get("context", {}).get("text", "")
        highlighted = context[offset:offset + length]
        replacements = [r.get("value", "") for r in match.get("replacements", [])[:3]]

        print(f"\n  Match {i+1}:")
        print(f"    Message: {msg}")
        print(f"    Position: {offset}:{offset+length} -> '{highlighted}'")
        print(f"    Suggestions: {replacements}")

    # Check for "ioy"
    ioy_found = False
    for match in matches:
        offset = match.get("offset", 0)
        length = match.get("length", 0)
        context = match.get("context", {}).get("text", "")
        highlighted = context[offset:offset + length]
        if "ioy" in highlighted.lower():
            ioy_found = True
            print(f"\n✅ SUCCESS: 'ioy' detected by LT!")
            break

    if not ioy_found:
        print(f"\n⚠️  WARNING: 'ioy' NOT detected by LT")
        print("   This means LanguageTool itself doesn't flag this as an error")

except Exception as e:
    print(f"\n❌ ERROR: {e}")

# Test 2: WebSocket draft_update
print("\n" + "="*70)
print("[TEST 2] WebSocket draft_update")
print("-" * 70)
print(f"WebSocket: {WS_URL}")
print(f"Sending draft_update with text: '{TEST_TEXT}'")


async def test_websocket():
    try:
        async with websockets.connect(WS_URL) as ws:
            # Send draft_update
            await ws.send(json.dumps({
                "type": "draft_update",
                "conversation_id": "117ff80d-bcb7-4356-a0c9-7fedca019237",
                "draft_text": TEST_TEXT
            }))

            # Receive response
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
                            print(f"\n✅ SUCCESS: 'ioy' detected via WebSocket!")
                            break

                if not ioy_found:
                    print(f"\n❌ BUG CONFIRMED: 'ioy' NOT detected via WebSocket!")
                    print("   LT API found it, but WebSocket pipeline lost it")

            elif data.get("type") == "error":
                error_msg = data.get("message", "Unknown error")
                error_code = data.get("code", "UNKNOWN")
                print(f"\n❌ WebSocket Error:")
                print(f"   Code: {error_code}")
                print(f"   Message: {error_msg}")

            else:
                print(f"\n⚠️  Unexpected response type: {data.get('type')}")
                print(f"   Full response: {json.dumps(data, indent=2)}")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


asyncio.run(test_websocket())

# Summary
print("\n" + "="*70)
print("DIAGNOSTIC SUMMARY")
print("="*70)
print("""
If LT API detects 'ioy' but WebSocket doesn't:
→ Bug is in the pipeline (language code, filtering, or overwrite)

If LT API also doesn't detect 'ioy':
→ LanguageTool limitation (may need different approach)

Next steps:
1. Check chat.py: _get_grammar_issues() language parameter
2. Check if micro_eval is overwriting LT issues
3. Check handle_user_message draft_feedback logic
""")
