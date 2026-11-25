/// <reference types="vitest/config" />
import path from "path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    host: true,
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/test-setup.ts"],
    // tests/e2e/ holds Playwright specs, not Vitest ones — without this
    // exclude, Vitest tries to collect them and crashes on test.describe().
    exclude: ["node_modules/**", "tests/e2e/**"],
    // No unit tests exist yet (see project TODO) — don't fail CI on that
    // alone. Remove once real specs land, so an empty run starts failing.
    passWithNoTests: true,
    coverage: {
      provider: "v8",
      reporter: ["text", "html"],
      exclude: ["node_modules/", "src/test-setup.ts", "tests/e2e/"],
      thresholds: {
        lines: 70,
        functions: 70,
        branches: 70,
        statements: 70,
      },
    },
  },
});
