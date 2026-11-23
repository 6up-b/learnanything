// The desks' visual harness (docs/specs/spec_reader_workbench_v2.md §18.3): the browser mode's shims
// (vite.browser.config.mjs) with one change, `@tauri-apps/api/core` answered from the synthetic
// workspace instead of a sidecar, and one page, desk-harness.html. `npm run dev`, the production
// build, `npm test` and the Tauri app never read this file.
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { mergeConfig } from "vite";
import baseConfig from "./vite.config.mjs";

const root = dirname(fileURLToPath(import.meta.url));
const shim = (name) => resolve(root, "browser-harness", name);

export default mergeConfig(baseConfig, {
  resolve: {
    alias: [
      { find: /^@tauri-apps\/api\/core$/, replacement: resolve(root, "src/fixtures/desks/fakeCore.ts") },
      { find: /^@tauri-apps\/api\/event$/, replacement: shim("event.ts") },
      { find: /^@tauri-apps\/api\/window$/, replacement: shim("window.ts") },
      { find: /^@tauri-apps\/api\/webview$/, replacement: shim("webview.ts") },
      { find: /^@tauri-apps\/plugin-dialog$/, replacement: shim("dialog.ts") },
      { find: /^@tauri-apps\/plugin-opener$/, replacement: shim("opener.ts") },
    ],
  },
  build: {
    outDir: resolve(root, "dist-desk-harness"),
    emptyOutDir: true,
    rollupOptions: { input: { deskHarness: resolve(root, "desk-harness.html") } },
  },
});
