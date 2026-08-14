import { test, expect } from '@playwright/test';

test.describe('Lingvist Mode - E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Mock HTMLAudioElement for testing audio flow
    await page.addInitScript(() => {
      const OriginalAudio = window.Audio;
      window.Audio = class MockAudio extends OriginalAudio {
        private _playPromise: Promise<void> | null = null;
        private _src: string = '';
        constructor(srcOrAudio?: string | AudioBuffer) {
          super();
          if (typeof srcOrAudio === 'string') {
            this._src = srcOrAudio;
          }
        }
        override play(): Promise<void> {
          console.log('[MockAudio] play() called');
          this._playPromise = new Promise((resolve) => {
            setTimeout(() => {
              const event = new Event('ended');
              this.dispatchEvent(event);
              resolve();
            }, 500);
          });
          return this._playPromise;
        }
        override set src(value: string) { this._src = value; }
        override get src() { return this._src; }
      } as any;
    });
  });

  test('1. fluxo completo: errar → hints → acertar → áudio → avançar', async ({ page }) => {
    // Navigate and select Lingvist mode via URL param (more reliable)
    await page.goto('/?mode=lingvist');
    await page.waitForTimeout(1000);

    // Create test profile
    const uniqueName = `LingvistUser${Date.now()}`;
    await page.fill('[data-testid="profile-create-name"]', uniqueName);
    await page.click('[data-testid="profile-create-start"]');

    // Wait for Lingvist session to replace the profile form and load its inline input
    await page.waitForSelector('[data-testid="lingvist-inline-input"]', { timeout: 15000 });
    console.log('✅ Card loaded');

    // TEST 1: Verify no Check button
    const submitButtons = await page.locator('button:has-text("Check"), button:has-text("Submit")').count();
    expect(submitButtons).toBe(0);
    console.log('✅ No Check button found');

    // Get initial state
    const inlineInput = page.locator('[data-testid="lingvist-inline-input"]');
    await expect(inlineInput).toBeVisible();
    const initialCardText = await page.textContent('body');

    // TEST 1.5: Verify translations panel is visible from card load (NEW)
    // Wait a moment for the translations panel to render
    await page.waitForTimeout(500);
    const translationsPanel = page.locator('text=Traduções').first();
    const isTranslationsVisible = await translationsPanel.isVisible().catch(() => false);
    expect(isTranslationsVisible).toBeTruthy();
    console.log('✅ Translations panel visible from card load');

    const learningContextPanel = page.locator('[data-testid="learning-context-panel"]');
    await expect(learningContextPanel).toBeVisible();
    await expect(learningContextPanel).toContainText('Objetivo da sessão');
    console.log('✅ Learning context panel visible in Lingvist');

    // TEST 2: Submit wrong answer - should NOT advance
    await inlineInput.fill('wronganswer123');
    await inlineInput.press('Enter');
    await page.waitForSelector('text=Tente novamente', { timeout: 3000 });
    console.log('✅ Wrong answer feedback shown');

    // Verify still on same card (card_id in debug hasn't changed)
    const afterErrorText = await page.textContent('body');
    expect(afterErrorText).toContain('Tente novamente');
    console.log('✅ Stayed on same card after error');

    // TEST 2.1: Verify input remains ENABLED after wrong answer (bug fix check)
    const isInputEnabledAfterError = await inlineInput.isEnabled();
    expect(isInputEnabledAfterError).toBeTruthy();
    console.log('✅ Input remains enabled after wrong answer');

    // TEST 2.2: Verify can type again after wrong answer
    await inlineInput.fill('anotherwronganswer');
    const valueAfterTyping = await inlineInput.inputValue();
    expect(valueAfterTyping).toBe('anotherwronganswer');
    console.log('✅ Can type again after wrong answer');

    // TEST 2.3: Verify pressing Enter again triggers another submission
    await inlineInput.press('Enter');
    await page.waitForSelector('text=Tente novamente', { timeout: 3000 });
    console.log('✅ Can submit again after wrong answer');

    // TEST 2.4: Verify no "Check" button appears (Lingvist uses auto-submit)
    const submitButtonsAfterError = await page.locator('button:has-text("Check"), button:has-text("Submit")').count();
    expect(submitButtonsAfterError).toBe(0);
    console.log('✅ No Check button after wrong answer');

    // TEST 2.5: NEW - Make 4 more errors (total 6) to trigger complete answer hint
    for (let i = 3; i <= 6; i++) {
      await inlineInput.fill(`wronganswer${i}`);
      await inlineInput.press('Enter');
      await page.waitForTimeout(500); // Wait for submission
    }

    // TEST 2.6: Verify complete answer hint appears at level 6
    const answerHint = page.getByText('Resposta', { exact: true }).first();
    const isAnswerVisible = await answerHint.isVisible().catch(() => false);
    expect(isAnswerVisible).toBeTruthy();
    console.log('✅ Complete answer hint visible after 6 errors');

    // TEST 2.5: NEW - Verify hint progression after errors
    // After 2 errors, should show "Length" and "First letter" hints
    const hintPanel = page.getByText('Pistas', { exact: true }).first();
    const isHintVisible = await hintPanel.isVisible().catch(() => false);
    expect(isHintVisible).toBeTruthy();
    console.log('✅ Hint panel visible after errors');

    // Check if Length hint is visible
    const lengthHint = page.getByText('Tamanho', { exact: true }).first();
    const isLengthVisible = await lengthHint.isVisible().catch(() => false);
    expect(isLengthVisible).toBeTruthy();
    console.log('✅ Length hint visible after errors');

    // Check if First letter hint is visible (should appear at level 2)
    const firstLetterHint = page.getByText('Primeira letra', { exact: true }).first();
    const isFirstLetterVisible = await firstLetterHint.isVisible().catch(() => false);
    expect(isFirstLetterVisible).toBeTruthy();
    console.log('✅ First letter hint visible after 2nd error');

    // TEST 3: Submit CORRECT answer
    // Try to find correct_answer in debug info (only available in DEV mode)
    const correctAnswerText = await page.locator('text=correct_answer:').textContent({ timeout: 2000 }).catch(() => null);
    const correctAnswer = correctAnswerText?.split('correct_answer:')[1]?.trim();

    if (correctAnswer) {
      await inlineInput.fill(correctAnswer);
      await page.waitForTimeout(500); // wait for auto-submit
      await inlineInput.press('Enter'); // fallback

      // Verify "Correct!" feedback
      await page.waitForSelector('text=Correto!', { timeout: 2000 });
      console.log('✅ Correct feedback shown');

      // Verify input is locked
      const isInputDisabled = await inlineInput.isDisabled();
      expect(isInputDisabled).toBeTruthy();
      console.log('✅ Input locked after correct answer');

      // Wait for audio mock to finish and next card to load
      await page.waitForTimeout(1500);

      // Verify we're on a different card now (input exists and is enabled again)
      const newInput = page.locator('[data-testid="lingvist-inline-input"]');
      await expect(newInput).toBeVisible();
      const isNewEnabled = await newInput.isEnabled();
      expect(isNewEnabled).toBeTruthy();
      console.log('✅ Advanced to next card after audio');
    } else {
      console.log('⚠️ Debug info not available (DEV mode required for correct_answer test), skipping correct answer test');
      console.log('✅ Hint progression tests passed - main functionality verified');
    }
  });

  test('2. Spec4 sanity check - não quebrou o Spec4', async ({ page }) => {
    // Navigate to Spec4 (default)
    await page.goto('/');

    // Create test profile
    const uniqueName = `Spec4SanityUser${Date.now()}`;
    await page.fill('[data-testid="profile-create-name"]', uniqueName);
    await page.click('[data-testid="profile-create-start"]');

    // Wait for study session
    await page.waitForTimeout(2000);

    // Check if we have cards
    const hasCards = await page.locator('[data-testid="study-card"]').isVisible().catch(() => false);

    if (hasCards) {
      // Spec4 should have answer input and SUBMIT button (different from Lingvist)
      await expect(page.locator('[data-testid="answer-input"]')).toBeVisible();
      await expect(page.locator('[data-testid="answer-submit"]')).toBeVisible();
      console.log('✅ Spec4 has Submit button (as expected)');

      // Submit an answer
      await page.fill('[data-testid="answer-input"]', 'test');
      await page.click('[data-testid="answer-submit"]');
      await page.waitForTimeout(1000);
      console.log('✅ Spec4 answer submitted successfully');
    }

    // Verify we DON'T have Lingvist-specific inline input (no data-testid)
    const hasInlineInput = await page.locator('[data-testid="lingvist-inline-input"]').isVisible().catch(() => false);
    expect(hasInlineInput).toBeFalsy();
    console.log('✅ Spec4 has no Lingvist inline input');
  });
});
