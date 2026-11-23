---
title: "Desktop module · src/screens/desks/pads/PassageMarks.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.pads.PassageMarks"
language: "TypeScript"
area: "TypeScript/screens/desks/pads"
source_path: "apps/learnloop-tauri/src/screens/desks/pads/PassageMarks.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/pads/PassageMarks.tsx"
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

# `src/screens/desks/pads/PassageMarks.tsx`

Area: [[Reference/Desktop/TypeScript/screens/desks/pads/_area|TypeScript/screens/desks/pads]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `PassageMarks` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/pads/PassageMarks.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pads/PassageMarks.tsx) |
| Source lines | 147 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/pads/_area|TypeScript/screens/desks/pads]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/pads/PassageMarks|src/screens/desks/pads/PassageMarks.tsx]]

## Public API

- `export interface PadLink` — interface, line 9
- `export function visibleSpanRange(stage: HTMLElement, windowId: string):` — function, line 20
- `export function placeMarks(stage: HTMLElement, windows: Array<` — function, line 51
- `export function PassageMarks(` — function, line 84

## Internal implementation anchors

- `const host = stage.querySelector(`[$` — const, line 21
- `const frame = host.getBoundingClientRect()` — const, line 23
- `const spans = [...host.querySelectorAll<HTMLElement>("[data-span-id], [data-transcript-span]")]` — const, line 24
- `const inView = spans.filter((element)` — const, line 25
- `const box = element.getBoundingClientRect()` — const, line 26
- `const shown = inView.length ? inView : spans` — const, line 29
- `const id = (element: HTMLElement | undefined)` — const, line 30
- `const from = id(shown[0])` — const, line 31
- `const to = id(shown[shown.length - 1])` — const, line 32
- `interface Placed` — interface, line 36
- `function quoted(value: string): string` — function, line 46
- `const origin = stage.getBoundingClientRect()` — const, line 52
- `const out: Placed[] = []` — const, line 53
- `const host = stage.querySelector(`[$` — const, line 55
- `const frame = host.getBoundingClientRect()` — const, line 57
- `const at = (spanId: string)` — const, line 58
- `const element = host.querySelector(`[data-span-id="$` — const, line 59
- `const box = element.getBoundingClientRect()` — const, line 61
- `const place = at(link.spanId)` — const, line 67
- `const anchor = question.anchor as` — const, line 71
- `const place = at(anchor.span_id)` — const, line 73
- `function sameMarks(a: Placed[], b: Placed[]): boolean` — function, line 80
- `const windowsKey = windows.map((each)` — const, line 95
- `let frame = 0` — let, line 98
- `const update = ()` — const, line 99
- `const next = placeMarks(stage, windows, links, carried)` — const, line 101
- `const schedule = ()` — const, line 105
- `const timer = setInterval(schedule, 1000)` — const, line 111

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `PadLink`, `PassageMarks`, `visibleSpanRange`; references `PadLink`, `PassageMarks`, `visibleSpanRange`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CarriedQuestionDto`
- [[Reference/Desktop/TypeScript/screens/desks/keys/listeners|src/screens/desks/keys/listeners.ts]] — import-or-re-export; imports `WINDOW_ATTRIBUTE`

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

1. Modify [apps/learnloop-tauri/src/screens/desks/pads/PassageMarks.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pads/PassageMarks.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
