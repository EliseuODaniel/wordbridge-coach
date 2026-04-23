import { request, FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  console.log('🚀 Setting up WordBridge Coach E2E test environment...');

  // Wait for services to be ready
  const baseURL = config.webServer?.baseURL || process.env.BASE_URL || 'http://localhost:3007';
  const apiURL = baseURL.replace('3007', '8000');

  console.log(`📡 Checking API health at ${apiURL}/health...`);

  let attempts = 0;
  const maxAttempts = 30;

  while (attempts < maxAttempts) {
    try {
      const apiClient = await request.newContext();
      const response = await apiClient.get(`${apiURL}/health`);

      if (response.status() === 200) {
        console.log('✅ API is healthy and ready');
        await apiClient.dispose();
        break;
      }

      await apiClient.dispose();
    } catch (error) {
      attempts++;
      console.log(`⏳ Waiting for API... attempt ${attempts}/${maxAttempts}`);
      await new Promise(resolve => setTimeout(resolve, 2000));
    }

    if (attempts >= maxAttempts) {
      throw new Error('❌ API not ready after maximum attempts');
    }
  }

  console.log('🌐 Checking frontend health...');
  attempts = 0;

  while (attempts < maxAttempts) {
    try {
      const webClient = await request.newContext();
      const response = await webClient.get(baseURL);

      if (response.status() === 200) {
        console.log('✅ Frontend is healthy and ready');
        await webClient.dispose();
        break;
      }

      await webClient.dispose();
    } catch (error) {
      attempts++;
      console.log(`⏳ Waiting for frontend... attempt ${attempts}/${maxAttempts}`);
      await new Promise(resolve => setTimeout(resolve, 2000));
    }

    if (attempts >= maxAttempts) {
      throw new Error('❌ Frontend not ready after maximum attempts');
    }
  }

  console.log('🎯 E2E test environment ready!');
}

export default globalSetup;
