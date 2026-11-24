---
title: "Desktop module · src/screens/desks/checks/VeilLayer.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.checks.VeilLayer"
language: "TypeScript"
area: "TypeScript/screens/desks/checks"
source_path: "apps/learnloop-tauri/src/screens/desks/checks/VeilLayer.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/checks/VeilLayer.tsx"
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

# `src/screens/desks/checks/VeilLayer.tsx`

Area: [[Reference/Desktop/TypeScript/screens/desks/checks/_area|TypeScript/screens/desks/checks]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `VeilLayer` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/checks/VeilLayer.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/checks/VeilLayer.tsx) |
| Source lines | 156 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/checks/_area|TypeScript/screens/desks/checks]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/checks/VeilLayer|src/screens/desks/checks/VeilLayer.tsx]]

## Public API

- `export function applyVeils(root: ParentNode, veils: readonly CheckVeilRefDto[]): Pill[]` — function, line 55
- `export function VeilLayer(` — function, line 83

## Internal implementation anchors

- `const MARK = "ck-veiled"` — const, line 13
- `const UNVEIL_MS = 700` — const, line 14
- `interface Pill` — interface, line 16
- `const OCCLUDERS = "[data-companion-dock], [data-check-card='overlay'], [data-desk-search], .goalband"` — const, line 24
- `function placeOf(element: Element, root: ParentNode):` — function, line 28
- `const box = element.getBoundingClientRect()` — const, line 29
- `const frames = [element.parentElement?.closest("[data-desk-pane-body]"), element.closest("[data-desk-window]")] .filter((each): each is Element` — const, line 32
- `const left = Math.max(box.left, ...frames.map((f)` — const, line 35
- `const right = Math.min(box.right, ...frames.map((f)` — const, line 36
- `const top = Math.max(box.top, ...frames.map((f)` — const, line 37
- `const bottom = Math.min(box.bottom, ...frames.map((f)` — const, line 38
- `const at =` — const, line 40
- `const r = cover.getBoundingClientRect()` — const, line 43
- `function element0(wanted: Map<Element, CheckVeilRefDto>): Element | null` — function, line 49
- `const wanted = new Map<Element, CheckVeilRefDto>()` — const, line 56
- `const selector = veilSelector(ref)` — const, line 58
- `const pills: Pill[] = []` — const, line 69
- `const laidOut = (element0(wanted)?.ownerDocument.documentElement.getBoundingClientRect().width ?? 0) > 0` — const, line 70
- `const at = laidOut ? placeOf(element, root) :` — const, line 75
- `const veils = desk.veils()` — const, line 85
- `const veilsKey = veils.map(refKey).join("|")` — const, line 86
- `const frame = useRef(0)` — const, line 89
- `const current = useRef(veils)` — const, line 90
- `const changed = useRef(onChange)` — const, line 92
- `const run = ()` — const, line 97
- `const next = applyVeils(root, current.current)` — const, line 100
- `const schedule = ()` — const, line 105
- `const observer = new MutationObserver(()` — const, line 110

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `VeilLayer`; references `VeilLayer`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CheckVeilRefDto`
- [[Reference/Desktop/TypeScript/screens/desks/checks/controller|src/screens/desks/checks/controller.ts]] — import-or-re-export; imports `CheckDesk`
- [[Reference/Desktop/TypeScript/screens/desks/checks/model|src/screens/desks/checks/model.ts]] — import-or-re-export; imports `SHOW_ANYWAY_COST`, `SHOW_NOTE_COST`, `VEIL_LABEL`, `refKey`, `veilIsNote`, `veilSelector`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/checks/checks.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/checks/checks.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/checks/VeilLayer.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/checks/VeilLayer.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
