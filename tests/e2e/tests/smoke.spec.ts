import { test, expect } from '@playwright/test';

test.describe('Smoke', () => {
  test('loads the profile selection screen', async ({ page }) => {
    await page.goto('/');

    await expect(page.locator('h1')).toContainText('WordBridge Coach');
    await expect(page.locator('[data-testid="profile-create-name"]')).toBeVisible();
    await expect(page.locator('[data-testid="profile-create-start"]')).toBeVisible();
  });

  test('creates a profile and reaches the study shell', async ({ page }) => {
    await page.goto('/');

    const uniqueName = `SmokeUser${Date.now()}`;
    await page.fill('[data-testid="profile-create-name"]', uniqueName);
    await page.click('[data-testid="profile-create-start"]');

    await Promise.race([
      page.waitForSelector('[data-testid="study-container"]', { timeout: 15000 }),
      page.waitForSelector('text=No cards available', { timeout: 15000 }),
    ]);

    await expect(page.locator('[data-testid="profile-create-name"]')).not.toBeVisible();
  });
});
