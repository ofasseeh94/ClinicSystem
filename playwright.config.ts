import { defineConfig } from '@playwright/test';
export default defineConfig({ testDir: './tests/e2e', timeout: 45000, workers: 1,
  use: { baseURL: process.env.E2E_BASE_URL ?? 'http://127.0.0.1:5173', headless: true },
  reporter: 'list', outputDir: 'test-results',
});
