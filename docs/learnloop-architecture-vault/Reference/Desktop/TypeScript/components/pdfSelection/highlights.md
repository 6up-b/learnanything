---
title: "Desktop module · src/components/pdfSelection/highlights.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.pdfSelection.highlights"
language: "TypeScript"
area: "TypeScript/components/pdfSelection"
source_path: "apps/learnloop-tauri/src/components/pdfSelection/highlights.ts"
source_paths:
  - "apps/learnloop-tauri/src/components/pdfSelection/highlights.ts"
source_commit: "e2916ff0e7ba40841036aa11af2f95256708db50"
source_commit_timestamp: "2026-10-15T20:38:52-04:00"
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

# `src/components/pdfSelection/highlights.ts`

Area: [[Reference/Desktop/TypeScript/components/pdfSelection/_area|TypeScript/components/pdfSelection]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides shared `highlights` state or utility behavior for desktop components.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/pdfSelection/highlights.ts](../../../../../../../apps/learnloop-tauri/src/components/pdfSelection/highlights.ts) |
| Source lines | 176 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/pdfSelection/_area|TypeScript/components/pdfSelection]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `e2916ff0e7ba40841036aa11af2f95256708db50` |
| Commit timestamp | `2026-10-15T20:38:52-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/components/pdfSelection/highlights|src/components/pdfSelection/highlights.ts]]

## Public API

- `export type HighlightState = "here" | "moved" | "flagged"` — type, line 16
- `export interface PdfHighlight` — interface, line 18
- `export interface PlacedHighlight extends PdfHighlight` — interface, line 31
- `export function highlightFromPlacement( base:` — function, line 40
- `export function placeHighlights(model: SelectionModel, highlights: readonly PdfHighlight[]): PlacedHighlight[]` — function, line 59
- `export interface HighlightOnPage` — interface, line 76
- `export function highlightsOnPage(model: SelectionModel, placed: readonly PlacedHighlight[], page: number): HighlightOnPage[]` — function, line 90
- `export function chipRect(entry: Pick<HighlightOnPage, "rects">, at:` — function, line 109
- `export function highlightAt(onPage: readonly HighlightOnPage[], x: number, y: number): string | null` — function, line 128
- `export function kindLabel(kind: string): string` — function, line 153
- `export function stateLabel(state: HighlightState): string | null` — function, line 158
- `export function highlightAriaLabel(highlight: Pick<PdfHighlight, "kind" | "state" | "quote" | "note">, continued = false): string` — function, line 166

## Internal implementation anchors

- `const placed: PlacedHighlight[] = []` — const, line 60
- `const flagBlock = highlight.flagSpanId ? model.blockIndex(highlight.flagSpanId) ?? null : null` — const, line 63
- `const ranges = highlight.segments.flatMap((segment)` — const, line 67
- `const range = anchorRange(model, segment.spanId, segment.start, segment.end)` — const, line 68
- `const out: HighlightOnPage[] = []` — const, line 91
- `const block = model.blocks[highlight.flagBlock]` — const, line 94
- `const rects = rangeRects(model, highlight.ranges, page)` — const, line 98
- `const first = highlight.ranges.reduce((lo, range)` — const, line 100
- `let best = entry.rects[0]` — let, line 112
- `let bestDistance = Infinity` — let, line 113
- `const dx = at.x < rect[0] ? rect[0] - at.x : at.x > rect[2] ? at.x - rect[2] : 0` — const, line 115
- `const dy = at.y < rect[1] ? rect[1] - at.y : at.y > rect[3] ? at.y - rect[3] : 0` — const, line 116
- `const distance = Math.hypot(dx, dy)` — const, line 117
- `const entry = onPage[index]` — const, line 130
- `const tolerance = entry.state === "flagged" ? 0 : 1` — const, line 131
- `const KIND_LABELS: Record<string, string> =` — const, line 139
- `const quote = highlight.quote.replace(/\s+/g, " ").trim()` — const, line 167
- `const clipped = quote.length > 80 ? `$` — const, line 168
- `const parts = [continued ? `$` — const, line 169
- `const state = stateLabel(highlight.state)` — const, line 171

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/PdfReaderPane|src/components/PdfReaderPane.tsx]] — import-or-re-export: `HighlightOnPage`, `PdfHighlight`, `highlightAt`, `highlightsOnPage`, `placeHighlights`; references `HighlightOnPage`, `PdfHighlight`, `highlightAt`, `highlightsOnPage`, `placeHighlights`
- [[Reference/Desktop/TypeScript/components/pdfSelection/PdfSelectionLayer|src/components/pdfSelection/PdfSelectionLayer.tsx]] — import-or-re-export: `HighlightOnPage`, `PdfHighlight`, `chipRect`, `highlightAriaLabel`, `kindLabel`, `stateLabel`; references `HighlightOnPage`, `PdfHighlight`, `chipRect`, `highlightAriaLabel`, `kindLabel`, `stateLabel`
- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `PdfHighlight`, `highlightFromPlacement`, `kindLabel`; references `PdfHighlight`, `highlightFromPlacement`, `kindLabel`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ReaderAnnotationPlacementDto`
- [[Reference/Desktop/TypeScript/components/pdfSelection/model|src/components/pdfSelection/model.ts]] — import-or-re-export; imports `Box`, `SelRange`, `SelectionModel`, `anchorRange`, `rangeRects`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/ReaderScreen.pdfSelection.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/ReaderScreen.pdfSelection.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/PdfReaderPane.selection.test.tsx](../../../../../../../apps/learnloop-tauri/src/components/PdfReaderPane.selection.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

1. Modify [apps/learnloop-tauri/src/components/pdfSelection/highlights.ts](../../../../../../../apps/learnloop-tauri/src/components/pdfSelection/highlights.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
