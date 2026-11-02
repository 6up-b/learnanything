---
title: "Desktop module · src/screens/reader/figures/sketch/sketchCompartment.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.figures.sketch.sketchCompartment"
language: "TypeScript"
area: "TypeScript/screens/reader/figures/sketch"
source_path: "apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchCompartment.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchCompartment.ts"
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

# `src/screens/reader/figures/sketch/sketchCompartment.ts`

Area: [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/_area|TypeScript/screens/reader/figures/sketch]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `WorkerLike`, `CompartmentInputs`, `createSketchCompartment`, `appEngineBytes` within the desktop's TypeScript/screens/reader/figures/sketch ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchCompartment.ts](../../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchCompartment.ts) |
| Source lines | 161 |
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
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/LessonScreen|src/screens/LessonScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/SketchFigure|src/screens/reader/figures/sketch/SketchFigure.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchRunner|src/screens/reader/figures/sketch/sketchRunner.ts]] → [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchCompartmentClient|src/screens/reader/figures/sketch/sketchCompartmentClient.ts]] → [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchCompartment|src/screens/reader/figures/sketch/sketchCompartment.ts]]

## Public API

- `export type WorkerLike =` — type, line 17
- `export type CompartmentInputs =` — type, line 24
- `export function createSketchCompartment(inputs: CompartmentInputs): WorkerLike` — function, line 33
- `export function appEngineBytes(url: string): ()` — function, line 151

## Internal implementation anchors

- `const doc = inputs.document ?? document` — const, line 34
- `const control = new MessageChannel()` — const, line 35
- `const engine = new MessageChannel()` — const, line 36
- `const frame = doc.createElement("iframe")` — const, line 37
- `let state: "starting" | "started" | "failed" | "ended" = "starting"` — let, line 38
- `let failure = ""` — let, line 39
- `let pending: WorkerRequest[] = []` — let, line 40
- `const handle: WorkerLike =` — const, line 42
- `function refuse(message: WorkerRequest)` — function, line 76
- `const parsed = parseWorkerRequest(message)` — const, line 77
- `const id = parsed.ok ? parsed.request.id : parsed.id` — const, line 78
- `function failWith(message: string)` — function, line 83
- `const waiting = pending` — const, line 87
- `const notice = parseFrameNotice(event.data)` — const, line 98
- `const waiting = pending` — const, line 107
- `let booted = false` — let, line 115
- `async function boot()` — function, line 116
- `const bytes = await inputs.engineBytes()` — const, line 121
- `let engineCache: Promise<ArrayBuffer> | null = null` — let, line 147
- `const shared = engineCache` — const, line 157

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchCompartmentClient|src/screens/reader/figures/sketch/sketchCompartmentClient.ts]] — import-or-re-export: `WorkerLike`, `appEngineBytes`, `createSketchCompartment`; references `WorkerLike`, `appEngineBytes`, `createSketchCompartment`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchFrameProtocol|src/screens/reader/figures/sketch/sketchFrameProtocol.ts]] — import-or-re-export; imports `SKETCH_ENGINE_MAX_BYTES`, `SKETCH_FRAME_PATH`, `SKETCH_WORKER_SOURCE_MAX_CHARS`, `parseFrameNotice`
- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchProtocol|src/screens/reader/figures/sketch/sketchProtocol.ts]] — import-or-re-export; imports `REPLY_MESSAGE_MAX`, `WorkerRequest`, `WorkerResponse`, `parseWorkerRequest`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchCompartment.test.ts](../../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchCompartment.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
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

1. Modify [apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchCompartment.ts](../../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchCompartment.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
