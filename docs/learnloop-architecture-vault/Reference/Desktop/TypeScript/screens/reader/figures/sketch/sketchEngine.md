---
title: "Desktop module · src/screens/reader/figures/sketch/sketchEngine.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.figures.sketch.sketchEngine"
language: "TypeScript"
area: "TypeScript/screens/reader/figures/sketch"
source_path: "apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchEngine.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchEngine.ts"
source_commit: "0789bfcbea576a16363b70c092fc6fdc7c47cfea"
source_commit_timestamp: "2026-10-31T19:50:29-04:00"
source_worktree_state: "clean"
activation_kind: "entry-reachable build graph"
activation_evidence: "A static TypeScript import path reaches this file from the Vite entry src/main.tsx."
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/reference/module"
  - "learnloop/desktop"
  - "learnloop/desktop/typescript"
  - "refactor/active"
---

# `src/screens/reader/figures/sketch/sketchEngine.ts`

Area: [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/_area|TypeScript/screens/reader/figures/sketch]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `ENGINE_SHA256`, `SKETCH_FRAME_MS`, `SKETCH_WATCHDOG_FRAMES`, `PLAY_TICKS` and related exports within the desktop's TypeScript/screens/reader/figures/sketch ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchEngine.ts](../../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchEngine.ts) |
| Source lines | 290 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/_area|TypeScript/screens/reader/figures/sketch]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `0789bfcbea576a16363b70c092fc6fdc7c47cfea` |
| Commit timestamp | `2026-10-31T19:50:29-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/SketchFigure|src/screens/reader/figures/sketch/SketchFigure.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchEngine|src/screens/reader/figures/sketch/sketchEngine.ts]]

## Public API

- `export const ENGINE_SHA256 = "7fc7671506ec276c1c4e338afafb86b0d1ff3b397f901813b62715d7e274cbfe"` — const, line 15
- `export const SKETCH_FRAME_MS = 16` — const, line 18
- `export const SKETCH_WATCHDOG_FRAMES = 30` — const, line 19
- `export const PLAY_TICKS = 100` — const, line 22
- `export const TESTED_DIGEST_HEX = 32` — const, line 24
- `export const SKETCH_MEMORY_BYTES = 67_108_864` — const, line 26
- `export const SKETCH_FUEL_PER_CALL = 16` — const, line 27
- `export const SKETCH_SERIALIZE_TICKS = 48` — const, line 28
- `export const STATUS_NAMES = ["ok", "error", "work_cap", "memory_cap", "stack", "no_program", "output", "input"] as const` — const, line 30
- `export type SketchErrorKind = (typeof STATUS_NAMES)[number] | "trap" | "scene" | "probe" | "paused"` — type, line 31
- `export class SketchRunError extends Error` — class, line 44
- `export type Digest = (bytes: Uint8Array)` — type, line 52
- `export function sha256Hex(bytes: Uint8Array): string` — function, line 66
- `export function sceneDigest(sceneText: string, probesText: string): string` — function, line 99
- `export async function webDigest(bytes: Uint8Array): Promise<string>` — function, line 104
- `export type EntryPoints =` — type, line 126
- `export function canonicalJson(value: unknown): string` — function, line 130
- `export type Params = Record<string, number>` — type, line 133
- `export class SketchEngineHost` — class, line 136

## Internal implementation anchors

- `const STDERR_KEEP = 4096` — const, line 33
- `const EBADF = 8` — const, line 34
- `const ENOSYS = 52` — const, line 35
- `const ALLOWED_IMPORTS = new Set([ "wasi_snapshot_preview1.clock_time_get", "wasi_snapshot_preview1.fd_close", "wasi_snapshot_preview1.fd_fdstat_get", "wasi_snapshot_preview1.fd_seek", "wasi_snapshot_preview1.fd_write", ])` — const, line 36
- `const K256 = new Uint32Array([` — const, line 54
- `const length = bytes.length` — const, line 67
- `const padded = new Uint8Array(((length + 9 + 63) >> 6) << 6)` — const, line 68
- `const view = new DataView(padded.buffer)` — const, line 71
- `const h = new Uint32Array([0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19])` — const, line 74
- `const w = new Uint32Array(64)` — const, line 75
- `const rotr = (x: number, n: number)` — const, line 76
- `const s0 = rotr(w[i - 15], 7) ^ rotr(w[i - 15], 18) ^ (w[i - 15] >>> 3)` — const, line 80
- `const s1 = rotr(w[i - 2], 17) ^ rotr(w[i - 2], 19) ^ (w[i - 2] >>> 10)` — const, line 81
- `const t1 = (hh + (rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25)) + ((e & f) ^ (~e & g)) + K256[i] + w[i]) >>> 0` — const, line 86
- `const t2 = ((rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22)) + ((a & b) ^ (a & c) ^ (b & c))) >>> 0` — const, line 87
- `const subtle = (globalThis as` — const, line 105
- `const hash = await subtle.digest("SHA-256", bytes as unknown as BufferSource)` — const, line 107
- `type Exports =` — type, line 111
- `const expected = options.expected ?? ENGINE_SHA256` — const, line 153
- `const digest = await (options.digest ?? webDigest)(bytes)` — const, line 154
- `const module = await WebAssembly.compile(bytes as unknown as BufferSource)` — const, line 158
- `let host: SketchEngineHost | null = null` — let, line 164
- `let memory: WebAssembly.Memory | null = null` — let, line 165
- `const shim =` — const, line 166
- `const wasi =` — const, line 171
- `const view = new DataView(memory.buffer)` — const, line 178
- `let total = 0` — let, line 179
- `const pointer = view.getUint32(iovs + 8 * index, true)` — const, line 181
- `const length = view.getUint32(iovs + 8 * index + 4, true)` — const, line 182
- `const room = STDERR_KEEP - host.stderr.length` — const, line 184
- `const instance = await WebAssembly.instantiate(module,` — const, line 193
- `const message = caught instanceof Error ? caught.message : String(caught)` — const, line 205
- `const bytes = this.encoder.encode(text)` — const, line 211
- `const pointer = this.call(()` — const, line 212
- `const pointer = this.exports.sk_output_ptr()` — const, line 219
- `const length = this.exports.sk_output_len()` — const, line 220
- `const text = this.output()` — const, line 225
- `const length = this.write(code)` — const, line 235
- `const found = JSON.parse(this.run(this.call(()` — const, line 236
- `const code = this.write(this.code)` — const, line 246
- `const length = this.write(canonicalJson(params))` — const, line 249
- `const length = this.write(canonicalJson(` — const, line 254
- `const length = this.write(canonicalJson(params))` — const, line 259
- `const length = this.write(canonicalJson(params))` — const, line 264
- `const sceneText = this.viewText(params, index)` — const, line 270

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/SketchFigure|src/screens/reader/figures/sketch/SketchFigure.tsx]] — import-or-re-export: `Params`, `SketchRunError`; references `Params`, `SketchRunError`
- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/engineForTests|src/screens/reader/figures/sketch/engineForTests.ts]] — import-or-re-export: `SketchEngineHost`; references `SketchEngineHost`
- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchProtocol|src/screens/reader/figures/sketch/sketchProtocol.ts]] — import-or-re-export: `STATUS_NAMES`, `SketchEngineHost`, `SketchErrorKind`, `SketchRunError`, `sceneDigest`; references `STATUS_NAMES`, `SketchEngineHost`, `SketchErrorKind`, `SketchRunError`, `sceneDigest`
- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchRunner|src/screens/reader/figures/sketch/sketchRunner.ts]] — import-or-re-export: `EntryPoints`, `Params`, `SKETCH_FRAME_MS`, `SKETCH_WATCHDOG_FRAMES`, `SketchEngineHost`, `SketchRunError`, `sceneDigest`; references `EntryPoints`, `Params`, `SKETCH_FRAME_MS`, `SKETCH_WATCHDOG_FRAMES`, `SketchEngineHost`, `SketchRunError`, `sceneDigest`
- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchScene (ts)|src/screens/reader/figures/sketch/sketchScene.ts]] — import-or-re-export: `PLAY_TICKS`; references `PLAY_TICKS`
- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchWorkerCore|src/screens/reader/figures/sketch/sketchWorkerCore.ts]] — import-or-re-export: `SketchEngineHost`; references `SketchEngineHost`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchSandboxReview.test.tsx](../../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchSandboxReview.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchProtocol.test.ts](../../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchProtocol.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchParity.test.ts](../../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchParity.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchCompartment.test.ts](../../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchCompartment.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/figures/sketch/SketchFigure.test.tsx](../../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sketch/SketchFigure.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_sketch_engine.py](../../../../../../../../../tests/test_sketch_engine.py) — cross-boundary name contract: references uniquely owned exported names `ENGINE_SHA256`, `SKETCH_FUEL_PER_CALL`, `SKETCH_MEMORY_BYTES`, `SKETCH_SERIALIZE_TICKS`; it does **not** directly execute this source module.
- [tests/test_sketch_hostile.py](../../../../../../../../../tests/test_sketch_hostile.py) — cross-boundary name contract: references uniquely owned exported name `SketchRunError`; it does **not** directly execute this source module.
- [tests/test_sketch_parity.py](../../../../../../../../../tests/test_sketch_parity.py) — cross-boundary name contract: references uniquely owned exported name `ENGINE_SHA256`; it does **not** directly execute this source module.
- [tests/test_sidecar_reader.py](../../../../../../../../../tests/test_sidecar_reader.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_reader_pdf_view.py](../../../../../../../../../tests/test_sidecar_reader_pdf_view.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_render_views.py](../../../../../../../../../tests/test_reader_render_views.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_requests.py](../../../../../../../../../tests/test_reader_requests.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchEngine.ts](../../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchEngine.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
