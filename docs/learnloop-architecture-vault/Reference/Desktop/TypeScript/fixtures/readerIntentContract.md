---
title: "Desktop module · src/fixtures/readerIntentContract.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.fixtures.readerIntentContract"
language: "TypeScript"
area: "TypeScript/fixtures"
source_path: "apps/learnloop-tauri/src/fixtures/readerIntentContract.ts"
source_paths:
  - "apps/learnloop-tauri/src/fixtures/readerIntentContract.ts"
source_commit: "cfb103d72ab61860c77b5ddc699d2267a180e772"
source_commit_timestamp: "2026-10-27T17:57:00-04:00"
source_worktree_state: "clean"
activation_kind: "vitest-support"
activation_evidence: "Outside the Vite build graph: test support imported only by vitest files, directly or through other test support; it runs under `npm test` and is never in the app bundle."
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/reference/module"
  - "learnloop/desktop"
  - "learnloop/desktop/typescript"
  - "refactor/active"
---

# `src/fixtures/readerIntentContract.ts`

Area: [[Reference/Desktop/TypeScript/fixtures/_area|TypeScript/fixtures]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Exposes deterministic `readerIntentContract` fixture data for a reproducible desktop scenario.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/fixtures/readerIntentContract.ts](../../../../../../apps/learnloop-tauri/src/fixtures/readerIntentContract.ts) |
| Source lines | 436 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/fixtures/_area|TypeScript/fixtures]] |
| Refactor status | `ACTIVE` |
| Activation kind | `vitest-support` |
| Worktree state | `clean` |
| Source commit | `cfb103d72ab61860c77b5ddc699d2267a180e772` |
| Commit timestamp | `2026-10-27T17:57:00-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> Outside the Vite build graph: test support imported only by vitest files, directly or through other test support; it runs under `npm test` and is never in the app bundle.
>
> Test-import chain (from a vitest file): [[Reference/Desktop/TypeScript/fixtures/readerIntentContract|src/fixtures/readerIntentContract.ts]]

## Public API

- `export const readerIntentContractFixture: ReaderIntentContractDto =` — const, line 8

## Internal implementation anchors

No non-exported declaration anchor was detected by the static extractor.

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

No live desktop source file directly imports this module. Do not infer dormancy: it can still be an implicit entry, worker, ambient declaration, fixture, or runtime-dispatched surface.

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ReaderIntentContractDto`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/rw1bReview.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/reader/rw1bReview.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/readingPathsReader.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/reader/readingPathsReader.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/nextStepFold.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/reader/nextStepFold.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/libraryRoles.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/reader/libraryRoles.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/libraryExercisesReader.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/reader/libraryExercisesReader.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/libraryAskSwitchOff.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/reader/libraryAskSwitchOff.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/libraryAsk.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/reader/libraryAsk.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/intentBoxInShell.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/reader/intentBoxInShell.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_sidecar_reader.py](../../../../../../tests/test_sidecar_reader.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_reader_pdf_view.py](../../../../../../tests/test_sidecar_reader_pdf_view.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_render_views.py](../../../../../../tests/test_reader_render_views.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_requests.py](../../../../../../tests/test_reader_requests.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/fixtures/readerIntentContract.ts](../../../../../../apps/learnloop-tauri/src/fixtures/readerIntentContract.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
