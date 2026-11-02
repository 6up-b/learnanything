---
title: "Desktop module · src/screens/reader/figures/sketch/sketchFrameProtocol.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.figures.sketch.sketchFrameProtocol"
language: "TypeScript"
area: "TypeScript/screens/reader/figures/sketch"
source_path: "apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchFrameProtocol.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchFrameProtocol.ts"
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

# `src/screens/reader/figures/sketch/sketchFrameProtocol.ts`

Area: [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/_area|TypeScript/screens/reader/figures/sketch]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `SKETCH_FRAME_PATH`, `SKETCH_ENGINE_MAX_BYTES`, `SKETCH_WORKER_SOURCE_MAX_CHARS`, `FRAME_MESSAGE_MAX` and related exports within the desktop's TypeScript/screens/reader/figures/sketch ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchFrameProtocol.ts](../../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchFrameProtocol.ts) |
| Source lines | 94 |
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
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/LessonScreen|src/screens/LessonScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/SketchFigure|src/screens/reader/figures/sketch/SketchFigure.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchRunner|src/screens/reader/figures/sketch/sketchRunner.ts]] → [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchCompartmentClient|src/screens/reader/figures/sketch/sketchCompartmentClient.ts]] → [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchCompartment|src/screens/reader/figures/sketch/sketchCompartment.ts]] → [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchFrameProtocol|src/screens/reader/figures/sketch/sketchFrameProtocol.ts]]

## Public API

- `export const SKETCH_FRAME_PATH = "/sketch-frame.html"` — const, line 22
- `export const SKETCH_ENGINE_MAX_BYTES = 2 * 1024 * 1024` — const, line 24
- `export const SKETCH_WORKER_SOURCE_MAX_CHARS = 1024 * 1024` — const, line 26
- `export const FRAME_MESSAGE_MAX = 600` — const, line 28
- `export type FrameNotice =` — type, line 31
- `export function parseFrameNotice(data: unknown): FrameNotice | null` — function, line 41
- `export function parseWorkerBoot(data: unknown, ports: readonly unknown[]):` — function, line 54
- `export const STRIPPED_GLOBALS = [ "fetch", "XMLHttpRequest", "WebSocket", "EventSource", "importScripts", "indexedDB", "caches", "Worker", "SharedWorker", "WebTransport", "BroadcastChannel", "RTCPeerConnection", ] as const` — const, line 68
- `export function stripNetwork(scope: object): string[]` — function, line 73

## Internal implementation anchors

- `const isPlain = (value: unknown): value is Record<string, unknown>` — const, line 33
- `const hasOnly = (value: Record<string, unknown>, keys: string[])` — const, line 36
- `const message = typeof data.message === "string" && data.message.length <= FRAME_MESSAGE_MAX ? data.message : "the sketch engine could not start here"` — const, line 45
- `const kept: string[] = []` — const, line 74

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchCompartment|src/screens/reader/figures/sketch/sketchCompartment.ts]] — import-or-re-export: `SKETCH_ENGINE_MAX_BYTES`, `SKETCH_FRAME_PATH`, `SKETCH_WORKER_SOURCE_MAX_CHARS`, `parseFrameNotice`; references `SKETCH_ENGINE_MAX_BYTES`, `SKETCH_FRAME_PATH`, `SKETCH_WORKER_SOURCE_MAX_CHARS`, `parseFrameNotice`
- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchWorkerCore|src/screens/reader/figures/sketch/sketchWorkerCore.ts]] — import-or-re-export: `FRAME_MESSAGE_MAX`, `parseWorkerBoot`, `stripNetwork`; references `FRAME_MESSAGE_MAX`, `parseWorkerBoot`, `stripNetwork`

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

1. Modify [apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchFrameProtocol.ts](../../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchFrameProtocol.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
