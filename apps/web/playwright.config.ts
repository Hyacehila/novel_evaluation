import { defineConfig } from "@playwright/test";

const providerMode = process.env.NOVEL_EVAL_E2E_PROVIDER_MODE ?? "deterministic";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  timeout: 300_000,
  retries: process.env.CI ? 2 : 0,
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:13000",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  webServer: [
    {
      command: `node ./scripts/start-e2e-api.cjs`,
      url: "http://127.0.0.1:18000/api/provider-status",
      reuseExistingServer: false,
      timeout: 300_000,
      env: {
        NOVEL_EVAL_E2E_PROVIDER_MODE: providerMode,
        NOVEL_EVAL_DEEPSEEK_API_KEY: process.env.NOVEL_EVAL_DEEPSEEK_API_KEY ?? "",
      },
    },
    {
      command: "node ./scripts/start-e2e-web.cjs",
      url: "http://127.0.0.1:13000",
      reuseExistingServer: false,
      timeout: 300_000,
    },
  ],
});
