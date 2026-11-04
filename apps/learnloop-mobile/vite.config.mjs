import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const root = dirname(fileURLToPath(import.meta.url));

// The phone's own Vite app (spec_mobile_tailnet_v1 §3.4, D4). It imports the desktop's DTO
// types, query cache and render components through `@desktop`, and has its own HTTP call().
// The host serves this build at /app/ (a gitignored directory inside the package), so `base`
// is that path, and every module the shared files import resolves from this app's own
// node_modules (`dedupe`): one React, and no need for the desktop's npm install.
export default defineConfig({
  base: "/app/",
  plugins: [react()],
  clearScreen: false,
  resolve: {
    alias: { "@desktop": resolve(root, "../learnloop-tauri/src") },
    dedupe: ["react", "react-dom", "react-markdown", "rehype-katex", "remark-gfm", "remark-math", "katex"],
  },
  server: { fs: { allow: [resolve(root, "..")] } },
  build: {
    outDir: resolve(root, "../../src/learnloop_mobile/static/app"),
    emptyOutDir: true,
    // The host's CSP has no inline-script allowance, and a phone is a phone.
    assetsInlineLimit: 0,
    target: "es2020",
  },
});
