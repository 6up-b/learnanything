---
title: "Desktop module · src/screens/reader/CompareKeep.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.CompareKeep"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/CompareKeep.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/CompareKeep.tsx"
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

# `src/screens/reader/CompareKeep.tsx`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `CompareKeep` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/CompareKeep.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/CompareKeep.tsx) |
| Source lines | 306 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/KeptMark|src/screens/reader/KeptMark.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/CompareKeep|src/screens/reader/CompareKeep.tsx]]

## Public API

- `export const KEEP_COPY =` — const, line 29
- `export const FINE_LABELS: Record<string, string> =` — const, line 51
- `export function fineLabel(fine: string | null | undefined): string` — function, line 60
- `export function shortDate(iso: string | null | undefined): string` — function, line 64
- `export function relationPairs(table: CompareTableDto): RelationPair[]` — function, line 85
- `export type KeepTarget =` — type, line 118
- `export function CompareKeep(` — function, line 121
- `export function KeptComparisonView(` — function, line 261

## Internal implementation anchors

- `const date = new Date(iso)` — const, line 66
- `const linkStyle =` — const, line 70
- `const quietStyle =` — const, line 74
- `const headStyle =` — const, line 75
- `interface RelationPair` — interface, line 77
- `const seen = new Map<string, RelationPair>()` — const, line 86
- `const title = row.sourceTitle ?? "a source"` — const, line 88
- `const other = cell.otherSourceTitle ?? "a source"` — const, line 90
- `const titles = [title, other].sort() as [string, string]` — const, line 91
- `const key = `$` — const, line 92
- `interface TakeTarget` — interface, line 99
- `function takeTargets(table: CompareTableDto): TakeTarget[]` — function, line 105
- `const rows = table.rows` — const, line 106
- `const title = (index: number)` — const, line 107
- `const pairs: TakeTarget[] = []` — const, line 108
- `const claims = rows.map((row, index)` — const, line 114
- `const ctx = useCompareKeep()` — const, line 122
- `const allowed = ctx ? ("askId" in target ? ctx.settings.library || Boolean(table.kept) : ctx.settings.tutor) : false` — const, line 125
- `const targets = takeTargets(table)` — const, line 128
- `const comparisonId = table.comparisonId` — const, line 142
- `const pairs = relationPairs(table)` — const, line 143
- `const keep = async (withTake: boolean, noteText?: string): Promise<boolean>` — const, line 147
- `const chosen = targets.find((entry)` — const, line 148
- `const text = (noteText ?? take).trim()` — const, line 149
- `const takes = withTake && text && chosen ? [` — const, line 150
- `const result = await api.readerLibraryCompareKeep(` — const, line 154
- `const remove = async ()` — const, line 176
- `const ctx = useCompareKeep()` — const, line 270
- `const openSourceId = ctx?.openSourceId ?? null` — const, line 274
- `let cancelled = false` — let, line 276

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/reader/ComparePointTable|src/screens/reader/ComparePointTable.tsx]] — import-or-re-export: `KEEP_COPY`, `fineLabel`; references `KEEP_COPY`, `fineLabel`
- [[Reference/Desktop/TypeScript/screens/reader/CompareScope|src/screens/reader/CompareScope.tsx]] — import-or-re-export: `CompareKeep`; references `CompareKeep`
- [[Reference/Desktop/TypeScript/screens/reader/KeptMark|src/screens/reader/KeptMark.tsx]] — import-or-re-export: `KeptComparisonView`, `shortDate`; references `KeptComparisonView`, `shortDate`
- [[Reference/Desktop/TypeScript/screens/reader/LibraryAnswer|src/screens/reader/LibraryAnswer.tsx]] — import-or-re-export: `CompareKeep`, `KEEP_COPY`, `KeptComparisonView`, `shortDate`; references `CompareKeep`, `KEEP_COPY`, `KeptComparisonView`, `shortDate`
- [[Reference/Desktop/TypeScript/screens/reader/TutorOffers|src/screens/reader/TutorOffers.tsx]] — import-or-re-export: `CompareKeep`; references `CompareKeep`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CompareTableDto`, `KeptComparisonDto`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`
- [[Reference/Desktop/TypeScript/screens/reader/ReaderNotes|src/screens/reader/ReaderNotes.tsx]] — import-or-re-export; imports `NotesTakeBand`
- [[Reference/Desktop/TypeScript/screens/reader/compareKeepContext|src/screens/reader/compareKeepContext.ts]] — import-or-re-export; imports `useCompareKeep`
- [[Reference/Desktop/TypeScript/screens/reader/comparePoints|src/screens/reader/comparePoints.ts]] — import-or-re-export; imports `byPoint`
- [[Reference/Desktop/TypeScript/screens/reader/voices|src/screens/reader/voices.tsx]] — import-or-re-export; imports `LearnerVoice`, `MeaningLabel`, `ModelVoice`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

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

1. Modify [apps/learnloop-tauri/src/screens/reader/CompareKeep.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/CompareKeep.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
