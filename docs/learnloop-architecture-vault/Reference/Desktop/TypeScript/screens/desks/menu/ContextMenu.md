---
title: "Desktop module · src/screens/desks/menu/ContextMenu.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.menu.ContextMenu"
language: "TypeScript"
area: "TypeScript/screens/desks/menu"
source_path: "apps/learnloop-tauri/src/screens/desks/menu/ContextMenu.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/menu/ContextMenu.tsx"
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

# `src/screens/desks/menu/ContextMenu.tsx`

Area: [[Reference/Desktop/TypeScript/screens/desks/menu/_area|TypeScript/screens/desks/menu]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `ContextMenu` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/menu/ContextMenu.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/menu/ContextMenu.tsx) |
| Source lines | 253 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/menu/_area|TypeScript/screens/desks/menu]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/menu/ContextMenu|src/screens/desks/menu/ContextMenu.tsx]]

## Public API

- `export interface PromotedApi` — interface, line 13
- `export interface AppendTargets` — interface, line 20
- `export interface ContextMenuProps` — interface, line 26
- `export function ContextMenu(` — function, line 55

## Internal implementation anchors

- `const PAGE_LISTEN = (target: "window", type: string, handler: (event: Event)` — const, line 50
- `const menuRef = useRef<HTMLDivElement | null>(null)` — const, line 63
- `const appendRef = useRef<HTMLButtonElement | null>(null)` — const, line 64
- `const objectKey = object ? JSON.stringify(object) : ""` — const, line 68
- `const promotedNow = useRef(promoted)` — const, line 71
- `const hasPromoted = promoted !== null` — const, line 73
- `const promoted = promotedNow.current` — const, line 75
- `let live = true` — let, line 77
- `let jobId: string | null = null` — let, line 78
- `let finished = false` — let, line 79
- `let stop: (()` — let, line 80
- `const promotedRows: MenuRow[] = shownPromoted(cheap, dismissed).map((row)` — const, line 115
- `const all = [...promotedRows, ...rows]` — const, line 123
- `const runnable = all.filter((row)` — const, line 124
- `const menu = menuRef.current` — const, line 128
- `const box = menu.getBoundingClientRect()` — const, line 130
- `const openSubmenu = ()` — const, line 134
- `const row = appendRef.current?.getBoundingClientRect()` — const, line 135
- `const dismiss = (row: PromotedRowDto, label: "dismiss" | "not_this")` — const, line 141
- `const onKey = (event: KeyboardEvent)` — const, line 148
- `const current = runnable[Math.min(index, runnable.length - 1)]` — const, line 151
- `const row = runnable.find((each)` — const, line 162
- `const onDown = (event: MouseEvent)` — const, line 170
- `const offs = [listen("window", "keydown", onKey as (event: Event)` — const, line 173
- `const rowView = (row: MenuRow)` — const, line 179
- `const at = runnable.indexOf(row)` — const, line 180
- `const selected = at >= 0 && at === Math.min(index, runnable.length - 1)` — const, line 181
- `const verbs = rows.filter((row)` — const, line 213
- `const inserts = rows.filter((row)` — const, line 214
- `const tail = rows.filter((row)` — const, line 215

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `ContextMenu`, `PromotedApi`; references `ContextMenu`, `PromotedApi`
- [[Reference/Desktop/TypeScript/screens/desks/pads/PadOverlays|src/screens/desks/pads/PadOverlays.tsx]] — import-or-re-export: `ContextMenu`; references `ContextMenu`
- [[Reference/Desktop/TypeScript/screens/desks/pads/host|src/screens/desks/pads/host.ts]] — import-or-re-export: `PromotedApi`; references `PromotedApi`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `MenuObjectInput`, `PassagePromotedDto`, `PromotedJobDto`, `PromotedRowDto`, `ProposalLabel`
- [[Reference/Desktop/TypeScript/api/poller|src/api/poller.ts]] — import-or-re-export; imports `Poller`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/screens/desks/menu/model|src/screens/desks/menu/model.ts]] — import-or-re-export; imports `MENU_SIZES`, `MenuRow`, `placeMenu`, `placeSubmenu`, `promotedReason`, `shownPromoted`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/menu/ContextMenu.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/menu/ContextMenu.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/menu/ContextMenu.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/menu/ContextMenu.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
