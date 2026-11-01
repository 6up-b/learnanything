---
title: "Desktop module · src/screens/reader/cues.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.cues"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/cues.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/cues.ts"
source_commit: "758fec8241d0befbc095f69220952611b05e419b"
source_commit_timestamp: "2026-10-20T15:05:02-04:00"
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

# `src/screens/reader/cues.ts`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `CUE_DENSITIES`, `DENSITY_BUDGET`, `stepDown`, `CUE_COPY` and related exports within the desktop's TypeScript/screens/reader ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/cues.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/cues.ts) |
| Source lines | 232 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `758fec8241d0befbc095f69220952611b05e419b` |
| Commit timestamp | `2026-10-20T15:05:02-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/cues|src/screens/reader/cues.ts]]

## Public API

- `export const CUE_DENSITIES: readonly CueDensity[] = ["off", "fewer", "normal", "more"]` — const, line 19
- `export const DENSITY_BUDGET: Readonly<Record<CueDensity, number>> =` — const, line 22
- `export function stepDown(density: CueDensity): CueDensity` — function, line 25
- `export const CUE_COPY =` — const, line 31
- `export const DISCOVERED_COPY =` — const, line 75
- `export function markClass(cue: ReaderCueDto): string` — function, line 94
- `export type CueSuppression = "skim" | "working" | "restored_line" | "spacing" | "no_place"` — type, line 100
- `export interface CuePlacementInput` — interface, line 102
- `export interface CuePlacement` — interface, line 125
- `export function placeCueMarks(input: CuePlacementInput): CuePlacement` — function, line 136
- `export function stepMark(count: number, fromIndex: number, direction: 1 | -1): number | null` — function, line 174
- `export const PDF_PAGE_GAP_PX = 14` — const, line 182
- `export const PDF_LEFT_OUT_LINE_PX = 28` — const, line 185
- `export interface PdfPageSize` — interface, line 189
- `export interface PdfPageLayout` — interface, line 201
- `export function pdfPageTops(layout: PdfPageLayout): Map<number,` — function, line 209
- `export function pdfPassageTop( tops: ReadonlyMap<number,` — function, line 225

## Internal implementation anchors

- `const index = CUE_DENSITIES.indexOf(density)` — const, line 26
- `const withheld = new Set((input.heldOut ?? []).map((cue)` — const, line 137
- `const ranked = [...input.marks, ...(input.heldOut ?? [])].sort((a, b)` — const, line 138
- `const split = (placement: CuePlacement): CuePlacement` — const, line 139
- `const placed: Array<` — const, line 150
- `const suppressed: CuePlacement["suppressed"] = []` — const, line 151
- `const y = input.positionOf(cue.spanId)` — const, line 157
- `const next = fromIndex + direction` — const, line 176
- `const tops = new Map<number,` — const, line 210
- `let top = 0` — let, line 211
- `const scale = entry.widthPoints > 0 ? layout.widthPx / entry.widthPoints : 0` — const, line 215
- `const entry = tops.get(page)` — const, line 230

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/PdfReaderPane|src/components/PdfReaderPane.tsx]] — import-or-re-export: `PdfPageLayout`; references `PdfPageLayout`
- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `PdfPageLayout`; references `PdfPageLayout`
- [[Reference/Desktop/TypeScript/screens/reader/MarginMark|src/screens/reader/MarginMark.tsx]] — import-or-re-export: `CUE_COPY`, `CUE_DENSITIES`, `DISCOVERED_COPY`, `markClass`; references `CUE_COPY`, `CUE_DENSITIES`, `DISCOVERED_COPY`, `markClass`
- [[Reference/Desktop/TypeScript/screens/reader/ReaderCueSettings|src/screens/reader/ReaderCueSettings.tsx]] — import-or-re-export: `CUE_COPY`, `CUE_DENSITIES`; references `CUE_COPY`, `CUE_DENSITIES`
- [[Reference/Desktop/TypeScript/screens/reader/useCueImpressions|src/screens/reader/useCueImpressions.ts]] — import-or-re-export: `CuePlacement`; references `CuePlacement`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderCues|src/screens/reader/useReaderCues.ts]] — import-or-re-export: `CUE_COPY`, `CuePlacement`, `CueSuppression`, `PdfPageLayout`, `pdfPageTops`, `pdfPassageTop`, `placeCueMarks`, `stepDown`, `stepMark`; references `CUE_COPY`, `CuePlacement`, `CueSuppression`, `PdfPageLayout`, `pdfPageTops`, `pdfPassageTop`, `placeCueMarks`, `stepDown`, `stepMark`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CueDensity`, `ReaderCueDto`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/rw3bReview.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/rw3bReview.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/cues.test.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/cues.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/PdfReaderPane.marks.test.tsx](../../../../../../../apps/learnloop-tauri/src/components/PdfReaderPane.marks.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

1. Modify [apps/learnloop-tauri/src/screens/reader/cues.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/cues.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
