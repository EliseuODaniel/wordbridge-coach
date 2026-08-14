import { test, expect } from '@playwright/test';

test.describe('Training mode switching - E2E', () => {
  test('switches between Spec4 and Lingvist without leaving the session shell', async ({ page }) => {
    await page.goto('/');

    const uniqueName = `ModeSwitchUser${Date.now()}`;
    await page.fill('[data-testid="profile-create-name"]', uniqueName);
    await page.click('[data-testid="profile-goal-100"]');
    await page.click('[data-testid="profile-create-start"]');

    await expect(page.locator('[data-testid="study-container"]')).toBeVisible({ timeout: 15000 });
    await expect(page.getByRole('heading', { name: 'Revisão guiada' })).toBeVisible();

    await page.locator('[data-testid="mode-picker-lingvist"]').click();
    await expect(page.getByRole('heading', { name: 'Cloze adaptativo' })).toBeVisible({ timeout: 15000 });
    await expect(page.locator('[data-testid="lingvist-inline-input"]')).toBeVisible();

    await page.locator('[data-testid="mode-picker-spec4"]').click();
    await expect(page.locator('[data-testid="study-container"]')).toBeVisible({ timeout: 15000 });
    await expect(page.getByRole('heading', { name: 'Revisão guiada' })).toBeVisible();
    await expect(page.locator('[data-testid="lingvist-inline-input"]')).not.toBeVisible();
  });
});
