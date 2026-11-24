---
title: "Desktop module · src/screens/desks/notebook/PadCell.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.notebook.PadCell"
language: "TypeScript"
area: "TypeScript/screens/desks/notebook"
source_path: "apps/learnloop-tauri/src/screens/desks/notebook/PadCell.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/notebook/PadCell.tsx"
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

# `src/screens/desks/notebook/PadCell.tsx`

Area: [[Reference/Desktop/TypeScript/screens/desks/notebook/_area|TypeScript/screens/desks/notebook]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `PadCell` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/notebook/PadCell.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/notebook/PadCell.tsx) |
| Source lines | 155 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/notebook/_area|TypeScript/screens/desks/notebook]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/pads/PadStackWindow|src/screens/desks/pads/PadStackWindow.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/notebook/PadCell|src/screens/desks/notebook/PadCell.tsx]]

## Public API

- `export const RUN_POLL =` — const, line 24
- `export const GROUP_HEIGHT_PX = 380` — const, line 26
- `export interface PadCellProps` — interface, line 28
- `export function PadCell(` — function, line 45

## Internal implementation anchors

- `function message(error: unknown): string` — function, line 39
- `const host = usePadsHost()` — const, line 46
- `const key = padNotebookKey(host?.store.clientId ?? "", padId)` — const, line 49
- `const state = useSyncExternalStore(subscribePadNotebooks, ()` — const, line 50
- `const area = useRef<HTMLTextAreaElement | null>(null)` — const, line 52
- `const shape = cellShape(blocks)` — const, line 53
- `const last = shape[shape.length - 1] === block.blockId` — const, line 54
- `const run = useCallback(async (code: string)` — const, line 60
- `const now = padNotebook(key)` — const, line 62
- `const name = now.names[block.blockId]` — const, line 70
- `const sessionId = now.session.sessionId` — const, line 78
- `const until = Date.now() + RUN_POLL.forMs` — const, line 79
- `const onKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>)` — const, line 90
- `const target = event.currentTarget` — const, line 104
- `const next = `$` — const, line 106
- `const tutor = block.provenance === "tutor"` — const, line 112

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/pads/PadStackWindow|src/screens/desks/pads/PadStackWindow.tsx]] — import-or-re-export: `PadCell`; references `PadCell`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `PadBlockDto`
- [[Reference/Desktop/TypeScript/screens/desks/notebook/NotebookFrame|src/screens/desks/notebook/NotebookFrame.tsx]] — import-or-re-export; imports `NotebookFrame`
- [[Reference/Desktop/TypeScript/screens/desks/notebook/padNotebooks|src/screens/desks/notebook/padNotebooks.ts]] — import-or-re-export; imports `cellShape`, `cellStateLine`, `needsOpen`, `notePadSession`, `noteRunPending`, `padNotebook`, `padNotebookKey`, `startPadNotebook`, `subscribePadNotebooks`
- [[Reference/Desktop/TypeScript/screens/desks/pads/host|src/screens/desks/pads/host.ts]] — import-or-re-export; imports `usePadsHost`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/notebook/PadCell.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/notebook/PadCell.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/notebook/PadCell.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/notebook/PadCell.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
