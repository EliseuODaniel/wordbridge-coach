# Change: Chat Coach - Realtime Draft Grammar & Suggestions

**Status:** 📝 Proposal
**Created:** 2025-12-25
**Author:** Claude (executor)
**Related Specs:** 2025-12-chat-coach-mode-v1

---

## Overview

**Current Problems:**
1. **No real grammar checking:** `micro_eval` uses heuristics only, missing real spelling/grammar errors
2. **Poor draft feedback:** No "where you errored" visualization (highlight_spans exist but not used)
3. **Whole-page scroll:** Chat messages scroll the entire page, not the messages container
4. **Weak suggestions:** Only 3 ghost words, limited autocomplete, no real-time options

**Proposed Solutions:**
1. **LanguageTool integration:** Local Docker container for real grammar/spell checking
2. **Real-time suggestions:** 10k dataset for word completion + n-gram model for next-word prediction
3. **Internal scroll:** Messages container scrolls, page stays fixed
4. **Clickable chips:** Multiple suggestion chips that insert at cursor position

**Impact:** Professional draft coaching experience with real-time feedback

---

## Problem Analysis

### Problem 1: Weak Grammar Checking

**Current State:**
```python
# api/app/llm/mock_provider.py:688
async def micro_eval(self, context, lesson_frame, draft, student_profile):
    # Heuristic analysis only
    # Detects basic patterns but misses real errors
```

**Evidence:**
- "lets go" → No error detected (should be "let's")
- "i am fine" → No capitalization error detected
- Relies on pattern matching, not linguistic analysis

**Root Cause:**
- No NLP grammar engine
- MockLLMProvider uses simple regex/string matching

---

### Problem 2: Page Scroll Jumps

**Current State:**
```tsx
// frontend/src/components/ChatCoachSession.tsx:320
<div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
  {messages.map(...)}
</div>
```

**Problem:**
- When new message arrives, entire page scrolls
- Header and input area move out of view
- Poor UX for long conversations

---

### Problem 3: Limited Suggestions

**Current State:**
- Ghost suggestion: 1 option (Tab to accept)
- `suggested_next_words`: 3 words from heuristic
- No word completion while typing
- No contextual next-word prediction

---

## Proposed Solution

### Solution 1: LanguageTool Integration

**Architecture:**
```
ChatCoachSession → WebSocket → draft_update
                                  ↓
                          chat endpoint
                                  ↓
                          LanguageTool Client
                                  ↓
                          languagetool:8010/v2/check
                                  ↓
                          DraftIssue[] + highlight_spans
```

**Docker Service:**
```yaml
languagetool:
  image: erikvl72/languagetool:latest
  ports:
    - "8010:8010"
  environment:
    - LANGUAGETOOL_PORT=8010
    - LANGUAGETOOL_LANGUAGE_TOOL__ANONYMIZED__TEXT__MIN_LENGTH=0
```

**Python Client:**
```python
# api/app/services/languagetool_client.py
class LanguageToolClient:
    async def check_text(self, text: str) -> List[DraftIssue]:
        # Call /v2/check
        # Map LT rules → categories
        # Convert offset/length → start/end
        # Extract suggestions
```

**Mapping LT → DraftIssue:**
```python
LT_RULE_CATEGORY = {
    'GRAMMAR': 'grammar',
    'SPELLING': 'spelling',
    'STYLE': 'style',
    'TYPOGRAPHY': 'style',
    'CASING': 'grammar'  # "capitalize first letter"
}

def lt_match_to_issue(match, text) -> DraftIssue:
    return DraftIssue(
        category=LT_RULE_CATEGORY.get(match.rule.category, 'style'),
        title=match.message,
        explanation=match.shortMessage,
        highlight_spans=[{
            'start': match.offset,
            'end': match.offset + match.length
        }],
        suggestions=match.replacements[:3]  # Top 3
    )
```

**Feature Flags:**
```bash
CHAT_DRAFT_GRAMMAR_PROVIDER=languagetool|heuristic  # Default: heuristic
CHAT_LANGUAGETOOL_URL=http://languagetool:8010
```

---

### Solution 2: Real-time Suggestions

#### 2A. Word Completion (Prefix Match)

**Data Source:** `10k_words.tsv` (WordFrequency + Word)

**Algorithm:**
```python
import bisect

class WordCompletionService:
    def __init__(self, words_path='data/10k_words.tsv'):
        self.words = []  # List of (word, frequency)
        with open(words_path) as f:
            for line in f:
                freq, word = line.strip().split('\t')
                self.words.append((word, int(freq)))

        # Sort by word for binary search
        self.words.sort(key=lambda x: x[0])

    def complete_prefix(self, prefix: str, limit: int = 5) -> List[str]:
        # Binary search for prefix range
        start = bisect.bisect_left(self.words, (prefix, 0))
        results = []

        for i in range(start, min(start + limit * 2, len(self.words))):
            word, freq = self.words[i]
            if not word.startswith(prefix):
                break
            results.append((word, freq))

        # Return top N by frequency
        results.sort(key=lambda x: -x[1])
        return [word for word, _ in results[:limit]]
```

**Example:**
```python
service.complete_prefix("hel")  # ["hello", "help", "held", "hell", "helmet"]
```

#### 2B. Next-Word Prediction (N-Gram Model)

**Training Script:**
```python
# api/scripts/build_next_word_model.py

import json
from collections import Counter
from pathlib import Path

def build_bigram_model():
    sentence_bank = Path("data/english_100k_sentences.txt")

    bigrams = Counter()  # {(prev_word, curr_word): count}

    with open(sentence_bank) as f:
        for line in f:
            tokens = ['<s>'] + line.strip().lower().split() + ['</s>']

            for i in range(len(tokens) - 1):
                bigram = (tokens[i], tokens[i+1])
                bigrams[bigram] += 1

    # Group by prev_word, keep top 10 next words
    model = {}

    for (prev_word, curr_word), count in bigrams.items():
        if prev_word not in model:
            model[prev_word] = []

        model[prev_word].append((curr_word, count))

    # Sort and keep top 10
    for word in model:
        model[word].sort(key=lambda x: -x[1])
        model[word] = [w for w, _ in model[word][:10]]

    # Save
    with open("api/data/en_next_word_model.json", "w") as f:
        json.dump(model, f)

if __name__ == "__main__":
    build_bigram_model()
```

**Runtime Service:**
```python
# api/app/services/next_word_service.py

class NextWordService:
    def __init__(self, model_path='data/en_next_word_model.json'):
        with open(model_path) as f:
            self.model = json.load(f)

    def suggest_next(self, text: str, limit: int = 5) -> List[str]:
        # Get last word
        words = text.strip().lower().split()
        last_word = words[-1] if words else '<s>'

        # Return top N suggestions
        return self.model.get(last_word, [])[:limit]
```

**Feature Flags:**
```bash
CHAT_DRAFT_SUGGESTIONS_ENABLED=true
CHAT_DRAFT_SUGGESTIONS_MAX=8
CHAT_MICRO_EVAL_MIN_INTERVAL_MS=250  # Throttle checks
```

---

### Solution 3: Internal Scroll for Messages

**Frontend Changes:**

```tsx
// frontend/src/components/ChatCoachSession.tsx

<div className="h-screen flex flex-col bg-gray-900">
  {/* Fixed header */}
  <div className="flex-shrink-0">
    ...header...
  </div>

  {/* Scrollable messages area */}
  <div className="flex-1 overflow-y-auto" ref={messagesContainerRef}>
    {messages.map(...)}
  </div>

  {/* Fixed input area */}
  <div className="flex-shrink-0">
    ...input...
  </div>
</div>
```

**Smart Scroll Behavior:**
```tsx
// Auto-scroll only if user is near bottom (within 100px)
const isNearBottom = messagesContainerRef.current
  ? messagesContainerRef.current.scrollHeight -
    messagesContainerRef.current.scrollTop -
    messagesContainerRef.current.clientHeight < 100
  : true;

if (isNearBottom) {
  messagesContainerRef.current?.scrollTo({
    top: messagesContainerRef.current.scrollHeight,
    behavior: 'smooth'
  });
} else {
  setShowNewMessageButton(true);
}
```

---

### Solution 4: Clickable Suggestion Chips

**UI Design:**

```tsx
// Below textarea
<div className="flex flex-wrap gap-2">
  {suggestions.map((suggestion) => (
    <button
      key={suggestion}
      onClick={() => insertSuggestion(suggestion)}
      className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded-full text-sm"
    >
      {suggestion}
    </button>
  ))}
</div>
```

**Insert Logic:**
```tsx
const insertSuggestion = (word: string) => {
  const textarea = textareaRef.current;
  if (!textarea) return;

  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const text = draftText;

  // Insert word at cursor
  const before = text.slice(0, start);
  const after = text.slice(end);
  const newText = `${before}${word}${after}`;

  setDraftText(newText);

  // Restore focus and move cursor after inserted word
  requestAnimationFrame(() => {
    textarea.focus();
    const newPos = start + word.length;
    textarea.setSelectionRange(newPos, newPos);
  });
};
```

---

## Acceptance Criteria

### A) Real Grammar Detection
1. Type "lets go" → Panel shows grammar error
   - Highlight on "lets"
   - Suggestion: "let's"
2. Type "i am fine" → Panel shows grammar error
   - Highlight on "i"
   - Suggestion: "I"
3. Type "hello how r u" → Panel shows spelling/style errors
   - "r" highlighted → suggestion: "are"
   - "u" highlighted → suggestion: "you"

### B) Real-time Suggestions
1. Type "hel" → Show 5+ completion chips
   - "hello", "help", "held", "hell", "helmet"
2. Type "I want" → Show next-word suggestions
   - "to", "a", "the", "more", "you"
3. Click chip → Word inserted at cursor
   - Focus remains in textarea
   - Cursor positioned after inserted word

### C) Internal Scroll
1. Send 10+ messages
   - Page header stays visible
   - Input area stays visible
   - Only messages container scrolls
2. Scroll up in messages
   - New message arrives
   - "New messages" button appears
   - Click button → scroll to bottom

### D) Performance
1. Type continuously (fast)
   - Debounced checks (250ms)
   - No lag/stutter
   - Suggestions update smoothly

### E) No Regression
1. Spec4/Lingvist modes
   - Cards work normally
   - Audio plays
   - Input accepts text

---

## Implementation Plan

### Phase 1: Infrastructure (LanguageTool)
1. Add `languagetool` service to `docker-compose.yml`
2. Create `api/app/services/languagetool_client.py`
3. Add feature flags to `.env`
4. Test `/v2/check` endpoint manually

### Phase 2: Backend Grammar Integration
1. Update `handle_draft_update` in `chat.py`
   - Call LanguageTool if flag enabled
   - Fallback to MockLLMProvider if disabled
2. Implement span mapping (LT offset → draft position)
3. Add throttle cache (250ms min interval)
4. Unit tests for LT client + mapping

### Phase 3: Backend Suggestions
1. Create `api/scripts/build_next_word_model.py`
2. Run script to generate `en_next_word_model.json`
3. Create `api/app/services/word_completion_service.py`
4. Create `api/app/services/next_word_service.py`
5. Integrate into `draft_feedback` response

### Phase 4: Frontend Scroll
1. Update `ChatCoachSession.tsx` layout
   - Fixed header/footer
   - Scrollable messages container
2. Implement smart scroll logic
3. Add "New messages" button
4. Test with 20+ messages

### Phase 5: Frontend Chips
1. Add suggestion chips UI below textarea
2. Implement `insertSuggestion()` function
3. Ensure focus management
4. Style chips with hover states

### Phase 6: Testing
1. Unit tests (pytest):
   - LT client
   - Span mapping
   - Word completion
   - Next-word service
2. Playwright E2E:
   - Grammar detection flow
   - Suggestion insertion
   - Scroll behavior
3. Manual smoke test

---

## Feature Flags

```bash
# Grammar provider selection
CHAT_DRAFT_GRAMMAR_PROVIDER=languagetool  # | heuristic

# LanguageTool configuration
CHAT_LANGUAGETOOL_URL=http://languagetool:8010

# Suggestions
CHAT_DRAFT_SUGGESTIONS_ENABLED=true
CHAT_DRAFT_SUGGESTIONS_MAX=8

# Performance
CHAT_MICRO_EVAL_MIN_INTERVAL_MS=250
```

---

## Technical Notes

### LanguageTool Performance
- Local Docker: ~50-200ms per check
- Network latency: <5ms (localhost)
- Acceptable for real-time with debouncing

### Memory Usage
- Bigram model: ~5-10MB (10k sentences × 10 avg next words)
- Word list: ~500KB (10k words)
- Total: <20MB additional RAM

### Fallback Strategy
- If LT is down → use heuristic
- If model file missing → no next-word suggestions
- Always show something (graceful degradation)

---

## Files to Modify

### Infrastructure
1. `docker-compose.yml` - Add languagetool service
2. `.env` - Add feature flags

### Backend
3. `api/app/services/languagetool_client.py` - NEW
4. `api/app/services/word_completion_service.py` - NEW
5. `api/app/services/next_word_service.py` - NEW
6. `api/scripts/build_next_word_model.py` - NEW
7. `api/app/api/api_v1/endpoints/chat.py` - Integrate LT + suggestions
8. `api/data/en_next_word_model.json` - Generated artifact

### Frontend
9. `frontend/src/components/ChatCoachSession.tsx` - Scroll + chips
10. `frontend/src/components/AnalysisPanel.tsx` - Update for real issues

### Tests
11. `api/tests/test_languagetool_client.py` - NEW
12. `api/tests/test_word_completion.py` - NEW
13. `tests/e2e/chat-coach-grammar.spec.ts` - NEW

---

## Validation Plan

### Backend Tests
```bash
# Test LT client
pytest api/tests/test_languagetool_client.py -v

# Test word completion
pytest api/tests/test_word_completion.py -v
```

### E2E Tests
```typescript
test('realtime grammar detection', async ({ page }) => {
  await page.goto('http://localhost:3007/?mode=chat');
  const textarea = await page.locator('textarea');

  // Type "lets go"
  await textarea.type('lets go');

  // Check for grammar error in panel
  await expect(page.locator('text=let\'s')).toBeVisible();
});
```

### Manual Smoke Test
1. Open http://localhost:3007/?mode=chat
2. Type "lets go i am fine"
3. Verify: 2 errors detected, highlights visible
4. Click suggestion chip
5. Verify: Word inserted, focus maintained
6. Send 10 messages
7. Verify: Internal scroll works

---

## Success Metrics

- ✅ Grammar accuracy: >90% of common errors detected
- ✅ Suggestion relevance: >70% click-through rate
- ✅ Performance: <300ms response time
- ✅ No regression: Spec4/Lingvist work normally

---

## Risks & Mitigation

**Risk 1: LanguageTool slow**
- Mitigation: Debounce (250ms) + timeout (5s)
- Fallback: Heuristic provider

**Risk 2: Model file too large**
- Mitigation: Limit to 10k sentences, top 10 next words
- Expected size: <10MB

**Risk 3: Scroll behavior confusing**
- Mitigation: "New messages" button + smooth scroll
- User testing before merge

---

## References

- **Parent Spec:** 2025-12-chat-coach-mode-v1
- **LanguageTool API:** https://languagetool.org/http-api/swagger-ui/#!/default/post_check
- **10k Dataset:** `data/english_10k_words.tsv`
- **Sentence Bank:** `data/english_100k_sentences.txt`
