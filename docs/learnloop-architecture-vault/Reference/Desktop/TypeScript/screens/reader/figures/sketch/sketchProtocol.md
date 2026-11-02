---
title: "Desktop module · src/screens/reader/figures/sketch/sketchProtocol.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.figures.sketch.sketchProtocol"
language: "TypeScript"
area: "TypeScript/screens/reader/figures/sketch"
source_path: "apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchProtocol.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchProtocol.ts"
source_commit: "d2afa824ceecb2f6e35f7c6ff51d9008a644e70d"
source_commit_timestamp: "2026-11-01T14:49:03-05:00"
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

# `src/screens/reader/figures/sketch/sketchProtocol.ts`

Area: [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/_area|TypeScript/screens/reader/figures/sketch]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `SKETCH_MAX_SOURCE_BYTES`, `SKETCH_MAX_CLOCK_STEPS`, `SKETCH_MAX_PARAMETERS`, `REPLY_MESSAGE_MAX` and related exports within the desktop's TypeScript/screens/reader/figures/sketch ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchProtocol.ts](../../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchProtocol.ts) |
| Source lines | 168 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/_area|TypeScript/screens/reader/figures/sketch]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `d2afa824ceecb2f6e35f7c6ff51d9008a644e70d` |
| Commit timestamp | `2026-11-01T14:49:03-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/LessonScreen|src/screens/LessonScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/SketchFigure|src/screens/reader/figures/sketch/SketchFigure.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchRunner|src/screens/reader/figures/sketch/sketchRunner.ts]] → [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchProtocol|src/screens/reader/figures/sketch/sketchProtocol.ts]]

## Public API

- `export const SKETCH_MAX_SOURCE_BYTES = 32_768` — const, line 19
- `export const SKETCH_MAX_CLOCK_STEPS = 2_000` — const, line 21
- `export const SKETCH_MAX_PARAMETERS = 4` — const, line 23
- `export const REPLY_MESSAGE_MAX = 600` — const, line 25
- `export const SKETCH_MAX_OUTPUT_CHARS = 4 * 1024 * 1024` — const, line 28
- `export const WORKER_OPS = ["load", "init", "step", "read"] as const` — const, line 30
- `export type WorkerOp = (typeof WORKER_OPS)[number]` — type, line 31
- `export type WorkerRequest =` — type, line 32
- `export type SketchRead =` — type, line 33
- `export type SketchReadText =` — type, line 35
- `export type WorkerResponse = |` — type, line 36
- `export function parseWorkerRequest(data: unknown):` — function, line 91
- `export async function answerRequest(host: ()` — function, line 106
- `export function parseWorkerReply(data: unknown, expected: (id: number)` — function, line 135

## Internal implementation anchors

- `const PARAMETER_NAME = /^[A-Za-z][A-Za-z0-9_]` — const, line 40
- `const DIGEST = /^[0-9a-f]` — const, line 41
- `const KINDS = new Set<string>([...STATUS_NAMES, "trap", "scene", "probe", "paused"])` — const, line 42
- `const ENTRY_POINTS = ["init", "step", "view", "probes"] as const` — const, line 43
- `const isObject = (value: unknown): value is Record<string, unknown>` — const, line 45
- `const isId = (value: unknown): value is number` — const, line 47
- `const isIndex = (value: unknown): value is number` — const, line 48
- `function paramsProblem(value: unknown): string | null` — function, line 51
- `const names = Object.keys(value)` — const, line 53
- `const item = value[name]` — const, line 57
- `function argsProblem(op: WorkerOp, args: unknown[]): string | null` — function, line 63
- `const seed = args[1]` — const, line 71
- `const id = isId(data.id) ? data.id : 0` — const, line 93
- `const op = data.op as WorkerOp` — const, line 99
- `const problem = argsProblem(op, data.args)` — const, line 100
- `const parsed = parseWorkerRequest(data)` — const, line 107
- `const sketch = await host()` — const, line 111
- `const params = args[0] as Record<string, number>` — const, line 112
- `const read: SketchReadText =` — const, line 123
- `const error = caught instanceof SketchRunError ?` — const, line 126
- `const id = data.id` — const, line 138
- `const op = expected(id)` — const, line 139
- `const malformed =` — const, line 141
- `const kind = typeof data.error.kind === "string" && KINDS.has(data.error.kind) ? (data.error.kind as SketchErrorKind) : "error"` — const, line 144
- `const message = typeof data.error.message === "string" ? data.error.message.slice(0, REPLY_MESSAGE_MAX) : "error"` — const, line 145
- `const result = data.result` — const, line 149
- `const read: SketchRead =` — const, line 163

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchCompartment|src/screens/reader/figures/sketch/sketchCompartment.ts]] — import-or-re-export: `REPLY_MESSAGE_MAX`, `WorkerRequest`, `WorkerResponse`, `parseWorkerRequest`; references `REPLY_MESSAGE_MAX`, `WorkerRequest`, `WorkerResponse`, `parseWorkerRequest`
- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchRunner|src/screens/reader/figures/sketch/sketchRunner.ts]] — import-or-re-export: `SketchRead`, `SketchReadText`, `WorkerOp`, `WorkerRequest`, `WorkerResponse`, `parseWorkerReply`; references `SketchRead`, `WorkerOp`, `WorkerRequest`, `WorkerResponse`, `parseWorkerReply`
- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchWorkerCore|src/screens/reader/figures/sketch/sketchWorkerCore.ts]] — import-or-re-export: `answerRequest`; references `answerRequest`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchEngine|src/screens/reader/figures/sketch/sketchEngine.ts]] — import-or-re-export; imports `STATUS_NAMES`, `SketchEngineHost`, `SketchErrorKind`, `SketchRunError`, `sceneDigest`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchProtocol.test.ts](../../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchProtocol.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_sketch_verify.py](../../../../../../../../../tests/test_sketch_verify.py) — cross-boundary name contract: references uniquely owned exported name `SKETCH_MAX_SOURCE_BYTES`; it does **not** directly execute this source module.
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

1. Modify [apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchProtocol.ts](../../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchProtocol.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
