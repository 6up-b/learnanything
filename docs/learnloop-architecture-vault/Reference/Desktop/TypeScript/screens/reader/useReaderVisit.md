---
title: "Desktop module · src/screens/reader/useReaderVisit.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.useReaderVisit"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/useReaderVisit.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/useReaderVisit.ts"
source_commit: "38ccfa65f8d3889cdb161cd5db0cea3a5d0582f0"
source_commit_timestamp: "2026-11-09T06:12:48-05:00"
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

# `src/screens/reader/useReaderVisit.ts`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `ReaderVisitInput`, `ReaderVisit`, `useReaderVisit` within the desktop's TypeScript/screens/reader ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/useReaderVisit.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/useReaderVisit.ts) |
| Source lines | 134 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `38ccfa65f8d3889cdb161cd5db0cea3a5d0582f0` |
| Commit timestamp | `2026-11-09T06:12:48-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/useReaderVisit|src/screens/reader/useReaderVisit.ts]]

## Public API

- `export interface ReaderVisitInput` — interface, line 25
- `export interface ReaderVisit` — interface, line 34
- `export function useReaderVisit(` — function, line 54

## Internal implementation anchors

- `const visitRef = useRef<` — const, line 57
- `const backToReadingRef = useRef<` — const, line 58
- `const proactiveSeenRef = useRef<Set<string>>(new Set())` — const, line 59
- `const now = Date.now()` — const, line 71
- `const visit =` — const, line 72
- `const touchVisit = useCallback(()` — const, line 95
- `const visit = visitRef.current` — const, line 96
- `const visitPayload = useCallback( ()` — const, line 100
- `const noteBackToReading = useCallback(()` — const, line 104
- `const pending = backToReadingRef.current` — const, line 105
- `const noteUsableResult = useCallback((jobId: string, actionKind: string)` — const, line 113
- `const noteSelection = useCallback((spanCount: number, surface: string)` — const, line 116
- `const noteProactive = useCallback((key: string, element: string)` — const, line 122
- `const resetVisitState = useCallback(()` — const, line 128

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `useReaderVisit`; references `useReaderVisit`
- [[Reference/Desktop/TypeScript/screens/lessonActivity|src/screens/lessonActivity.ts]] — import-or-re-export: `VISIT_IDLE_MS`; references `VISIT_IDLE_MS`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderInquiry|src/screens/reader/useReaderInquiry.ts]] — import-or-re-export: `ReaderVisit`; references `ReaderVisit`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ReaderPdfViewDto`, `ReaderRenderViewDto`
- [[Reference/Desktop/TypeScript/screens/reader/activity|src/screens/reader/activity.ts]] — import-or-re-export; imports `flushReaderActivity`, `logReaderAction`, `logReaderActivity`, `newActivityId`, `noteLearnerActivity`, `setReaderActivityEnabled`, `takeReaderVisitInitiator`
- [[Reference/Desktop/TypeScript/screens/reader/visitClock|src/screens/reader/visitClock.ts]] — import-or-re-export; imports `VISIT_IDLE_MS`, `accrueVisit`, `visitSeconds`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/readerHooks.parity.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/readerHooks.parity.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/lessonActivity.test.ts](../../../../../../../apps/learnloop-tauri/src/screens/lessonActivity.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_sidecar_reader.py](../../../../../../../tests/test_sidecar_reader.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_reader_pdf_view.py](../../../../../../../tests/test_sidecar_reader_pdf_view.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_render_views.py](../../../../../../../tests/test_reader_render_views.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_requests.py](../../../../../../../tests/test_reader_requests.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/reader/useReaderVisit.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/useReaderVisit.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
