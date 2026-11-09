---
title: "Desktop module · src/screens/reader/LibraryAnswer.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.LibraryAnswer"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/LibraryAnswer.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/LibraryAnswer.tsx"
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

# `src/screens/reader/LibraryAnswer.tsx`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `LibraryAnswer` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/LibraryAnswer.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/LibraryAnswer.tsx) |
| Source lines | 693 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/LibraryAnswer|src/screens/reader/LibraryAnswer.tsx]]

## Public API

- `export type ExplorableOutcome = | "built" // the figure is under its passage | "not_built" // the build was refused, failed or did not verify | "stopped" // the build was cancelled (or its book closed) | "another_reading" // the book opened on another reading…` — type, line 61
- `export const LIBRARY_EXPLORABLE_COPY =` — const, line 72
- `export function CompareTable(` — function, line 196
- `export const COMPARE_AGAIN_COPY =` — const, line 201
- `export function CompareTableByBook(` — function, line 208
- `export function LibraryAnswer(` — function, line 279

## Internal implementation anchors

- `const linkStyle =` — const, line 47
- `const headStyle =` — const, line 89
- `function locator(hit: LibraryHitDto): string` — function, line 91
- `function clip(text: string, limit = 420): string` — function, line 95
- `const flat = text.split(/\s+/).join(" ").trim()` — const, line 96
- `function HitBlock(` — function, line 100
- `const pressOffer = ()` — const, line 122
- `const settled = onExplorable()` — const, line 125
- `const modelRole = note?.roles?.length && hit.role !== note.roles[0] ? note.roles[0].replace(/_/g, " ") : null` — const, line 128
- `function CompareCells(` — function, line 172
- `function uncheckedBecause(verification: CompareTableDto["verification"]): string | null` — function, line 187
- `const status = `$` — const, line 188
- `const unverified = table.unverifiedSources ?? []` — const, line 209
- `const because = uncheckedBecause(table.verification)` — const, line 210
- `const state = ctl.state` — const, line 305
- `const gridActions: CompareGridActions | null = ctl.byPoint ?` — const, line 309
- `const ask = state.ask.value` — const, line 333
- `const scopedCompare = ctl.scopeOn && Boolean(state.chips) && Boolean(state.lastCompare) && state.lastCompare?.door !== "pins"` — const, line 335
- `const answerSources = new Set((ask?.hits ?? []).flatMap((hit)` — const, line 338
- `const notes = new Map((state.notes.value?.notes ?? []).map((note)` — const, line 339
- `const notesPhase = state.notes.phase` — const, line 340
- `const hits = new Map((ask?.hits ?? []).map((hit)` — const, line 341
- `const order = state.notes.value?.order ?? []` — const, line 342
- `const ordered = (keys: string[])` — const, line 343
- `const left = order.indexOf(a)` — const, line 344
- `const right = order.indexOf(b)` — const, line 345
- `const itemList = (items: ProposedItemDto[])` — const, line 348
- `const block = (key: string)` — const, line 366
- `const hit = hits.get(key)` — const, line 367
- `const prerequisites = ask?.expansions.find((expansion)` — const, line 383
- `const perspectiveList = ()` — const, line 384
- `const pinsCompare = state.compare.phase !== "idle" ? ( <ModelActionState phase=` — const, line 389
- `const pinsTutor = ( <>` — const, line 408
- `const onKeyDown = (event: ReactKeyboardEvent<HTMLElement>)` — const, line 460
- `const target = event.target as HTMLElement` — const, line 461
- `const items = Array.from(event.currentTarget.querySelectorAll<HTMLElement>("[data-library-hit]"))` — const, line 469
- `const current = target.closest<HTMLElement>("[data-library-hit]")` — const, line 470
- `const key = current?.getAttribute("data-library-hit") ?? null` — const, line 471
- `const at = current ? items.indexOf(current) : -1` — const, line 475
- `const next = items[(at + (event.key === "ArrowDown" ? 1 : -1) + items.length) % items.length]` — const, line 476
- `const hit = hits.get(key)` — const, line 494

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `ExplorableOutcome`, `LibraryAnswer`, `LibraryExercisesProps`; references `ExplorableOutcome`, `LibraryAnswer`, `LibraryExercisesProps`
- [[Reference/Desktop/TypeScript/screens/reader/KeptMark|src/screens/reader/KeptMark.tsx]] — import-or-re-export: `CompareTable`; references `CompareTable`
- [[Reference/Desktop/TypeScript/screens/reader/LibraryPane|src/screens/reader/LibraryPane.tsx]] — import-or-re-export: `ExplorableOutcome`, `LibraryAnswer`, `LibraryExercisesProps`; references `ExplorableOutcome`, `LibraryAnswer`, `LibraryExercisesProps`
- [[Reference/Desktop/TypeScript/screens/reader/TutorOffers|src/screens/reader/TutorOffers.tsx]] — import-or-re-export: `CompareTable`; references `CompareTable`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CompareTableDto`, `LibraryHitDto`, `LibraryNoteDto`, `ProposedItemDto`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`
- [[Reference/Desktop/TypeScript/screens/reader/CompareKeep|src/screens/reader/CompareKeep.tsx]] — import-or-re-export; imports `CompareKeep`, `KEEP_COPY`, `KeptComparisonView`, `shortDate`
- [[Reference/Desktop/TypeScript/screens/reader/ComparePointTable|src/screens/reader/ComparePointTable.tsx]] — import-or-re-export; imports `CompareGridActions`, `CompareGridActionsContext`, `ComparePointTable`, `useCompareGridActions`
- [[Reference/Desktop/TypeScript/screens/reader/CompareScope|src/screens/reader/CompareScope.tsx]] — import-or-re-export; imports `CompareScopeBody`, `CompareScopeView`, `PeekPanel`
- [[Reference/Desktop/TypeScript/screens/reader/ModelActionState|src/screens/reader/ModelActionState.tsx]] — import-or-re-export; imports `ModelActionState`
- [[Reference/Desktop/TypeScript/screens/reader/ProposalExercises|src/screens/reader/ProposalExercises.tsx]] — import-or-re-export; imports `LibraryExercisesProps`, `ProposalExercises`
- [[Reference/Desktop/TypeScript/screens/reader/comparePoints|src/screens/reader/comparePoints.ts]] — import-or-re-export; imports `byPoint`
- [[Reference/Desktop/TypeScript/screens/reader/roleLabel|src/screens/reader/roleLabel.ts]] — import-or-re-export; imports `hitRoleLabel`
- [[Reference/Desktop/TypeScript/screens/reader/useLibraryAsk|src/screens/reader/useLibraryAsk.ts]] — import-or-re-export; imports `LIBRARY_COPY`, `LibraryAskController`, `SCOPE_COPY`
- [[Reference/Desktop/TypeScript/screens/reader/voices|src/screens/reader/voices.tsx]] — import-or-re-export; imports `EvidenceMarker`, `MeaningLabel`, `ModelVoice`, `SourceVoice`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.
- [[Workflows/Import Canonical Sources|Import Canonical Sources]] — owns import sequencing.
- [[Architecture/Content Pipeline#Durable checkpoint ladder|content checkpoint ladder]] — owns pipeline persistence semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/libraryExercises.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/libraryExercises.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/figures/libraryOfferSettle.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/libraryOfferSettle.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/figures/advancedPanels.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/advancedPanels.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/comparePointTable.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/comparePointTable.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/compareKeep.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/compareKeep.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

1. Modify [apps/learnloop-tauri/src/screens/reader/LibraryAnswer.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/LibraryAnswer.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
