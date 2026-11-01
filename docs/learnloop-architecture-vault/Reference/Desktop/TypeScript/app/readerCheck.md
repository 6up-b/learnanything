---
title: "Desktop module · src/app/readerCheck.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.app.readerCheck"
language: "TypeScript"
area: "TypeScript/app"
source_path: "apps/learnloop-tauri/src/app/readerCheck.ts"
source_paths:
  - "apps/learnloop-tauri/src/app/readerCheck.ts"
source_commit: "9ed381bc3787439c88ffe3ec08b319b51049fa02"
source_commit_timestamp: "2026-11-01T03:48:43-05:00"
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

# `src/app/readerCheck.ts`

Area: [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `ReaderReturn`, `returnsToReader`, `keepReaderReturn`, `readerCheckOffer` within the desktop's TypeScript/app ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/app/readerCheck.ts](../../../../../../apps/learnloop-tauri/src/app/readerCheck.ts) |
| Source lines | 62 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `9ed381bc3787439c88ffe3ec08b319b51049fa02` |
| Commit timestamp | `2026-11-01T03:48:43-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/app/readerCheck|src/app/readerCheck.ts]]

## Public API

- `export interface ReaderReturn` — interface, line 16
- `export function returnsToReader(readerReturn: ReaderReturn | null, practiceItemId: string | null): boolean` — function, line 30
- `export function keepReaderReturn(readerReturn: ReaderReturn | null, openingItemId: string): ReaderReturn | null` — function, line 35
- `export function readerCheckOffer( result: Pick<DailyPlanDto, "enabled" | "step">, practiceItemId: string, proposalId: string | null, /** RW4b: the sources service's import that wrote the item (a textbook exercise). */ importId: string | null = null, ): Practi…` — function, line 47

## Internal implementation anchors

- `const step = result.step` — const, line 54
- `const item = step && step.kind === "item" ? step : null` — const, line 55

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `ReaderReturn`, `keepReaderReturn`, `readerCheckOffer`, `returnsToReader`; references `ReaderReturn`, `keepReaderReturn`, `readerCheckOffer`, `returnsToReader`
- [[Reference/Desktop/TypeScript/app/readerWorkbench|src/app/readerWorkbench.ts]] — import-or-re-export: `ReaderReturn`; references `ReaderReturn`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `DailyPlanDto`, `SourceLibraryCard`
- [[Reference/Desktop/TypeScript/app/practiceOffer|src/app/practiceOffer.ts]] — import-or-re-export; imports `PracticeOffer`
- [[Reference/Desktop/TypeScript/screens/reader/returnStack|src/screens/reader/returnStack.ts]] — import-or-re-export; imports `ReturnStack`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/readerWorkbenchExercise.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/reader/readerWorkbenchExercise.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/app/readerWorkbench.test.ts](../../../../../../apps/learnloop-tauri/src/app/readerWorkbench.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/app/readerCheck.test.ts](../../../../../../apps/learnloop-tauri/src/app/readerCheck.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_sidecar_reader.py](../../../../../../tests/test_sidecar_reader.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_reader_pdf_view.py](../../../../../../tests/test_sidecar_reader_pdf_view.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_render_views.py](../../../../../../tests/test_reader_render_views.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_requests.py](../../../../../../tests/test_reader_requests.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/app/readerCheck.ts](../../../../../../apps/learnloop-tauri/src/app/readerCheck.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
