# Chat Coach Realtime Grammar - Implementation Status

**Date:** 2025-12-25
**Status:** 🚧 In Progress (2/10 tasks complete)
**OpenSpec:** `openspec/changes/2025-12-chat-coach-realtime-draft-coach-v1.md`

---

## Progress Summary

### ✅ Completed (2 tasks)

1. **Infrastructure** - LanguageTool Docker service
   - Added `languagetool` service to `docker-compose.yml`
   - Added feature flags to API environment
   - Commit: `af2ee6b`

2. **Backend Client** - LanguageTool Python client
   - Created `api/app/services/languagetool_client.py`
   - Implements `/v2/check` API calls
   - Converts LT matches → DraftIssue format
   - Maps categories (grammar/spelling/style)
   - Extracts highlight_spans and suggestions
   - Commit: `7958115`

### ⏳ Pending (8 tasks)

3. **Backend Integration** - Integrate LT in chat.py
   - Update `handle_draft_update` to call LanguageTool
   - Add feature flag check (`CHAT_DRAFT_GRAMMAR_PROVIDER`)
   - Fallback to MockLLMProvider if LT disabled/down
   - Add throttle cache (250ms min interval)

4. **Backend Suggestions** - Word completion service
   - Create `api/app/services/word_completion_service.py`
   - Load 10k words dataset
   - Implement prefix match with binary search
   - Return top N by frequency

5. **Backend Suggestions** - Build next-word model
   - Create `api/scripts/build_next_word_model.py`
   - Process sentence bank → bigram model
   - Save to `api/data/en_next_word_model.json`

6. **Backend Suggestions** - Next-word service
   - Create `api/app/services/next_word_service.py`
   - Load model JSON
   - Suggest next words based on last token

7. **Frontend Scroll** - Internal scroll for messages
   - Update `ChatCoachSession.tsx` layout
   - Fixed header/footer, scrollable messages
   - Smart scroll (auto-scroll only near bottom)
   - "New messages" button

8. **Frontend Chips** - Clickable suggestion chips
   - Render chips below textarea
   - Implement `insertSuggestion()` function
   - Maintain focus after insertion
   - Style chips with hover states

9. **Tests** - Unit tests for LT client
   - `api/tests/test_languagetool_client.py`
   - Mock HTTP responses
   - Test span mapping
   - Test category mapping

10. **Tests** - E2E Playwright tests
    - Grammar detection flow
    - Suggestion insertion
    - Scroll behavior

---

## Current Commit History

```
7958115 feat(chat-coach): add LanguageTool client for real grammar checking
af2ee6b infra(chat-coach): add LanguageTool service + feature flags
2dd1333 docs(openspec): propose realtime grammar + suggestions
```

---

## Next Steps (Priority Order)

### Immediate (Critical Path)
1. **Integrate LanguageTool in chat.py** (Takes ~30 min)
   - Edit `api/app/api/api_v1/endpoints/chat.py`
   - Add LT client instantiation
   - Call `lt_client.check_text()` in draft_update
   - Merge with existing micro_eval results

2. **Create simplified suggestions** (Takes ~20 min)
   - Skip full word completion for now
   - Use heuristic suggestions from MockLLMProvider
   - Just increase count from 3 to 8
   - Add to draft_feedback response

3. **Test basic grammar flow** (Takes ~15 min)
   - `docker compose up -d languagetool`
   - Test "lets go" → should show error
   - Test "i am fine" → should show capitalization

### Short-term (Important but not blocking)
4. **Add internal scroll to ChatCoachSession**
   - Layout changes only
   - No backend changes needed

5. **Add suggestion chips UI**
   - Frontend only
   - Can start with mock data

### Medium-term (Nice to have)
6. **Build full word completion service**
7. **Build next-word model**
8. **Write unit tests**
9. **Write E2E tests**

---

## How to Continue

### Option A: Complete Core Feature Fast
1. Integrate LanguageTool in chat.py (30 min)
2. Increase suggestion count in MockLLMProvider (5 min)
3. Test manually "lets go" (5 min)
4. Done! Basic real grammar working

### Option B: Full Implementation
Follow the full task list in order (3-4 hours of work)

### Option C: Incremental
Do task 3 only, then test. Continue later with remaining tasks.

---

## Testing LanguageTool Service

Once service is running:

```bash
# Start LanguageTool
docker compose up -d languagetool

# Check health
curl http://localhost:8010/v2/check

# Test grammar check
curl -X POST http://localhost:8010/v2/check \
  -H "Content-Type: application/json" \
  -d '{
    "text": "lets go",
    "language": "en-US"
  }'
```

Expected response:
```json
{
  "matches": [
    {
      "message": "This sentence does not start with an uppercase letter.",
      "shortMessage": "Capitalize first letter",
      "offset": 0,
      "length": 4,
      "replacements": [
        {"value": "Lets"},
        {"value": "It's"}
      ],
      "rule": { "category": "CASING" }
    }
  ]
}
```

---

## Integration Code Snippet

For `api/app/api/api_v1/endpoints/chat.py`:

```python
from app.services.languagetool_client import LanguageToolClient
import os

# In handle_draft_update or similar
async def handle_draft_update(websocket, data):
    draft = data.get('draft', '')

    # Check if LT is enabled
    grammar_provider = os.getenv('CHAT_DRAFT_GRAMMAR_PROVIDER', 'heuristic')

    if grammar_provider == 'languagetool':
        lt_url = os.getenv('CHAT_LANGUAGETOOL_URL', 'http://languagetool:8010')
        lt_client = LanguageToolClient(base_url=lt_url)

        try:
            lt_issues = await lt_client.check_text(draft)

            # Merge with existing issues
            all_issues = lt_issues + existing_issues
        except Exception as e:
            logger.warning(f"LT failed, using heuristic: {e}")
            all_issues = existing_issues  # Fallback
    else:
        all_issues = existing_issues  # Heuristic only

    # Send feedback
    await websocket.send_json({
        'type': 'draft_feedback',
        'issues': all_issues,
        ...
    })
```

---

## Notes

- LanguageTool image: `erikvl72/languagetool:latest`
- HTTP API: `/v2/check`
- Port: 8010
- Response time: ~50-200ms per check
- Throttle needed: 250ms min interval

---

**Prepared by:** Claude Code (executor)
**Tokens Used:** ~114k / ~200k (plenty remaining for completion)
