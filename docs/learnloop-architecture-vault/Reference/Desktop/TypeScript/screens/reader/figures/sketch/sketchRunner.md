---
title: "Desktop module · src/screens/reader/figures/sketch/sketchRunner.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.figures.sketch.sketchRunner"
language: "TypeScript"
area: "TypeScript/screens/reader/figures/sketch"
source_path: "apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchRunner.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchRunner.ts"
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

# `src/screens/reader/figures/sketch/sketchRunner.ts`

Area: [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/_area|TypeScript/screens/reader/figures/sketch]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `SketchRunner`, `SketchRunnerFactory`, `hostRunner`, `portRunner` and related exports within the desktop's TypeScript/screens/reader/figures/sketch ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchRunner.ts](../../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchRunner.ts) |
| Source lines | 146 |
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
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/LessonScreen|src/screens/LessonScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/SketchFigure|src/screens/reader/figures/sketch/SketchFigure.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchRunner|src/screens/reader/figures/sketch/sketchRunner.ts]]

## Public API

- `export interface SketchRunner` — interface, line 21
- `export type SketchRunnerFactory = ()` — type, line 29
- `export function hostRunner(host: SketchEngineHost): SketchRunner` — function, line 32
- `export function portRunner(worker:` — function, line 53
- `export const WATCHDOG_MS = SKETCH_FRAME_MS * SKETCH_WATCHDOG_FRAMES` — const, line 90
- `export function withWatchdog(runner: SketchRunner, ms: number = WATCHDOG_MS, onPause?: ()` — function, line 94
- `export function workerRunner(): SketchRunner` — function, line 124
- `export const SketchRunnerContext = createContext<SketchRunnerFactory>(workerRunner)` — const, line 146

## Internal implementation anchors

- `const wrap = <T,>(run: ()` — const, line 33
- `let next = 1` — let, line 54
- `const waiting = new Map<number,` — const, line 55
- `let ended = false` — let, line 56
- `const reply = parseWorkerReply(event.data as unknown, (id)` — const, line 60
- `const entry = waiting.get(reply.id)!` — const, line 62
- `const send = <T,>(op: WorkerOp, args: unknown[]): Promise<T>` — const, line 67
- `const id = next++` — const, line 69
- `let stopped = false` — let, line 95
- `const guard = <T,>(call: ()` — const, line 96
- `const timer = setTimeout(()` — const, line 99
- `let real: SketchRunner | null = null` — let, line 125
- `let disposed = false` — let, line 126
- `const ready = import("./sketchCompartmentClient").then((client)` — const, line 127
- `const via = <T,>(call: (runner: SketchRunner)` — const, line 132

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/SketchFigure|src/screens/reader/figures/sketch/SketchFigure.tsx]] — import-or-re-export: `SketchRunner`, `SketchRunnerContext`, `withWatchdog`; references `SketchRunner`, `SketchRunnerContext`, `withWatchdog`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchCompartmentClient|src/screens/reader/figures/sketch/sketchCompartmentClient.ts]] — dynamic import
- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchEngine|src/screens/reader/figures/sketch/sketchEngine.ts]] — import-or-re-export; imports `EntryPoints`, `Params`, `SKETCH_FRAME_MS`, `SKETCH_WATCHDOG_FRAMES`, `SketchEngineHost`, `SketchRunError`, `sceneDigest`
- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchProtocol|src/screens/reader/figures/sketch/sketchProtocol.ts]] — import-or-re-export; imports `SketchRead`, `SketchReadText`, `WorkerOp`, `WorkerRequest`, `WorkerResponse`, `parseWorkerReply`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchSandboxReview.test.tsx](../../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchSandboxReview.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchProtocol.test.ts](../../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchProtocol.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchCompartment.test.ts](../../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchCompartment.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/figures/sketch/SketchFigure.test.tsx](../../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sketch/SketchFigure.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

1. Modify [apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchRunner.ts](../../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchRunner.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
