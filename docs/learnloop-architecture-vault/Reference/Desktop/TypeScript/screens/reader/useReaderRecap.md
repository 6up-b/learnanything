---
title: "Desktop module · src/screens/reader/useReaderRecap.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.useReaderRecap"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/useReaderRecap.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/useReaderRecap.ts"
source_commit: "c94882abe7a8f5a7cde491603d6abba8a4c0e2db"
source_commit_timestamp: "2026-10-22T16:58:30-04:00"
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

# `src/screens/reader/useReaderRecap.ts`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `ReaderRecapInput`, `ReaderRecapCtl`, `useReaderRecap` within the desktop's TypeScript/screens/reader ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/useReaderRecap.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/useReaderRecap.ts) |
| Source lines | 231 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `c94882abe7a8f5a7cde491603d6abba8a4c0e2db` |
| Commit timestamp | `2026-10-22T16:58:30-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/useReaderRecap|src/screens/reader/useReaderRecap.ts]]

## Public API

- `export interface ReaderRecapInput` — interface, line 24
- `export interface ReaderRecapCtl` — interface, line 45
- `export function useReaderRecap(` — function, line 63

## Internal implementation anchors

- `const autoFoldedRef = useRef(false)` — const, line 72
- `const shownRef = useRef<string | null>(null)` — const, line 73
- `const extractionRef = useRef<string | null>(extractionId)` — const, line 74
- `const visitIdRef = useRef(visitId)` — const, line 76
- `const revealRef = useRef(reveal)` — const, line 78
- `const record = useCallback((event: ReaderRecapEvent)` — const, line 81
- `const extraction = extractionRef.current` — const, line 82
- `let cancelled = false` — let, line 94
- `let cancelled = false` — let, line 137
- `const noteShown = useCallback(()` — const, line 151
- `const extraction = extractionRef.current` — const, line 152
- `const key = `$` — const, line 154
- `const expand = useCallback(()` — const, line 160
- `const continueReading = useCallback(()` — const, line 161
- `const dismiss = useCallback(async ()` — const, line 165
- `const reload = useCallback(()` — const, line 173
- `const openWrapUp = useCallback(async ()` — const, line 175
- `const extraction = extractionRef.current` — const, line 176
- `let result: ReaderWrapUpDto` — let, line 180
- `const closeWrapUp = useCallback(()` — const, line 193
- `const onKey = (event: KeyboardEvent)` — const, line 199
- `const target = event.target` — const, line 202
- `let cancelled = false` — let, line 214

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `useReaderRecap`; references `useReaderRecap`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ReaderRecapCardDto`, `ReaderRecapEvent`, `ReaderWrapUpDto`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/recapReview.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/recapReview.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/WrapUp.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/WrapUp.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/RecapCard.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/RecapCard.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

1. Modify [apps/learnloop-tauri/src/screens/reader/useReaderRecap.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/useReaderRecap.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
