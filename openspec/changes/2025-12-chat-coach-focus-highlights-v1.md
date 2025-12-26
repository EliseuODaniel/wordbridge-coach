# Change: Chat Coach - Persistent Focus + Error Highlights

**Status:** 📝 Proposal
**Created:** 2025-12-25
**Author:** Claude (executor)
**Related Specs:** 2025-12-chat-coach-mode-v1

---

## Overview

Two UX improvements for Chat Coach:

1. **Persistent Focus:** Textarea keeps focus ready for typing after each message
2. **Error Highlights:** Right panel shows draft text with highlighted error spans

**Impact:** Better typing flow + clearer visual feedback on mistakes

---

## Problem 1 - Focus Loss

**Current Behavior:**
- User sends message (Enter or Send button)
- After assistant response, user must click textarea again to type next message
- Frustrating flow that breaks conversation continuity

**Root Cause:**
- `frontend/src/components/ChatCoachSession.tsx` has `disabled={isStreaming}` on textarea
- Disabled inputs lose focus in React
- Even after re-enable, focus doesn't return automatically

**Evidence:**
```tsx
// Current code (line ~120)
<textarea
  ref={textareaRef}
  value={draftText}
  onChange={(e) => setDraftText(e.target.value)}
  disabled={isStreaming}  // ← PROBLEM: loses focus
  ...
/>
```

---

## Problem 2 - No Visual Error Location

**Current Behavior:**
- Backend sends `issues[].highlight_spans[]` with `{start, end}` positions
- Frontend only shows issue cards (title, explanation, suggestions)
- User sees "Grammar error" but not WHERE in their text

**Example:**
User types: "I go to the market yesterday"

Backend sends:
```json
{
  "issues": [{
    "title": "Past tense error",
    "explanation": "Use past tense for yesterday...",
    "highlight_spans": [{"start": 2, "end": 4}]  // "go"
  }]
}
```

Frontend shows:
- ✅ Title: "Past tense error"
- ✅ Explanation: "Use past tense..."
- ❌ No highlight on "go" in the original text
- ❌ User must manually find which word is wrong

**Root Cause:**
- `AnalysisPanel.tsx` doesn't receive `draftText` prop
- No rendering logic to highlight text spans
- Issue cards don't show the affected snippet

---

## Proposed Solution

### A) Persistent Focus (ChatCoachSession.tsx)

**A1. Remove disabled attribute:**
```tsx
<textarea
  ref={textareaRef}
  value={draftText}
  onChange={(e) => setDraftText(e.target.value)}
  // REMOVED: disabled={isStreaming}
  autoFocus={true}  // NEW
  ...
/>
```

**A2. Keep Send button disabled:**
```tsx
<button
  onClick={handleSendMessage}
  disabled={isStreaming || !draftText.trim()}  // Still disable during stream
>
  Send
</button>
```

**A3. Refocus after send:**
```tsx
const handleSendMessage = () => {
  if (isStreaming || !draftText.trim()) return;

  // ... send logic ...

  // Refocus textarea for next message
  requestAnimationFrame(() => {
    textareaRef.current?.focus();
  });
};
```

**A4. Refocus after assistant done:**
```tsx
const handleAssistantDone = () => {
  setIsStreaming(false);
  setDraftText('');  // Clear draft

  // Refocus for next message
  requestAnimationFrame(() => {
    textareaRef.current?.focus();
  });
};
```

**Prevention of double-send:**
- `handleSendMessage` already checks `if (isStreaming)` at start
- Keyboard handler (Enter) also checks `isStreaming`
- Removing `disabled` from textarea doesn't break this

---

### B) Error Highlights (AnalysisPanel.tsx)

**B1. Pass draftText to panel:**
```tsx
// In ChatCoachSession.tsx
<AnalysisPanel
  draftText={draftText}  // NEW
  issues={feedback.issues}
  ...
/>
```

**B2. Render highlighted text:**
```tsx
// In AnalysisPanel.tsx
interface AnalysisPanelProps {
  draftText?: string;  // NEW
  issues: DraftIssue[];
  ...
}

const renderHighlightedText = (text: string, issues: DraftIssue[]) => {
  // Extract all highlight_spans with category
  const spans = issues.flatMap(issue =>
    (issue.highlight_spans || []).map(span => ({
      ...span,
      category: issue.category,
      title: issue.title
    }))
  );

  // Sort by start, filter invalid, resolve overlaps
  const validSpans = spans
    .filter(s => s.start >= 0 && s.end <= text.length && s.start < s.end)
    .sort((a, b) => a.start - b.start);

  // Render text with <span> wrappers for highlights
  let lastEnd = 0;
  const parts = [];

  for (const span of validSpans) {
    if (span.start < lastEnd) continue;  // Skip overlap

    // Text before highlight
    if (span.start > lastEnd) {
      parts.push(text.slice(lastEnd, span.start));
    }

    // Highlighted text
    parts.push(
      <span key={`${span.start}-${span.end}`} className={`highlight-${span.category}`}>
        {text.slice(span.start, span.end)}
      </span>
    );

    lastEnd = span.end;
  }

  // Remaining text
  if (lastEnd < text.length) {
    parts.push(text.slice(lastEnd));
  }

  return parts;
};
```

**B3. Color scheme by category:**
```css
/* Tailwind classes */
.highlight-spelling → bg-red-900/40 border-b-2 border-red-500
.highlight-grammar → bg-yellow-900/40 border-b-2 border-yellow-500
.highlight-syntax → bg-orange-900/40 border-b-2 border-orange-500
.highlight-semantic → bg-purple-900/40 border-b-2 border-purple-500
.highlight-style → bg-blue-900/40 border-b-2 border-blue-500
```

**B4. Show snippet in issue card:**
```tsx
// For each issue, if highlight_spans exists:
{issue.highlight_spans && issue.highlight_spans.length > 0 && (
  <div className="snippet">
    <span className="text-xs text-gray-400">Error in:</span>
    <span className={`highlight-${issue.category}`}>
      {draftText.slice(span.start, span.end)}
    </span>
  </div>
)}
```

---

## Acceptance Criteria

### Focus Persistence
- **Send "hello" → Enter:** After assistant responds, cursor already in textarea (no click needed)
- **Click Send button:** After assistant responds, cursor in textarea
- **During streaming:** Can't send again (Send button disabled), but textarea remains focused
- **10 messages flow:** No clicks needed between messages, smooth conversation

### Error Highlights
- **Type "lets go":** Panel highlights "lets" in yellow/underline (grammar apostrophe missing)
- **Type "I go market":** Panel highlights "go" in yellow (wrong tense)
- **Hover on highlight:** Shows tooltip or badge with error category
- **Issue card snippet:** Each issue shows the specific error word/phrase highlighted
- **No crashes:** Invalid spans (out of bounds, negative) ignored gracefully

### No Regression
- **Spec4/Lingvist:** Manual test passes (card selection, audio, input still work)
- **Existing tests:** All pass

---

## Implementation Order

1. **Create OpenSpec proposal** (this doc)
2. **Apply focus persistence:**
   - Remove `disabled` from textarea
   - Add `autoFocus`
   - Add refocus logic in `handleSendMessage` and `handleAssistantDone`
3. **Apply error highlights:**
   - Pass `draftText` to AnalysisPanel
   - Implement `renderHighlightedText()` function
   - Add CSS classes for highlight colors
   - Show snippets in issue cards
4. **Validate:**
   - Manual UI test (focus flow + highlight visibility)
   - Optional: Playwright E2E test for focus
5. **Governance:**
   - Update this doc with screenshot evidence
   - Mark Applied/Validated

---

## Technical Notes

### Why `requestAnimationFrame` for focus?
- Ensures React has finished re-render before calling `.focus()`
- Prevents race condition where focus is lost immediately

### Why not `disabled` on textarea?
- Disabled inputs lose focus in DOM
- Better to control via:
  - Send button state (visual feedback)
  - Handler guards (functional safety)

### Overlapping spans resolution:
- Real texts might have overlapping error spans
- Algorithm: sort by start, skip if `start < lastEnd`
- Keeps first span, ignores overlapping later spans

### Span validation:
- Check `start >= 0` and `end <= text.length`
- Check `start < end` (not empty)
- Silently drop invalid spans to prevent crashes

---

## Files to Modify

### Frontend
1. `frontend/src/components/ChatCoachSession.tsx`:
   - Remove `disabled` from textarea
   - Add `autoFocus`
   - Add refocus in `handleSendMessage`
   - Add refocus in `handleAssistantDone`
   - Pass `draftText` prop to AnalysisPanel

2. `frontend/src/components/AnalysisPanel.tsx`:
   - Accept `draftText?: string` prop
   - Implement `renderHighlightedText()` function
   - Add "Seu texto" section with highlights
   - Add CSS classes for highlight colors
   - Show snippet in each issue card

---

## Validation Plan

### Manual Test Steps

1. **Focus Test:**
   - Open http://localhost:3007/?mode=chat
   - Type "hello" → Press Enter
   - Wait for assistant response
   - ✅ Cursor should be blinking in textarea (no click needed)
   - Type "how are you" → Press Enter
   - ✅ Cursor in textarea again
   - Click Send button (mouse)
   - ✅ Cursor in textarea after response

2. **Highlight Test:**
   - Type "lets go" (don't press Enter)
   - Look at right panel
   - ✅ Should see "Seu texto" section with "lets" highlighted (yellow underline)
   - ✅ Issue card should show snippet: "lets" highlighted
   - Type "I go to market"
   - ✅ "go" should be highlighted (yellow - wrong tense)
   - ✅ Explanation visible: "Use past tense..."

3. **Regression Test:**
   - Test Spec4: http://localhost:3007/?mode=card
   - ✅ Card selection works
   - ✅ Audio plays
   - ✅ Input accepts text

### Optional E2E Test
```typescript
test('textarea refocus after assistant response', async () => {
  render(<ChatCoachSession />);
  const textarea = screen.getByRole('textbox');

  // Type and send
  await user.type(textarea, 'hello');
  await user.keyboard('{Enter}');

  // Wait for assistant response
  await waitFor(() => expect(screen.getByText(/assistant/i)).toBeVisible());

  // Check focus
  expect(textarea).toHaveFocus();
});
```

---

## References

- **Parent Spec:** 2025-12-chat-coach-mode-v1
- **Component:** `frontend/src/components/ChatCoachSession.tsx`
- **Panel:** `frontend/src/components/AnalysisPanel.tsx`
- **API:** `DraftIssue.highlight_spans` format in `api/app/schemas/chat.py`
