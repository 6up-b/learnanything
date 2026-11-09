---
title: "Desktop module · src/screens/reader/comparePoints.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.comparePoints"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/comparePoints.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/comparePoints.ts"
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

# `src/screens/reader/comparePoints.ts`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `RELATION_ORDER`, `CHIP_LABELS`, `RowChip`, `columnTitles` and related exports within the desktop's TypeScript/screens/reader ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/comparePoints.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/comparePoints.ts) |
| Source lines | 135 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/LibraryAnswer|src/screens/reader/LibraryAnswer.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/comparePoints|src/screens/reader/comparePoints.ts]]

## Public API

- `export const RELATION_ORDER = ["equivalent", "different_assumptions", "different_notation", "disagreement", "unclear"] as const` — const, line 17
- `export const CHIP_LABELS: Record<(typeof RELATION_ORDER)[number], string> =` — const, line 20
- `export type RowChip =` — type, line 28
- `export function columnTitles(table: CompareTableDto): Map<string, string>` — function, line 31
- `export function quotedKeys(point: ComparePointDto): string[]` — function, line 35
- `export function rowChips(point: ComparePointDto, titles: Map<string, string>): RowChip[]` — function, line 40
- `export function chipPairs(point: ComparePointDto): ComparePointRelationDto[]` — function, line 59
- `export function notFound(point: ComparePointDto): boolean` — function, line 68
- `export type CompareLayout = "by_point" | "by_book"` — type, line 72
- `export const LAYOUT_KEY = "ll.compare.layout"` — const, line 73
- `export function readLayout(): CompareLayout` — function, line 76
- `export function writeLayout(layout: CompareLayout): void` — function, line 84
- `export const POINT_COLUMN_PX = 190` — const, line 94
- `export const READABLE_CELL_PX = 220` — const, line 95
- `export const YOU_COLUMN_PX = 170` — const, line 96
- `export function cardsByPoint(paneWidth: number | null, windowWidth: number): boolean` — function, line 100
- `export interface CellPosition` — interface, line 105
- `export function moveCell(at: CellPosition, key: string, rows: number, cols: (row: number)` — function, line 112
- `export function byPoint(table: CompareTableDto): boolean` — function, line 133

## Internal implementation anchors

- `const quoted = quotedKeys(point)` — const, line 41
- `const returned = point.relations.map((relation)` — const, line 45
- `const pairsOnRow = (quoted.length * (quoted.length - 1)) / 2` — const, line 46
- `const chips: RowChip[] = []` — const, line 47
- `const count = returned.filter((value)` — const, line 49
- `const order = (relation: string)` — const, line 60
- `const at = (RELATION_ORDER as readonly string[]).indexOf(relation)` — const, line 61
- `const clampCol = (row: number, col: number)` — const, line 113

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/reader/CompareKeep|src/screens/reader/CompareKeep.tsx]] — import-or-re-export: `byPoint`; references `byPoint`
- [[Reference/Desktop/TypeScript/screens/reader/ComparePointTable|src/screens/reader/ComparePointTable.tsx]] — import-or-re-export: `CellPosition`, `CompareLayout`, `POINT_COLUMN_PX`, `READABLE_CELL_PX`, `YOU_COLUMN_PX`, `cardsByPoint`, `chipPairs`, `columnTitles`, `moveCell`, `notFound`, `readLayout`, `rowChips`, `writeLayout`; references `CellPosition`, `CompareLayout`, `POINT_COLUMN_PX`, `READABLE_CELL_PX`, `YOU_COLUMN_PX`, `cardsByPoint`, `chipPairs`, `columnTitles`, `moveCell`, `notFound`, `readLayout`, `rowChips`, `writeLayout`
- [[Reference/Desktop/TypeScript/screens/reader/LibraryAnswer|src/screens/reader/LibraryAnswer.tsx]] — import-or-re-export: `byPoint`; references `byPoint`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ComparePointDto`, `ComparePointRelationDto`, `CompareTableDto`
- [[Reference/Desktop/TypeScript/screens/workbench/splitWidth|src/screens/workbench/splitWidth.ts]] — import-or-re-export; imports `NARROW_BREAKPOINT`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/comparePointTable.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/comparePointTable.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

1. Modify [apps/learnloop-tauri/src/screens/reader/comparePoints.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/comparePoints.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
