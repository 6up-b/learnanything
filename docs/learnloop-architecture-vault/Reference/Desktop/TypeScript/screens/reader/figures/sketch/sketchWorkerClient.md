---
title: "Desktop module · src/screens/reader/figures/sketch/sketchWorkerClient.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.figures.sketch.sketchWorkerClient"
language: "TypeScript"
area: "TypeScript/screens/reader/figures/sketch"
source_path: "apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchWorkerClient.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchWorkerClient.ts"
source_commit: "8427228c2d6ecbf8bf612e57a5e1d5d0c0d7fb6b"
source_commit_timestamp: "2026-10-31T14:41:14-04:00"
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

# `src/screens/reader/figures/sketch/sketchWorkerClient.ts`

Area: [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/_area|TypeScript/screens/reader/figures/sketch]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `createSketchWorker` within the desktop's TypeScript/screens/reader/figures/sketch ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchWorkerClient.ts](../../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchWorkerClient.ts) |
| Source lines | 11 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/_area|TypeScript/screens/reader/figures/sketch]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `8427228c2d6ecbf8bf612e57a5e1d5d0c0d7fb6b` |
| Commit timestamp | `2026-10-31T14:41:14-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/SketchFigure|src/screens/reader/figures/sketch/SketchFigure.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchRunner|src/screens/reader/figures/sketch/sketchRunner.ts]] → [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchWorkerClient|src/screens/reader/figures/sketch/sketchWorkerClient.ts]]

## Public API

- `export function createSketchWorker():` — function, line 5

## Internal implementation anchors

No non-exported declaration anchor was detected by the static extractor.

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchRunner|src/screens/reader/figures/sketch/sketchRunner.ts]] — dynamic import: dynamic import; no named call claim

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketch.worker|src/screens/reader/figures/sketch/sketch.worker.ts]] — import-or-re-export; imports `SketchWorker`
- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchRunner|src/screens/reader/figures/sketch/sketchRunner.ts]] — import-or-re-export; imports `WorkerRequest`, `WorkerResponse`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

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

1. Modify [apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchWorkerClient.ts](../../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchWorkerClient.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
