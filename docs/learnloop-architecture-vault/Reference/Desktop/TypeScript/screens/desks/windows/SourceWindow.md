---
title: "Desktop module · src/screens/desks/windows/SourceWindow.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.windows.SourceWindow"
language: "TypeScript"
area: "TypeScript/screens/desks/windows"
source_path: "apps/learnloop-tauri/src/screens/desks/windows/SourceWindow.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/windows/SourceWindow.tsx"
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

# `src/screens/desks/windows/SourceWindow.tsx`

Area: [[Reference/Desktop/TypeScript/screens/desks/windows/_area|TypeScript/screens/desks/windows]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `SourceWindow` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/windows/SourceWindow.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/windows/SourceWindow.tsx) |
| Source lines | 127 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/windows/_area|TypeScript/screens/desks/windows]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/windows/SourceWindow|src/screens/desks/windows/SourceWindow.tsx]]

## Public API

- `export type ReaderPassThrough = Pick<ComponentProps<typeof ScopedSource>, "onCheckMe" | "onUseExercise" | "onTeachMe" | "workbench">` — type, line 15
- `export interface SourceStatus` — interface, line 17
- `export function SourceWindow(` — function, line 24

## Internal implementation anchors

- `const onTitle = useCallback((title: string)` — const, line 90
- `const onReaderStatus = useCallback( (status:` — const, line 91
- `const windowing = useMemo<ReaderWindowing>( ()` — const, line 97
- `const initialSource = useMemo( ()` — const, line 102

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/fixtures/desks/harness|src/fixtures/desks/harness.tsx]] — import-or-re-export: `SourceWindow`; references `SourceWindow`
- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `ReaderPassThrough`, `SourceStatus`, `SourceWindow`; references `ReaderPassThrough`, `SourceStatus`, `SourceWindow`
- [[Reference/Desktop/TypeScript/screens/desks/video/VideoWindow|src/screens/desks/video/VideoWindow.tsx]] — import-or-re-export: `SourceWindow`; references `SourceWindow`
- [[Reference/Desktop/TypeScript/screens/desks/windows/PanelWindow|src/screens/desks/windows/PanelWindow.tsx]] — import-or-re-export: `ReaderPassThrough`; references `ReaderPassThrough`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ContentRefDto`, `SourceLibraryCard`
- [[Reference/Desktop/TypeScript/screens/desks/pen/PenLayer|src/screens/desks/pen/PenLayer.tsx]] — import-or-re-export; imports `PenLayer`
- [[Reference/Desktop/TypeScript/screens/desks/source/ScopedSource|src/screens/desks/source/ScopedSource.tsx]] — import-or-re-export; imports `ScopedSource`
- [[Reference/Desktop/TypeScript/screens/desks/source/types|src/screens/desks/source/types.ts]] — import-or-re-export; imports `PenSurface`, `ReaderLens`, `ReaderWindowing`, `WindowInquiry`
- [[Reference/Desktop/TypeScript/screens/reader/YouTubeWatchPanel|src/screens/reader/YouTubeWatchPanel.tsx]] — import-or-re-export; imports `VideoExtras`
- [[Reference/Desktop/TypeScript/screens/reader/readingPosition|src/screens/reader/readingPosition.ts]] — import-or-re-export; imports `ReadingPosition`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderInquiry|src/screens/reader/useReaderInquiry.ts]] — import-or-re-export; imports `WindowAsk`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Import Canonical Sources|Import Canonical Sources]] — owns import sequencing.
- [[Architecture/Content Pipeline#Durable checkpoint ladder|content checkpoint ladder]] — owns pipeline persistence semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/windows/SourceWindow.recap.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/windows/SourceWindow.recap.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/windows/SourceWindow.lifecycle.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/windows/SourceWindow.lifecycle.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

1. Modify [apps/learnloop-tauri/src/screens/desks/windows/SourceWindow.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/windows/SourceWindow.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
