---
title: "Desktop module · src/screens/desks/pads/host.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.pads.host"
language: "TypeScript"
area: "TypeScript/screens/desks/pads"
source_path: "apps/learnloop-tauri/src/screens/desks/pads/host.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/pads/host.ts"
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

# `src/screens/desks/pads/host.ts`

Area: [[Reference/Desktop/TypeScript/screens/desks/pads/_area|TypeScript/screens/desks/pads]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `PadsApi`, `SourcePiece`, `PadsHost`, `PadStackHandle` and related exports within the desktop's TypeScript/screens/desks/pads ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/pads/host.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pads/host.ts) |
| Source lines | 177 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/pads/_area|TypeScript/screens/desks/pads]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/pads/host|src/screens/desks/pads/host.ts]]

## Public API

- `export interface PadsApi` — interface, line 27
- `export interface SourcePiece` — interface, line 47
- `export interface PadsHost` — interface, line 56
- `export interface PadStackHandle` — interface, line 101
- `export interface PendingFigure` — interface, line 123
- `export class PendingFigures` — class, line 133
- `export const PadsHostContext = createContext<PadsHost | null>(null)` — const, line 159
- `export function usePadsHost(): PadsHost | null` — function, line 161
- `export function localDay(date: Date = new Date()): string` — function, line 166
- `export function dayHeading(day: string, today: string): string` — function, line 172

## Internal implementation anchors

- `const waiting = this.byWindow.get(windowId) ?? []` — const, line 153
- `const pad = (n: number)` — const, line 167
- `const date = new Date(`$` — const, line 173
- `const label = date.toLocaleDateString("en-GB",` — const, line 175

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/fixtures/desks/harness|src/fixtures/desks/harness.tsx]] — import-or-re-export: `PadsHost`, `PadsHostContext`, `PendingFigures`; references `PadsHost`, `PadsHostContext`, `PendingFigures`
- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `PadStackHandle`, `PadsApi`, `PadsHost`, `PadsHostContext`, `PendingFigures`, `SourcePiece`, `localDay`; references `PadStackHandle`, `PadsApi`, `PadsHost`, `PadsHostContext`, `PendingFigures`, `SourcePiece`, `localDay`
- [[Reference/Desktop/TypeScript/screens/desks/notebook/PadCell|src/screens/desks/notebook/PadCell.tsx]] — import-or-re-export: `usePadsHost`; references `usePadsHost`
- [[Reference/Desktop/TypeScript/screens/desks/pads/PadOverlays|src/screens/desks/pads/PadOverlays.tsx]] — import-or-re-export: `PadsHost`; references `PadsHost`
- [[Reference/Desktop/TypeScript/screens/desks/pads/PadStackWindow|src/screens/desks/pads/PadStackWindow.tsx]] — import-or-re-export: `PadStackHandle`, `PadsHost`, `dayHeading`, `usePadsHost`; references `PadStackHandle`, `PadsHost`, `dayHeading`, `usePadsHost`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CarriedQuestionDto`, `CarryInput`, `MenuObjectInput`, `PadProposalsDto`, `PadSubmitBlockDto`, `PadSubmitBlockInput`, `PassageContentDto`, `PassageUnionDto`, `PassageUnionInput`, `PromotedRowDto`, `ProposalLabelInput`, `SessionSnapshot`, `SubmitTeachBackTurnInput`, `TeachBackTurnResult`
- [[Reference/Desktop/TypeScript/api/poller|src/api/poller.ts]] — import-or-re-export; imports `Poller`
- [[Reference/Desktop/TypeScript/screens/desks/lesson/host|src/screens/desks/lesson/host.ts]] — import-or-re-export; imports `LessonsHost`
- [[Reference/Desktop/TypeScript/screens/desks/menu/ContextMenu|src/screens/desks/menu/ContextMenu.tsx]] — import-or-re-export; imports `PromotedApi`
- [[Reference/Desktop/TypeScript/screens/desks/notebook/menuBridge|src/screens/desks/notebook/menuBridge.ts]] — import-or-re-export; imports `NotebookMenuRequest`
- [[Reference/Desktop/TypeScript/screens/desks/problem/ProblemPad|src/screens/desks/problem/ProblemPad.tsx]] — import-or-re-export; imports `ProblemHost`
- [[Reference/Desktop/TypeScript/screens/desks/search/model|src/screens/desks/search/model.ts]] — import-or-re-export; imports `SearchRow`
- [[Reference/Desktop/TypeScript/screens/desks/store|src/screens/desks/store.ts]] — import-or-re-export; imports `DeskStore`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/pen/inkPad.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pen/inkPad.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/pads/PadStackWindow.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pads/PadStackWindow.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/notebook/PadCell.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/notebook/PadCell.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/lesson/lessonWindows.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/lesson/lessonWindows.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/DeskShell.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/DeskShell.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/DeskShell.menu.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/DeskShell.menu.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/pads/host.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pads/host.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
