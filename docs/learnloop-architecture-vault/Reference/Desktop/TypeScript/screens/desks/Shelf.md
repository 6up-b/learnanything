---
title: "Desktop module · src/screens/desks/Shelf.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.Shelf"
language: "TypeScript"
area: "TypeScript/screens/desks"
source_path: "apps/learnloop-tauri/src/screens/desks/Shelf.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/Shelf.tsx"
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

# `src/screens/desks/Shelf.tsx`

Area: [[Reference/Desktop/TypeScript/screens/desks/_area|TypeScript/screens/desks]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `Shelf` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/Shelf.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/Shelf.tsx) |
| Source lines | 276 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/_area|TypeScript/screens/desks]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/Shelf|src/screens/desks/Shelf.tsx]]

## Public API

- `export interface ShelfRow` — interface, line 7
- `export function Shelf(` — function, line 25
- `export function CarriedList(` — function, line 221

## Internal implementation anchors

- `const DRAG_THRESHOLD_PX = 5` — const, line 23
- `const setOpen = (next: boolean)` — const, line 60
- `const body = ( <> <ShelfBody rows=` — const, line 68
- `function ShelfBody(` — function, line 104
- `const press = useRef<` — const, line 119
- `const listRef = useRef<HTMLDivElement | null>(null)` — const, line 120
- `const slotAt = (clientY: number): number` — const, line 123
- `const list = listRef.current` — const, line 124
- `const items = [...list.querySelectorAll<HTMLElement>("[data-shelf-slot]")]` — const, line 126
- `let target = 0` — let, line 127
- `const box = item.getBoundingClientRect()` — const, line 129
- `const onPointerDown = (row: ShelfRow)` — const, line 135
- `const onPointerMove = (event: ReactPointerEvent<HTMLButtonElement>)` — const, line 138
- `const current = press.current` — const, line 139
- `const onPointerUp = (row: ShelfRow)` — const, line 147
- `const current = press.current` — const, line 148
- `const to = slotAt(event.clientY)` — const, line 152
- `const read = (at?: string)` — const, line 230
- `const base = at ? now ?? [] : []` — const, line 234
- `const label = (question: CarriedQuestionDto, event: "fruitful" | "not_now" | "let_go")` — const, line 246

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `CarriedList`, `Shelf`, `ShelfRow`; references `CarriedList`, `Shelf`, `ShelfRow`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CarriedQuestionDto`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/goal/shelf.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/goal/shelf.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/Shelf.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/Shelf.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
