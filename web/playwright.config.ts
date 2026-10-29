import { defineConfig } from "@playwright/test"
export default defineConfig({
  testDir: "./e2e",
  timeout: 30000,
  fullyParallel: false,
  workers: 1,
  use: { channel: "chrome", headless: true, trace: "retain-on-failure" },
  projects: [
    {
      name: "desktop-light",
      use: { viewport: { width: 1440, height: 1000 }, colorScheme: "light" },
    },
    {
      name: "desktop-dark",
      use: { viewport: { width: 1440, height: 1000 }, colorScheme: "dark" },
    },
    {
      name: "small-window",
      use: { viewport: { width: 390, height: 844 }, colorScheme: "light" },
    },
  ],
})
