// Browser mode, for development and the UX walks only (scripts/ux_walk/README.md).
//
// The production config is imported unchanged; this file only swaps the
// `@tauri-apps/*` modules the frontend imports for the shims in
// browser-harness/, which call the walk bridge (scripts/ux_walk/bridge.py) over
// HTTP on 127.0.0.1. `npm run dev`, `npm run frontend:build`, `npm test` and
// the Tauri app never read this file, so their output does not change.
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { mergeConfig } from "vite";
import baseConfig from "./vite.config.mjs";

const root = dirname(fileURLToPath(import.meta.url));
const shim = (name) => resolve(root, "browser-harness", name);

// Console errors and unhandled rejections, kept for the analyst's log. The
// driver reads them after every step; the persona never sees them. Injected
// before the app's own module so an error during boot is kept too.
const CONSOLE_CAPTURE = `
(() => {
  const kept = [];
  const keep = (kind, parts) => {
    const text = parts.map((part) => {
      if (part instanceof Error) return part.stack || part.message;
      if (typeof part === "string") return part;
      try { return JSON.stringify(part); } catch { return String(part); }
    }).join(" ");
    kept.push({ kind, text: text.slice(0, 4000), at: Date.now() });
    if (kept.length > 500) kept.shift();
  };
  const original = console.error.bind(console);
  console.error = (...parts) => { keep("console.error", parts); original(...parts); };
  const warn = console.warn.bind(console);
  console.warn = (...parts) => { keep("console.warn", parts); warn(...parts); };
  window.addEventListener("error", (event) => keep("error", [event.error || event.message]));
  window.addEventListener("unhandledrejection", (event) => keep("unhandledrejection", [event.reason]));
  window.__walkConsole = { drain: () => kept.splice(0, kept.length) };
})();
`;

function walkConsoleCapture() {
  return {
    name: "learnloop-walk-console-capture",
    transformIndexHtml() {
      return [{ tag: "script", children: CONSOLE_CAPTURE, injectTo: "head-prepend" }];
    },
  };
}

export default mergeConfig(baseConfig, {
  plugins: [walkConsoleCapture()],
  resolve: {
    alias: [
      { find: /^@tauri-apps\/api\/core$/, replacement: shim("core.ts") },
      { find: /^@tauri-apps\/api\/event$/, replacement: shim("event.ts") },
      { find: /^@tauri-apps\/api\/window$/, replacement: shim("window.ts") },
      { find: /^@tauri-apps\/api\/webview$/, replacement: shim("webview.ts") },
      { find: /^@tauri-apps\/plugin-dialog$/, replacement: shim("dialog.ts") },
      { find: /^@tauri-apps\/plugin-opener$/, replacement: shim("opener.ts") },
    ],
  },
  // Walks serve the built bundle from the bridge itself. For development with
  // hot reload, run a bridge and point this dev server at it:
  //   WALK_BRIDGE_PORT=<bridge port> npx vite --config vite.browser.config.mjs
  server: {
    host: "127.0.0.1",
    port: 1421,
    strictPort: true,
    proxy: process.env.WALK_BRIDGE_PORT
      ? { "/__bridge": `http://127.0.0.1:${process.env.WALK_BRIDGE_PORT}` }
      : undefined,
  },
  build: { outDir: resolve(root, "dist-browser"), emptyOutDir: true },
});
