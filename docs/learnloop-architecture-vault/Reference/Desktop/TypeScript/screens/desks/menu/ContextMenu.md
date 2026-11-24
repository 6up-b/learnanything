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
| Source lines | 353 |
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
- `export function useSheetFocus(ref:` — function, line 68
- `export function ContextMenu(` — function, line 93

## Internal implementation anchors

- `function newRequestId(): string` — function, line 56
- `const random = typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : `$` — const, line 57
- `const PAGE_LISTEN = (target: "window", type: string, handler: (event: Event)` — const, line 61
- `const escape = useRef(onEscape)` — const, line 69
- `const before = document.activeElement as HTMLElement | null` — const, line 72
- `const node = ref.current` — const, line 73
- `const field = node.querySelector<HTMLElement>("textarea, input, select")` — const, line 75
- `const onKey = (event: KeyboardEvent)` — const, line 78
- `const menuRef = useRef<HTMLDivElement | null>(null)` — const, line 107
- `const appendRef = useRef<HTMLButtonElement | null>(null)` — const, line 108
- `const before = document.activeElement as HTMLElement | null` — const, line 111
- `const objectKey = object ? JSON.stringify(object) : ""` — const, line 119
- `const promotedNow = useRef(promoted)` — const, line 122
- `const onRowsNow = useRef(onRows)` — const, line 124
- `const onWithheldNow = useRef(onWithheld)` — const, line 126
- `const hasPromoted = promoted !== null` — const, line 128
- `const promoted = promotedNow.current` — const, line 130
- `let live = true` — let, line 132
- `let jobId: string | null = null` — let, line 133
- `let finished = false` — let, line 134
- `let stop: (()` — let, line 135
- `let requestId = newRequestId()` — let, line 137
- `const ask = (): Promise<PassagePromotedDto>` — const, line 138
- `const code = error && typeof error === "object" ? (error as` — const, line 139
- `const promotedRows: MenuRow[] = shownPromoted(cheap, dismissed).map((row)` — const, line 200
- `const all = [...promotedRows, ...rows]` — const, line 208
- `const runnable = all.filter((row)` — const, line 209
- `const menu = menuRef.current` — const, line 213
- `const box = menu.getBoundingClientRect()` — const, line 215
- `const openSubmenu = ()` — const, line 219
- `const row = appendRef.current?.getBoundingClientRect()` — const, line 220
- `const dismiss = (row: PromotedRowDto, label: "dismiss" | "not_this")` — const, line 227
- `const onKey = (event: KeyboardEvent)` — const, line 234
- `const current = runnable[Math.min(index, runnable.length - 1)]` — const, line 237
- `const count = append.pads.length + 1` — const, line 240
- `const row = runnable.find((each)` — const, line 260
- `const onDown = (event: MouseEvent)` — const, line 268
- `const offs = [listen("window", "keydown", onKey as (event: Event)` — const, line 271
- `const rowView = (row: MenuRow)` — const, line 277
- `const at = runnable.indexOf(row)` — const, line 278
- `const selected = at >= 0 && at === Math.min(index, runnable.length - 1)` — const, line 279
- `const verbs = rows.filter((row)` — const, line 311
- `const inserts = rows.filter((row)` — const, line 312
- `const tail = rows.filter((row)` — const, line 313

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `ContextMenu`, `PromotedApi`, `useSheetFocus`; references `ContextMenu`, `PromotedApi`, `useSheetFocus`
- [[Reference/Desktop/TypeScript/screens/desks/menu/ExerciseSheet|src/screens/desks/menu/ExerciseSheet.tsx]] — import-or-re-export: `useSheetFocus`; references `useSheetFocus`
- [[Reference/Desktop/TypeScript/screens/desks/menu/KnowsPanel|src/screens/desks/menu/KnowsPanel.tsx]] — import-or-re-export: `useSheetFocus`; references `useSheetFocus`
- [[Reference/Desktop/TypeScript/screens/desks/pads/PadOverlays|src/screens/desks/pads/PadOverlays.tsx]] — import-or-re-export: `ContextMenu`, `useSheetFocus`; references `ContextMenu`, `useSheetFocus`
- [[Reference/Desktop/TypeScript/screens/desks/pads/host|src/screens/desks/pads/host.ts]] — import-or-re-export: `PromotedApi`; references `PromotedApi`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `MenuObjectInput`, `PassagePromotedDto`, `PassagePromotedInput`, `PromotedJobDto`, `PromotedRowDto`, `ProposalLabel`
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
