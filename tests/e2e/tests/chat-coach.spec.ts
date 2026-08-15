import { test, expect } from '@playwright/test';

test.describe('Chat Coach - E2E', () => {
  test('starts a new profile directly in Chat Coach mode', async ({ page }) => {
    await page.goto('/?mode=chat');

    const uniqueName = `ChatCoachUser${Date.now()}`;
    await page.fill('[data-testid="profile-create-name"]', uniqueName);
    await page.click('[data-testid="profile-create-start"]');

    await expect(page.getByRole('heading', { name: 'Chat Coach' })).toBeVisible({ timeout: 15000 });
    await expect(page.getByPlaceholder('Escreva sua mensagem…')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Enviar' })).toBeDisabled();
    await expect(page.getByRole('heading', { name: 'Feedback' })).toBeVisible();
    await expect(page.getByRole('complementary').getByText('Coach memory')).toBeVisible();

    if ((page.viewportSize()?.width ?? 0) >= 1024) {
      const conversation = page.getByTestId('chat-coach-conversation');
      const feedback = page.getByTestId('chat-coach-feedback');
      const layout = page.getByTestId('chat-coach-layout');
      const composer = page.getByTestId('chat-coach-composer');
      const conversationBox = await conversation.boundingBox();
      const feedbackBox = await feedback.boundingBox();
      const layoutBox = await layout.boundingBox();
      const composerBox = await composer.boundingBox();

      expect(layoutBox?.width).toBeGreaterThan((page.viewportSize()?.width ?? 0) - 40);
      expect(conversationBox?.width).toBeGreaterThan(feedbackBox?.width ?? 0);
      expect(composerBox?.width).toBeLessThanOrEqual(800);
      expect(feedbackBox?.width).toBeGreaterThanOrEqual(340);
      expect(await feedback.evaluate((element) => element.scrollHeight <= element.clientHeight + 1)).toBe(true);
      expect(await feedback.evaluate((element) => element.scrollWidth <= element.clientWidth + 1)).toBe(true);

      await feedback.locator('summary').filter({ hasText: 'Coach memory' }).click();
      await expect(feedback.getByText('Feedback: Portuguese')).toBeVisible();
    }
  });

  test('opens Chat Coach from an existing profile card', async ({ page }) => {
    const uniqueName = `ChatCardUser${Date.now()}`;
    const response = await page.request.post('/api/v1/users/', {
      data: {
        username: uniqueName,
        language_preference: 'pt',
        target_language: 'en',
        word_goal_rank: 100,
      },
    });
    expect(response.ok()).toBeTruthy();

    await page.goto('/');

    const profileCard = page.locator('[data-testid="profile-card"]').filter({ hasText: uniqueName });
    await expect(profileCard).toBeVisible();
    await profileCard.getByRole('button', { name: `Abrir Conversa para ${uniqueName}` }).click();

    await expect(page.getByRole('heading', { name: 'Chat Coach' })).toBeVisible({ timeout: 15000 });
    await expect(page.getByRole('button', { name: 'Abrir configurações do modelo' })).toBeVisible();
  });
});
