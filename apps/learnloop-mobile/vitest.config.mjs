import { mergeConfig } from "vite";
import { defineConfig } from "vitest/config";
import viteConfig from "./vite.config.mjs";

export default mergeConfig(viteConfig, defineConfig({
  test: { environment: "jsdom", environmentOptions: { jsdom: { url: "https://desktop.tail.ts.net/app/" } }, include: ["src/**/*.test.{ts,tsx}", "public/**/*.test.ts"], clearMocks: true, setupFiles: ["src/test/setup.ts"] },
}));
