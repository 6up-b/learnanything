---
title: "Desktop area · TypeScript/screens/reader/figures/sketch"
type: "desktop-area-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/figures/sketch"
source_commit: "d2afa824ceecb2f6e35f7c6ff51d9008a644e70d"
source_commit_timestamp: "2026-11-01T14:49:03-05:00"
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/moc"
  - "learnloop/desktop"
  - "learnloop/desktop/area"
---

# TypeScript/screens/reader/figures/sketch

Parent: [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]] · Source: [apps/learnloop-tauri/src/screens/reader/figures/sketch](../../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sketch)

## Responsibility

The sandboxed sketch tier: the pinned engine host, its Worker protocol and runner, and the scene renderer.

> [!note] Ownership boundary
> This map inventories code organization. End-to-end behavior remains in the linked workflow and concept notes.

## Child areas

No nested ownership area.

## Direct modules

| Module | Status | Purpose | Imports | Imported by |
|---|---|---|---:|---:|
| [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/SketchFigure|SketchFigure.tsx]] | `ACTIVE` | Implements the `SketchFigure` routed desktop screen and coordinates its learner-facing workflow state. | 12 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/SketchScene (tsx)|SketchScene.tsx]] | `ACTIVE` | Implements the `SketchScene` routed desktop screen and coordinates its learner-facing workflow state. | 2 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/checksWithdrawn|checksWithdrawn.ts]] | `ACTIVE` | Provides `withdrawChecks`, `checksWithdrawn`, `useChecksWithdrawn`, `resetWithdrawnChecks` within the desktop's TypeScript/screens/reader/figures/sketch ownership area. | 0 | 2 |
| [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/engineForTests|engineForTests.ts]] | `ACTIVE` | Provides `ENGINE_BYTES`, `nodeDigest`, `newHost` within the desktop's TypeScript/screens/reader/figures/sketch ownership area. | 1 | 0 |
| [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketch.worker|sketch.worker.ts]] | `ACTIVE` | Provides the desktop `sketch.worker` module within the TypeScript/screens/reader/figures/sketch ownership area. | 1 | 0 |
| [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchCompartment|sketchCompartment.ts]] | `ACTIVE` | Provides `WorkerLike`, `CompartmentInputs`, `createSketchCompartment`, `appEngineBytes` within the desktop's TypeScript/screens/reader/figures/sketch ownership area. | 2 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchCompartmentClient|sketchCompartmentClient.ts]] | `ACTIVE` | Provides `createSketchWorker` within the desktop's TypeScript/screens/reader/figures/sketch ownership area. | 1 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchEngine|sketchEngine.ts]] | `ACTIVE` | Provides `ENGINE_SHA256`, `SKETCH_FRAME_MS`, `SKETCH_WATCHDOG_FRAMES`, `PLAY_TICKS` and related exports within the desktop's TypeScript/screens/reader/figures/sketch ownership area. | 0 | 6 |
| [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchFrameProtocol|sketchFrameProtocol.ts]] | `ACTIVE` | Provides `SKETCH_FRAME_PATH`, `SKETCH_ENGINE_MAX_BYTES`, `SKETCH_WORKER_SOURCE_MAX_CHARS`, `FRAME_MESSAGE_MAX` and related exports within the desktop's TypeScript/screens/reader/figures/sketch ownership area. | 0 | 2 |
| [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchProtocol|sketchProtocol.ts]] | `ACTIVE` | Provides `SKETCH_MAX_SOURCE_BYTES`, `SKETCH_MAX_CLOCK_STEPS`, `SKETCH_MAX_PARAMETERS`, `REPLY_MESSAGE_MAX` and related exports within the desktop's TypeScript/screens/reader/figures/sketch ownership area. | 1 | 3 |
| [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchRunner|sketchRunner.ts]] | `ACTIVE` | Provides `SketchRunner`, `SketchRunnerFactory`, `hostRunner`, `portRunner` and related exports within the desktop's TypeScript/screens/reader/figures/sketch ownership area. | 3 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchScene (ts)|sketchScene.ts]] | `ACTIVE` | Provides `SKETCH_MAX_ELEMENTS`, `SKETCH_MAX_POINTS`, `SKETCH_MAX_CELLS`, `SKETCH_MAX_SERIES` and related exports within the desktop's TypeScript/screens/reader/figures/sketch ownership area. | 1 | 3 |
| [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchWorkerCore|sketchWorkerCore.ts]] | `ACTIVE` | Provides `WorkerScopeLike`, `EngineFactory`, `startSketchWorker` within the desktop's TypeScript/screens/reader/figures/sketch ownership area. | 3 | 1 |

## Modification guidance

Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.

## Related notes

- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]
- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]
- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]
