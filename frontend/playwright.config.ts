import { defineConfig } from '@playwright/test'

// end-to-end tests in Chrome against the real backend; both servers are started if they aren't running
export default defineConfig({
  testDir: './e2e',
  testMatch: '**/*.e2e.ts', // not *.test.ts, so Vitest doesn't pick these up
  timeout: 30_000,
  use: {
    baseURL: 'http://localhost:5173',
    channel: 'chrome', // the installed Chrome, so nothing is downloaded
    viewport: { width: 1400, height: 900 },
  },
  webServer: [
    {
      command: 'uv run uvicorn metro.api.main:app --port 8000',
      cwd: '../backend',
      url: 'http://localhost:8000/api/network',
      reuseExistingServer: true,
    },
    {
      command: 'npm run dev',
      url: 'http://localhost:5173',
      reuseExistingServer: true,
    },
  ],
})
