---
title: "Desktop module · src/screens/desks/menu/KnowsPanel.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.menu.KnowsPanel"
language: "TypeScript"
area: "TypeScript/screens/desks/menu"
source_path: "apps/learnloop-tauri/src/screens/desks/menu/KnowsPanel.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/menu/KnowsPanel.tsx"
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

# `src/screens/desks/menu/KnowsPanel.tsx`

Area: [[Reference/Desktop/TypeScript/screens/desks/menu/_area|TypeScript/screens/desks/menu]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `KnowsPanel` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/menu/KnowsPanel.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/menu/KnowsPanel.tsx) |
| Source lines | 84 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/menu/_area|TypeScript/screens/desks/menu]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/menu/KnowsPanel|src/screens/desks/menu/KnowsPanel.tsx]]

## Public API

- `export interface KnowsActions` — interface, line 7
- `export function knowsGroups(place: PassageUnionSpanDto, actions: KnowsActions): Array<` — function, line 23
- `export function KnowsPanel(` — function, line 38

## Internal implementation anchors

- `function quality(alias: string): string` — function, line 13
- `function day(at: string | null | undefined): string` — function, line 17
- `const date = new Date(at)` — const, line 19
- `const groups: Array<` — const, line 24
- `let live = true` — let, line 47
- `const groups = knowsGroups(place.knows, actions)` — const, line 64

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `KnowsPanel`; references `KnowsPanel`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `MenuObjectInput`, `PassageKnowsDto`, `PassageUnionSpanDto`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/menu/KnowsPanel.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/menu/KnowsPanel.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/menu/KnowsPanel.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/menu/KnowsPanel.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
