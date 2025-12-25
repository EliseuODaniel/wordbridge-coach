import { test, expect } from '@playwright/test';

test.describe('Replay Previous Card', () => {
  test.beforeEach(async ({ page }) => {
    // Create a test user and start study session
    await page.goto('/');

    // Create profile with unique name
    const uniqueName = `ReplayTestUser${Date.now()}`;
    await page.fill('[data-testid="profile-create-name"]', uniqueName);
    await page.fill('[data-testid="profile-goal-slider"]', '100');
    await page.click('[data-testid="profile-create-start"]');

    // Wait for study container to load
    try {
      await page.waitForSelector('[data-testid="study-container"]', { timeout: 5000 });
    } catch (e) {
      // If no study container, check for no cards message
      await page.waitForSelector('text=No cards available', { timeout: 3000 });
    }

    // Stabilization wait
    await page.waitForTimeout(500);
  });

  test.describe('Spec4 Mode', () => {
    test('replay previous card button appears after advancing', async ({ page }) => {
      // Wait for page to stabilize
      await page.waitForTimeout(2000);

      // Check if we have cards
      const hasCards = await page.locator('[data-testid="study-card"]').isVisible().catch(() => false);
      if (!hasCards) {
        test.skip(true, 'No cards available');
        return;
      }

      // Initially, button should be disabled (no previous card yet)
      const replayButton = page.getByText('← Frase anterior');
      await expect(replayButton).toBeVisible();
      await expect(replayButton).toBeDisabled();

      // Answer first card correctly to advance to second card
      const answerInput = page.locator('[data-testid="answer-input"]');
      const submitButton = page.locator('[data-testid="answer-submit"]');

      // Get the current card's sentence to find the word (we'll need to extract it from the sentence)
      const sentenceElement = page.locator('[data-testid="study-card"]');
      const sentenceText = await sentenceElement.textContent();

      // For testing, we'll just type a simple answer and submit
      // In real testing, we'd parse the sentence to find the correct word
      await answerInput.fill('test');
      await submitButton.click();

      // Wait for next card to load (either correct or incorrect, doesn't matter for this test)
      await page.waitForTimeout(2000);

      // Now the button should be enabled
      await expect(replayButton).toBeEnabled();
    });

    test('opens modal with previous card content', async ({ page }) => {
      // Wait for page to stabilize
      await page.waitForTimeout(2000);

      // Check if we have cards
      const hasCards = await page.locator('[data-testid="study-card"]').isVisible().catch(() => false);
      if (!hasCards) {
        test.skip(true, 'No cards available');
        return;
      }

      // Answer first card to advance
      await page.locator('[data-testid="answer-input"]').fill('test');
      await page.locator('[data-testid="answer-submit"]').click();

      // Wait for next card
      await page.waitForTimeout(2000);

      // Click replay button
      const replayButton = page.getByText('← Frase anterior');
      await replayButton.click();

      // Modal should be visible
      const modalTitle = page.getByText('Frase Anterior');
      await expect(modalTitle).toBeVisible();

      // Should show "Apenas Visualização" badge
      const badge = page.getByText('Apenas Visualização');
      await expect(badge).toBeVisible();

      // Should have "Play Word" and "Play Sentence" buttons
      const playWordButton = page.getByText('Play Word');
      const playSentenceButton = page.getByText('Play Sentence');
      await expect(playWordButton).toBeVisible();
      await expect(playSentenceButton).toBeVisible();

      // Should have close button
      const closeButton = page.getByText('Voltar para o card atual');
      await expect(closeButton).toBeVisible();

      // Close modal
      await closeButton.click();

      // Modal should be closed
      await expect(modalTitle).not.toBeVisible();

      // Should still be on current card (not refetched)
      // We can verify this by checking the study container is still visible
      await expect(page.locator('[data-testid="study-container"]')).toBeVisible();
    });

    test('does not trigger POST /answer when using replay', async ({ page }) => {
      // Setup network listener to track API calls
      const answerRequests: string[] = [];

      page.on('request', (request) => {
        if (request.url().includes('/answer')) {
          answerRequests.push(request.url());
        }
      });

      // Wait for page to stabilize
      await page.waitForTimeout(2000);

      // Check if we have cards
      const hasCards = await page.locator('[data-testid="study-card"]').isVisible().catch(() => false);
      if (!hasCards) {
        test.skip(true, 'No cards available');
        return;
      }

      // Answer first card to advance
      await page.locator('[data-testid="answer-input"]').fill('test');
      await page.locator('[data-testid="answer-submit"]').click();

      // Wait for next card
      await page.waitForTimeout(2000);

      // Clear previous answer requests
      answerRequests.length = 0;

      // Click replay button
      await page.getByText('← Frase anterior').click();

      // Wait for modal to appear
      await page.waitForTimeout(500);

      // Click play audio buttons (these should not trigger /answer)
      await page.getByText('Play Word').click();
      await page.waitForTimeout(500);
      await page.getByText('Play Sentence').click();
      await page.waitForTimeout(500);

      // Close modal
      await page.getByText('Voltar para o card atual').click();
      await page.waitForTimeout(500);

      // Verify no POST /answer was made during replay
      expect(answerRequests.length).toBe(0);
    });
  });

  test.describe('Lingvist Mode', () => {
    test.beforeEach(async ({ page }) => {
      // Switch to Lingvist mode
      await page.goto('/?mode=lingvist');

      // Wait for mode switch
      await page.waitForTimeout(1000);
    });

    test('replay button works in Lingvist mode', async ({ page }) => {
      // Wait for page to stabilize
      await page.waitForTimeout(2000);

      // Check if we have cards
      const hasCards = await page.locator('text=Lingvist Mode').isVisible().catch(() => false);
      if (!hasCards) {
        test.skip(true, 'Lingvist mode not available');
        return;
      }

      // Initially, button should be disabled
      const replayButton = page.getByText('← Frase anterior');
      await expect(replayButton).toBeVisible();
      await expect(replayButton).toBeDisabled();

      // Look for gap input and fill it
      const gapInput = page.locator('input[type="text"]').first();
      const isVisible = await gapInput.isVisible().catch(() => false);

      if (!isVisible) {
        test.skip(true, 'No gap input found');
        return;
      }

      // Fill gap and wait for auto-submit or next card
      await gapInput.fill('test');
      await page.waitForTimeout(3000);

      // Now button should be enabled
      await expect(replayButton).toBeEnabled();

      // Click and verify modal opens
      await replayButton.click();

      // Modal should be visible
      const modalTitle = page.getByText('Frase Anterior');
      await expect(modalTitle).toBeVisible();

      // Close modal
      await page.getByText('Voltar para o card atual').click();

      // Modal should be closed
      await expect(modalTitle).not.toBeVisible();
    });
  });
});
