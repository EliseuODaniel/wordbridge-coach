import { test, expect } from '@playwright/test';

test('Debug user creation', async ({ page }) => {
  // Monitor API calls
  const apiCalls: any[] = [];
  page.on('request', request => {
    if (request.url().includes('/api/')) {
      apiCalls.push({
        url: request.url(),
        method: request.method()
      });
    }
  });

  // Monitor API responses
  const apiResponses: any[] = [];
  page.on('response', response => {
    if (response.url().includes('/api/')) {
      response.text().then(text => {
        try {
          apiResponses.push({
            url: response.url(),
            status: response.status(),
            data: JSON.parse(text)
          });
        } catch (e) {
          apiResponses.push({
            url: response.url(),
            status: response.status(),
            data: text
          });
        }
      });
    }
  });

  // Go to site
  await page.goto('/');

  // Fill out profile form with unique name
  const uniqueName = `DebugUser${Date.now()}`;
  await page.fill('[data-testid="profile-create-name"]', uniqueName);

  // Submit form
  await page.click('[data-testid="profile-create-start"]');

  // Wait for any loading state
  await page.waitForTimeout(5000);

  // Log API calls and responses
  console.log('API calls made:');
  apiCalls.forEach(call => {
    console.log(`${call.method} ${call.url}`);
  });

  console.log('API responses:');
  apiResponses.forEach(response => {
    console.log(`${response.status} ${response.url}`);
    if (response.data.id) {
      console.log(`  Created user ID: ${response.data.id}`);
    }
    if (response.data.username) {
      console.log(`  Username: ${response.data.username}`);
    }
  });

  // Check localStorage for user data
  const localStorage = await page.evaluate(() => {
    return {
      keys: Object.keys(localStorage),
      data: Object.keys(localStorage).reduce((acc, key) => {
        acc[key] = localStorage.getItem(key);
        return acc;
      }, {} as any)
    };
  });
  console.log('LocalStorage:', localStorage);

  // Check page content
  const bodyText = await page.locator('body').textContent();
  console.log('Page body text snippet:', bodyText?.substring(0, 500));

  // Look for any error messages
  const hasError = await page.locator('text=error, Error, ERROR').count();
  if (hasError > 0) {
    console.log('Found error messages on page');
  }

  // Look for study card
  const hasStudyCard = await page.locator('[data-testid="study-card"]').count();
  console.log('Study card count:', hasStudyCard);

  // Look for "No cards available" message
  const hasNoCardsMessage = await page.locator('text=No cards available').count();
  console.log('No cards message count:', hasNoCardsMessage);

  // Look for profile selection
  const hasProfileSelection = await page.locator('text=Choose Your Profile').count();
  console.log('Profile selection count:', hasProfileSelection);
});