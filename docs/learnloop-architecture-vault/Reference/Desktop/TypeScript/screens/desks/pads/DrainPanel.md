---
title: "Desktop module · src/screens/desks/pads/DrainPanel.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.pads.DrainPanel"
language: "TypeScript"
area: "TypeScript/screens/desks/pads"
source_path: "apps/learnloop-tauri/src/screens/desks/pads/DrainPanel.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/pads/DrainPanel.tsx"
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

# `src/screens/desks/pads/DrainPanel.tsx`

Area: [[Reference/Desktop/TypeScript/screens/desks/pads/_area|TypeScript/screens/desks/pads]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `DrainPanel` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/pads/DrainPanel.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pads/DrainPanel.tsx) |
| Source lines | 106 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/pads/_area|TypeScript/screens/desks/pads]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/pads/DrainPanel|src/screens/desks/pads/DrainPanel.tsx]]

## Public API

- `export interface DrainActions` — interface, line 9
- `export function DrainPanel(` — function, line 15

## Internal implementation anchors

- `const pending = useRef<number | null>(null)` — const, line 28
- `let live = true` — let, line 30
- `const onKey = (event: KeyboardEvent)` — const, line 37
- `const match = /^([1-9])$/.exec(event.key)` — const, line 46
- `const index = pending.current` — const, line 52
- `const pad = index !== null ? drain?.pads[index] : drain?.pads.length === 1 ? drain.pads[0] : undefined` — const, line 53
- `const act = (padId: string, said: string, run: ()` — const, line 66
- `const next =` — const, line 70
- `const next =` — const, line 78

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `DrainPanel`; references `DrainPanel`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `PadDrainDto`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- No repository test directly names this source path or a uniquely owned export. `npm run typecheck`, `npm test` and `npm run frontend:build` are the executable frontend gates; add a focused test when changing behavior.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/pads/DrainPanel.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pads/DrainPanel.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
