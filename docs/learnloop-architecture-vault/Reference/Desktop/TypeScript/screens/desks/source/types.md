---
title: "Desktop module · src/screens/desks/source/types.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.source.types"
language: "TypeScript"
area: "TypeScript/screens/desks/source"
source_path: "apps/learnloop-tauri/src/screens/desks/source/types.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/source/types.ts"
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

# `src/screens/desks/source/types.ts`

Area: [[Reference/Desktop/TypeScript/screens/desks/source/_area|TypeScript/screens/desks/source]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `ReaderOpenSource`, `ReaderWindowing`, `WindowInquiry`, `ReaderLens` and related exports within the desktop's TypeScript/screens/desks/source ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/source/types.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/source/types.ts) |
| Source lines | 135 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/source/_area|TypeScript/screens/desks/source]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/source/types|src/screens/desks/source/types.ts]]

## Public API

- `export interface ReaderOpenSource` — interface, line 17
- `export interface ReaderWindowing` — interface, line 36
- `export interface WindowInquiry` — interface, line 88
- `export interface ReaderLens` — interface, line 102
- `export interface PenSurface` — interface, line 114
- `export interface ReaderCheckMeRequest extends CueCheckMeRequest` — interface, line 123
- `export type ReaderExerciseRequest = ReaderWorkbenchExercise &` — type, line 135

## Internal implementation anchors

No non-exported declaration anchor was detected by the static extractor.

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `ReaderCheckMeRequest`, `ReaderExerciseRequest`, `ReaderOpenSource`; references `ReaderCheckMeRequest`, `ReaderExerciseRequest`, `ReaderOpenSource`
- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `WindowInquiry`; references `WindowInquiry`
- [[Reference/Desktop/TypeScript/screens/desks/checks/CheckCard|src/screens/desks/checks/CheckCard.tsx]] — import-or-re-export: `ReaderLens`; references `ReaderLens`
- [[Reference/Desktop/TypeScript/screens/desks/goal/GoalLayer|src/screens/desks/goal/GoalLayer.tsx]] — import-or-re-export: `ReaderLens`; references `ReaderLens`
- [[Reference/Desktop/TypeScript/screens/desks/goal/marks|src/screens/desks/goal/marks.tsx]] — import-or-re-export: `ReaderLens`; references `ReaderLens`
- [[Reference/Desktop/TypeScript/screens/desks/pen/PenLayer|src/screens/desks/pen/PenLayer.tsx]] — import-or-re-export: `PenSurface`; references `PenSurface`
- [[Reference/Desktop/TypeScript/screens/desks/source/ScopedSource|src/screens/desks/source/ScopedSource.tsx]] — import-or-re-export: `ReaderCheckMeRequest`, `ReaderExerciseRequest`, `ReaderOpenSource`, `ReaderWindowing`; references `ReaderCheckMeRequest`, `ReaderExerciseRequest`, `ReaderOpenSource`, `ReaderWindowing`
- [[Reference/Desktop/TypeScript/screens/desks/video/followLens|src/screens/desks/video/followLens.ts]] — import-or-re-export: `ReaderLens`; references `ReaderLens`
- [[Reference/Desktop/TypeScript/screens/desks/windows/SourceWindow|src/screens/desks/windows/SourceWindow.tsx]] — import-or-re-export: `PenSurface`, `ReaderLens`, `ReaderWindowing`, `WindowInquiry`; references `PenSurface`, `ReaderLens`, `ReaderWindowing`, `WindowInquiry`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `SourceLibraryCard`
- [[Reference/Desktop/TypeScript/screens/desks/lifecycle|src/screens/desks/lifecycle.tsx]] — import-or-re-export; imports `ListenerHub`, `ScopeClaims`, `WindowLifecycle`
- [[Reference/Desktop/TypeScript/screens/desks/problem/problemPads|src/screens/desks/problem/problemPads.ts]] — import-or-re-export; imports `ProblemHandoff`
- [[Reference/Desktop/TypeScript/screens/reader/YouTubeWatchPanel|src/screens/reader/YouTubeWatchPanel.tsx]] — import-or-re-export; imports `VideoExtras`, `WatchLens`
- [[Reference/Desktop/TypeScript/screens/reader/exerciseCandidates (ts)|src/screens/reader/exerciseCandidates.ts]] — import-or-re-export; imports `ReaderWorkbenchExercise`
- [[Reference/Desktop/TypeScript/screens/reader/readingPosition|src/screens/reader/readingPosition.ts]] — import-or-re-export; imports `ReadingPosition`
- [[Reference/Desktop/TypeScript/screens/reader/returnStack|src/screens/reader/returnStack.ts]] — import-or-re-export; imports `ReturnStack`
- [[Reference/Desktop/TypeScript/screens/reader/sideBySide|src/screens/reader/sideBySide.ts]] — import-or-re-export; imports `PaneTarget`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderCues|src/screens/reader/useReaderCues.ts]] — import-or-re-export; imports `CueCheckMeRequest`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderInquiry|src/screens/reader/useReaderInquiry.ts]] — import-or-re-export; imports `WindowAsk`, `WindowExchange`
- [[Reference/Desktop/TypeScript/screens/reader/useSideBySide|src/screens/reader/useSideBySide.ts]] — import-or-re-export; imports `SideBySideVia`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Import Canonical Sources|Import Canonical Sources]] — owns import sequencing.
- [[Architecture/Content Pipeline#Durable checkpoint ladder|content checkpoint ladder]] — owns pipeline persistence semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/windows/SourceWindow.lifecycle.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/windows/SourceWindow.lifecycle.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/pen/PenLayer.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pen/PenLayer.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_sidecar_ingest_m3.py](../../../../../../../../tests/test_sidecar_ingest_m3.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_source_ingestion.py](../../../../../../../../tests/test_source_ingestion.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_ingest_runner.py](../../../../../../../../tests/test_ingest_runner.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_init.py](../../../../../../../../tests/test_init.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/source/types.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/source/types.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
