import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { build } from "esbuild";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const root = dirname(fileURLToPath(import.meta.url));

// Reader RW5d P2, the sketch compartment: the sketch Worker as one script's
// text. The Reader hands it to the sandboxed frame (sketch-frame.html), which
// starts it from a blob so the Worker inherits the frame's CSP; a Worker
// loaded by URL would get no policy at all (the G-SM14 probe). Bundled here,
// in dev and in builds alike, as an IIFE with nothing left to import.
const SKETCH_WORKER_ID = "virtual:sketch-worker-source";
const SKETCH_WORKER_ENTRY = resolve(root, "src/screens/reader/figures/sketch/sketch.worker.ts");

function sketchWorkerSource() {
  return {
    name: "learnloop-sketch-worker-source",
    resolveId(source) {
      return source === SKETCH_WORKER_ID ? `\0${SKETCH_WORKER_ID}` : null;
    },
    async load(id) {
      if (id !== `\0${SKETCH_WORKER_ID}`) return null;
      const result = await build({
        entryPoints: [SKETCH_WORKER_ENTRY],
        bundle: true,
        format: "iife",
        platform: "browser",
        target: "es2020",
        minify: true,
        write: false,
        metafile: true,
        logLevel: "silent",
      });
      for (const input of Object.keys(result.metafile.inputs)) this.addWatchFile(resolve(root, input));
      return `export default ${JSON.stringify(result.outputFiles[0].text)};`;
    },
  };
}

export default defineConfig({
  plugins: [react(), sketchWorkerSource()],
  clearScreen: false,
  server: {
    port: 1420,
    strictPort: true,
    watch: {
      ignored: ["**/src-tauri/**"]
    }
  },
  build: {
    rollupOptions: {
      // The sketch compartment's frame document is a page of its own (Tauri serves it with the app's CSP
      // header, which the page's frame-src names, and it carries its own stricter policy).
      input: { index: resolve(root, "index.html"), sketchFrame: resolve(root, "sketch-frame.html") },
    },
  },
  envPrefix: ["VITE_", "TAURI_"]
});
