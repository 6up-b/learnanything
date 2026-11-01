// Reader RW5d P2: the sketch's dedicated Web Worker (spec_reader_show_me_figures_v1 §9.3).
//
// No DOM, terminable by the Reader's watchdog. Since the sketch compartment it
// is never loaded by URL: vite.config.mjs bundles this file into one script
// (the `virtual:sketch-worker-source` module), the Reader hands that text to
// the sandboxed, opaque-origin frame (sketch-frame.html), and the frame starts
// it from a blob, so the Worker inherits the frame's CSP (`connect-src 'none'`).
// It then answers only the narrow protocol (load, init, step, read) on the
// private port the boot gave it (sketchWorkerCore.ts). The program inside the
// engine reaches nothing of this Worker: it has no bindings at all.
import { startSketchWorker, type WorkerScopeLike } from "./sketchWorkerCore";

startSketchWorker(self as unknown as WorkerScopeLike);
