---
title: "Desktop module · src/screens/reader/figures/sketch/sketchWorkerCore.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.figures.sketch.sketchWorkerCore"
language: "TypeScript"
area: "TypeScript/screens/reader/figures/sketch"
source_path: "apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchWorkerCore.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchWorkerCore.ts"
source_commit: "d2afa824ceecb2f6e35f7c6ff51d9008a644e70d"
source_commit_timestamp: "2026-11-01T14:49:03-05:00"
source_worktree_state: "clean"
activation_kind: "bundled worker entry"
activation_evidence: "vite.config.mjs bundles src/screens/reader/figures/sketch/sketch.worker.ts (and what it imports) into the `virtual:sketch-worker-source` module, which sketchCompartmentClient.ts imports; the sketch compartment's frame starts it as a blob Worker."
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/reference/module"
  - "learnloop/desktop"
  - "learnloop/desktop/typescript"
  - "refactor/active"
---

# `src/screens/reader/figures/sketch/sketchWorkerCore.ts`

Area: [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/_area|TypeScript/screens/reader/figures/sketch]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `WorkerScopeLike`, `EngineFactory`, `startSketchWorker` within the desktop's TypeScript/screens/reader/figures/sketch ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchWorkerCore.ts](../../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchWorkerCore.ts) |
| Source lines | 44 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/_area|TypeScript/screens/reader/figures/sketch]] |
| Refactor status | `ACTIVE` |
| Activation kind | `bundled worker entry` |
| Worktree state | `clean` |
| Source commit | `d2afa824ceecb2f6e35f7c6ff51d9008a644e70d` |
| Commit timestamp | `2026-11-01T14:49:03-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> vite.config.mjs bundles src/screens/reader/figures/sketch/sketch.worker.ts (and what it imports) into the `virtual:sketch-worker-source` module, which sketchCompartmentClient.ts imports; the sketch compartment's frame starts it as a blob Worker.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketch.worker|src/screens/reader/figures/sketch/sketch.worker.ts]] → [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchWorkerCore|src/screens/reader/figures/sketch/sketchWorkerCore.ts]]

## Public API

- `export type WorkerScopeLike =` — type, line 15
- `export type EngineFactory = (bytes: Uint8Array)` — type, line 20
- `export function startSketchWorker(scope: WorkerScopeLike, create: EngineFactory = (bytes)` — function, line 23

## Internal implementation anchors

- `const boot = parseWorkerBoot(event.data, event.ports ?? [])` — const, line 25
- `const engine = create(new Uint8Array(boot.engine)).then((created)` — const, line 29

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketch.worker|src/screens/reader/figures/sketch/sketch.worker.ts]] — import-or-re-export: `WorkerScopeLike`, `startSketchWorker`; references `WorkerScopeLike`, `startSketchWorker`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchEngine|src/screens/reader/figures/sketch/sketchEngine.ts]] — import-or-re-export; imports `SketchEngineHost`
- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchFrameProtocol|src/screens/reader/figures/sketch/sketchFrameProtocol.ts]] — import-or-re-export; imports `FRAME_MESSAGE_MAX`, `parseWorkerBoot`, `stripNetwork`
- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchProtocol|src/screens/reader/figures/sketch/sketchProtocol.ts]] — import-or-re-export; imports `answerRequest`

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

1. Modify [apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchWorkerCore.ts](../../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchWorkerCore.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
