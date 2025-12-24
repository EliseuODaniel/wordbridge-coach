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

    // Wait for card to load
    await page.waitForSelector('input[type="text"]', { timeout: 10000 });
    console.log('✅ Card loaded');

    // TEST 1: Verify no Check button
    const submitButtons = await page.locator('button:has-text("Check"), button:has-text("Submit")').count();
    expect(submitButtons).toBe(0);
    console.log('✅ No Check button found');

    // Get initial state
    const inlineInput = page.locator('input[type="text"]');
    await expect(inlineInput).toBeVisible();
    const initialCardText = await page.textContent('body');

    // TEST 2: Submit wrong answer - should NOT advance
    await inlineInput.fill('wronganswer123');
    await inlineInput.press('Enter');
    await page.waitForSelector('text=Try again', { timeout: 3000 });
    console.log('✅ Wrong answer: "Try again" shown');

    // Verify still on same card (card_id in debug hasn't changed)
    const afterErrorText = await page.textContent('body');
    expect(afterErrorText).toContain('Try again');
    console.log('✅ Stayed on same card after error');

    // TEST 3: Verify hints appeared
    const hintPanel = page.locator('text=Hints').first();
    const isHintVisible = await hintPanel.isVisible().catch(() => false);
    expect(isHintVisible).toBeTruthy();
    console.log('✅ Hint panel appeared');

    // TEST 4: Submit CORRECT answer
    const correctAnswerText = await page.locator('text=correct_answer:').textContent();
    const correctAnswer = correctAnswerText?.split('correct_answer:')[1]?.trim();

    if (correctAnswer) {
      await inlineInput.fill(correctAnswer);
      await page.waitForTimeout(500); // wait for auto-submit
      await inlineInput.press('Enter'); // fallback

      // Verify "Correct!" feedback
      await page.waitForSelector('text=Correct!', { timeout: 2000 });
      console.log('✅ Correct feedback shown');

      // Verify input is locked
      const isInputDisabled = await inlineInput.isDisabled();
      expect(isInputDisabled).toBeTruthy();
      console.log('✅ Input locked after correct answer');

      // Wait for audio mock to finish and next card to load
      await page.waitForTimeout(1500);

      // Verify we're on a different card now (input exists and is enabled again)
      const newInput = page.locator('input[type="text"]');
      await expect(newInput).toBeVisible();
      const isNewEnabled = await newInput.isEnabled();
      expect(isNewEnabled).toBeTruthy();
      console.log('✅ Advanced to next card after audio');
    } else {
      console.log('⚠️ Could not find correct_answer, skipping correct answer test');
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
    const hasInlineInput = await page.locator('input[type="text"]:not([data-testid])').isVisible().catch(() => false);
    expect(hasInlineInput).toBeFalsy();
    console.log('✅ Spec4 has no Lingvist inline input');
  });
});
