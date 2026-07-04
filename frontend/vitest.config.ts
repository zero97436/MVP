import { defineConfig } from "vitest/config";

// Vitest : tests unitaires dans src/ uniquement. Les tests E2E (Playwright)
// vivent dans e2e/ et sont exécutés via `npm run e2e`.
export default defineConfig({
  test: {
    include: ["src/**/*.test.{ts,tsx}"],
    exclude: ["e2e/**", "node_modules/**"],
  },
});
