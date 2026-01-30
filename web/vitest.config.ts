import path from "node:path";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  css: {
    // Vitest/Vite loads PostCSS config by default, but our Next.js Tailwind config
    // uses plugin name strings which Vite's PostCSS loader does not accept.
    // Tests in this repo don't need PostCSS processing, so we disable it here.
    postcss: {
      plugins: [],
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
  },
});
