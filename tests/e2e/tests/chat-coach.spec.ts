import { test, expect } from '@playwright/test';

test.describe('Chat Coach - E2E', () => {
  test('starts a new profile directly in Chat Coach mode', async ({ page }) => {
    await page.goto('/?mode=chat');

    const uniqueName = `ChatCoachUser${Date.now()}`;
    await page.fill('[data-testid="profile-create-name"]', uniqueName);
    await page.click('[data-testid="profile-create-start"]');

    await expect(page.getByRole('heading', { name: 'Chat Coach' })).toBeVisible({ timeout: 15000 });
    await expect(page.getByPlaceholder('Type your message... (Enter to send, Shift+Enter for new line)')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Send' })).toBeDisabled();
    await expect(page.getByRole('heading', { name: 'Feedback' })).toBeVisible();
    await expect(page.getByText('Coach memory')).toBeVisible();
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

    const profileCard = page.locator('div[data-testid^="profile-card-"]').filter({ hasText: uniqueName });
    await expect(profileCard).toBeVisible();
    await profileCard.getByRole('button').filter({ hasText: 'Chat' }).click();

    await expect(page.getByRole('heading', { name: 'Chat Coach' })).toBeVisible({ timeout: 15000 });
    await expect(page.getByRole('button', { name: '⚙️' })).toBeVisible();
  });
});
