# Change: Lingvist Mode - Translations & Hints Improvements

**Status:** Partially Applied
**Created:** 2025-12-24
**Author:** Claude Code (executor)
**Branch:** `fix/lingvist-translations-hints`
**Spec:** [Link to spec if exists]

## Problem Statement

Lingvist Mode has 2 critical UX issues affecting user experience:

1. **Translations always showing "indisponível"** - Seed data creates sentences with empty translations and words without PT translations
2. **Hints stopping early without revealing full word** - hintLevel capped at 5, HintPanel only reveals ~60%

## Goals

Fix both issues without breaking Spec4 mode:

### Problem 1: Translations
- Add PT translations for at least ranks 1-500 words
- Maintain offline-first approach
- Keep seed data idempotent
- Display actual PT translations instead of "Tradução indisponível"

### Problem 2: Hints
- Increase MAX_HINT_LEVEL from 5 to 6
- Add final hint level showing complete answer
- Progressive reveal should continue increasing toward 100%
- Work even when translations don't exist

## Implementation Plan

### Problem 2: Hints (COMPLETED ✅)

**Files changed:**
- `frontend/src/components/LingvistSession.tsx`
- `frontend/src/components/HintPanel.tsx`
- `tests/e2e/tests/lingvist-session.spec.ts`

**Changes:**
1. Increase MAX_HINT_LEVEL from 5 to 6 in LingvistSession
2. Add Level 6 "Answer" hint in HintPanel showing complete correct answer
3. Progressive reveal now goes up to 80% before final answer
4. Update E2E test to verify complete answer appears after 6 errors

**Validation:**
- ✅ E2E test confirms complete answer visible after 6 errors
- ✅ All hint progression tests passing
- ✅ Spec4 sanity check passing

### Problem 1: Translations (PARTIAL ⚠️)

**Approach:**
- Created sample TSV file with 500 EN-PT word translations: `api/data/en_pt_word_translations_sample.tsv`
- Backend changes to `api/scripts/seed_data.py` needed to load and apply translations
- Sentence translations require more work (bilingual sentence bank)

**Remaining work:**
1. Add function to `seed_data.py` to load TSV file
2. Modify `create_10k_vocabulary()` to populate `Word.features.pt_translation`
3. Consider sentence translations (template-based or TSV)

**Created files:**
- `api/data/en_pt_word_translations_sample.tsv` (500 words translated)

## Validation Evidence

### Problem 2: Hints (COMPLETED ✅)

**E2E Test Results:**
```
✅ Complete answer hint visible after 6 errors
✅ Hint panel visible after errors
✅ Length hint visible after errors
✅ First letter hint visible after 2nd error
✅ Spec4 sanity check - not broken
2 passed (7.1s)
```

**Hint Progression:**
- Level 1: Length mask (`_ _ _`)
- Level 2: First letter
- Level 3: Reveal 2 letters
- Level 4: Reveal 4 letters
- Level 5: Reveal 6 letters (up to 80%)
- Level 6: **Complete answer** 💡

**Build Status:**
- ✅ TypeScript compilation successful
- ✅ Production build successful
- ✅ Container rebuilt and deployed
- ✅ All services healthy

### Problem 1: Translations (PARTIAL ⚠️)

**Created:**
- Sample translation file with 500 common words
- Format ready for integration into seed script

**Next Steps:**
- Backend changes to load TSV in seed_data.py
- Test with DB reset + reseed
- Verify SQL shows % of words with pt_translation
- Verify UI displays translations

## Definition of Done

### Completed ✅
- [x] Hint level 6 added showing complete answer
- [x] MAX_HINT_LEVEL increased to 6
- [x] Progressive reveal increased to 80%
- [x] E2E tests updated and passing
- [x] Spec4 verified unchanged
- [x] Container rebuilt and tested
- [x] Sample PT translation file created (500 words)
- [x] Git commits created

### Remaining ⚠️
- [ ] Backend changes to load PT translations in seed_data.py
- [ ] DB reset + reseed with translations
- [ ] SQL validation (% words with pt_translation)
- [ ] UI validation (PT translations visible)
- [ ] Sentence translations (optional enhancement)

## Commits

1. `fix(lingvist): add hint level 6 showing complete answer`
   - Increased MAX_HINT_LEVEL from 5 to 6
   - Added "Answer" hint showing complete word
   - Progressive reveal up to 80%
   - E2E test for 6 errors

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Translations file too large | Created 500-word sample, can expand incrementally |
| Seed data complexity | Changes isolated to seed_data.py, Spec4 untouched |
| Translation quality | Manual curation for common words |
| Performance impact | File loaded once at seed time only |

## Next Steps

1. **Complete Problem 1** (Backend):
   - Add `load_pt_translations()` function to seed_data.py
   - Modify `create_10k_vocabulary()` to apply translations
   - Test with `--full` seed flag

2. **SQL Validation**:
   ```sql
   -- Check % of words with PT translations
   SELECT
     COUNT(*) FILTER (WHERE features->>'pt_translation' IS NOT NULL AND features->>'pt_translation' != '') as with_pt,
     COUNT(*) as total,
     ROUND(100.0 * COUNT(*) FILTER (WHERE features->>'pt_translation' IS NOT NULL AND features->>'pt_translation' != '') / COUNT(*), 2) as percentage
   FROM words WHERE language_id = (SELECT id FROM languages WHERE code = 'en');
   ```

3. **UI Validation**:
   - Load Lingvist mode
   - Verify PT translations visible (not "indisponível")

4. **Future Enhancements**:
   - Bilingual sentence bank for sentence translations
   - Expand word translations beyond rank 500
   - Consider community contributions for translations
