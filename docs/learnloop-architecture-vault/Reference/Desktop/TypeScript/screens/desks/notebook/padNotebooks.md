---
title: "Desktop module · src/screens/desks/notebook/padNotebooks.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.notebook.padNotebooks"
language: "TypeScript"
area: "TypeScript/screens/desks/notebook"
source_path: "apps/learnloop-tauri/src/screens/desks/notebook/padNotebooks.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/notebook/padNotebooks.ts"
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

# `src/screens/desks/notebook/padNotebooks.ts`

Area: [[Reference/Desktop/TypeScript/screens/desks/notebook/_area|TypeScript/screens/desks/notebook]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `PadNotebook`, `padNotebookKey`, `padNotebook`, `subscribePadNotebooks` and related exports within the desktop's TypeScript/screens/desks/notebook ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/notebook/padNotebooks.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/notebook/padNotebooks.ts) |
| Source lines | 117 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/notebook/_area|TypeScript/screens/desks/notebook]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/pads/PadStackWindow|src/screens/desks/pads/PadStackWindow.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/notebook/PadCell|src/screens/desks/notebook/PadCell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/notebook/padNotebooks|src/screens/desks/notebook/padNotebooks.ts]]

## Public API

- `export interface PadNotebook` — interface, line 15
- `export function padNotebookKey(vaultScope: string, padId: string): string` — function, line 39
- `export function padNotebook(padId: string): PadNotebook` — function, line 43
- `export function subscribePadNotebooks(listener: ()` — function, line 52
- `export function cellShape(blocks:` — function, line 58
- `export function needsOpen(state: PadNotebook, shape: string[]): boolean` — function, line 64
- `export function startPadNotebook(padId: string, shape: string[]): void` — function, line 70
- `export function notePadSession(padId: string, session: NotebookSessionDto): void` — function, line 76
- `export function noteRunPending(padId: string, blockId: string, error: string | null = null): void` — function, line 88
- `export function cellRun(state: PadNotebook, blockId: string): NotebookCellRunDto | null` — function, line 93
- `export function cellStateLine(state: PadNotebook, blockId: string): string` — function, line 99
- `export function resetPadNotebooksForTests(): void` — function, line 114

## Internal implementation anchors

- `const EMPTY: PadNotebook =` — const, line 30
- `const pads = new Map<string, PadNotebook>()` — const, line 31
- `const listeners = new Set<()` — const, line 32
- `function emit(): void` — function, line 34
- `function update(padId: string, change: (now: PadNotebook)` — function, line 47
- `const session = state.session` — const, line 65
- `const names = session.padCells ?? now.names` — const, line 78
- `const pending =` — const, line 79
- `const run = session.cellRuns?.[name]` — const, line 81
- `const name = state.names[blockId]` — const, line 94
- `const session = state.session` — const, line 102
- `const run = cellRun(state, blockId)` — const, line 106

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/notebook/PadCell|src/screens/desks/notebook/PadCell.tsx]] — import-or-re-export: `cellShape`, `cellStateLine`, `needsOpen`, `notePadSession`, `noteRunPending`, `padNotebook`, `padNotebookKey`, `startPadNotebook`, `subscribePadNotebooks`; references `cellShape`, `cellStateLine`, `needsOpen`, `notePadSession`, `noteRunPending`, `padNotebook`, `padNotebookKey`, `startPadNotebook`, `subscribePadNotebooks`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `NotebookCellRunDto`, `NotebookSessionDto`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/notebook/padNotebooks.test.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/notebook/padNotebooks.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/notebook/PadCell.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/notebook/PadCell.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/notebook/padNotebooks.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/notebook/padNotebooks.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
