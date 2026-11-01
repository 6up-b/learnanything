---
title: "Desktop module · src/components/pdfSelection/PdfSelectionLayer.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.pdfSelection.PdfSelectionLayer"
language: "TypeScript"
area: "TypeScript/components/pdfSelection"
source_path: "apps/learnloop-tauri/src/components/pdfSelection/PdfSelectionLayer.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/pdfSelection/PdfSelectionLayer.tsx"
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

# `src/components/pdfSelection/PdfSelectionLayer.tsx`

Area: [[Reference/Desktop/TypeScript/components/pdfSelection/_area|TypeScript/components/pdfSelection]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `PdfSelectionLayer` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/pdfSelection/PdfSelectionLayer.tsx](../../../../../../../apps/learnloop-tauri/src/components/pdfSelection/PdfSelectionLayer.tsx) |
| Source lines | 235 |
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
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/components/PdfReaderPane|src/components/PdfReaderPane.tsx]] → [[Reference/Desktop/TypeScript/components/pdfSelection/PdfSelectionLayer|src/components/pdfSelection/PdfSelectionLayer.tsx]]

## Public API

- `export interface PdfSelectionLayerProps` — interface, line 21
- `export const PdfSelectionLayer = memo(function PdfSelectionLayer(` — const, line 57

## Internal implementation anchors

- `const WASH: Record<"highlight" | "other",` — const, line 15
- `const SELECTION_WASH = "rgba(64, 132, 214, 0.28)"` — const, line 19
- `function boxStyle(rect: readonly number[], scale: number, pad = 0)` — function, line 46
- `const onStopKey = (id: string)` — const, line 73
- `const tone = WASH[entry.kind === "highlight" ? "highlight" : "other"]` — const, line 91
- `const lit = entry.id === hovered || entry.id === active` — const, line 92
- `const detail = details.get(entry.id)` — const, line 160
- `const first = entry.rects[0]` — const, line 161
- `const entry = chip ? highlights.find((candidate)` — const, line 182
- `const detail = entry ? details.get(entry.id) : undefined` — const, line 183
- `const first = entry ? chipRect(entry, chip?.at ?? null) : null` — const, line 184
- `const state = stateLabel(entry.state)` — const, line 186
- `const note = detail.note.trim()` — const, line 187

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/PdfReaderPane|src/components/PdfReaderPane.tsx]] — import-or-re-export: `PdfSelectionLayer`; references `PdfSelectionLayer`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/components/pdfSelection/highlights|src/components/pdfSelection/highlights.ts]] — import-or-re-export; imports `HighlightOnPage`, `PdfHighlight`, `chipRect`, `highlightAriaLabel`, `kindLabel`, `stateLabel`
- [[Reference/Desktop/TypeScript/components/pdfSelection/model|src/components/pdfSelection/model.ts]] — import-or-re-export; imports `Box`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- No repository test directly names this source path or a uniquely owned export. `npm run typecheck`, `npm test` and `npm run frontend:build` are the executable frontend gates; add a focused test when changing behavior.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/pdfSelection/PdfSelectionLayer.tsx](../../../../../../../apps/learnloop-tauri/src/components/pdfSelection/PdfSelectionLayer.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
