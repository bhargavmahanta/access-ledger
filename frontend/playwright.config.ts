import { defineConfig } from '@playwright/test';
export default defineConfig({ testDir: './tests', workers: 1, timeout: 90000, expect: { timeout: 10000 }, use: { baseURL: 'http://127.0.0.1:5174', screenshot: 'only-on-failure', trace: 'retain-on-failure' }, webServer: [
 { command: 'PGDATABASE=accessledger_test_browser ../.venv/bin/uvicorn backend.app.main:app --app-dir .. --host 127.0.0.1 --port 8001', url: 'http://127.0.0.1:8001/health', reuseExistingServer: false },
 { command: 'API_PROXY=http://127.0.0.1:8001 npm run dev -- --port 5174 --strictPort', url: 'http://127.0.0.1:5174', reuseExistingServer: false }
] });
