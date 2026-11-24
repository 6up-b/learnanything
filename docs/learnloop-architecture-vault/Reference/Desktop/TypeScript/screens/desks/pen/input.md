---
title: "Desktop module · src/screens/desks/pen/input.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.pen.input"
language: "TypeScript"
area: "TypeScript/screens/desks/pen"
source_path: "apps/learnloop-tauri/src/screens/desks/pen/input.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/pen/input.ts"
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

# `src/screens/desks/pen/input.ts`

Area: [[Reference/Desktop/TypeScript/screens/desks/pen/_area|TypeScript/screens/desks/pen]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `PointerLike`, `Sample`, `FinishedStroke`, `DownOutcome` and related exports within the desktop's TypeScript/screens/desks/pen ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/pen/input.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pen/input.ts) |
| Source lines | 122 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/pen/_area|TypeScript/screens/desks/pen]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/pads/PadStackWindow|src/screens/desks/pads/PadStackWindow.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/pen/InkLine|src/screens/desks/pen/InkLine.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/pen/input|src/screens/desks/pen/input.ts]]

## Public API

- `export interface PointerLike` — interface, line 13
- `export interface Sample` — interface, line 27
- `export interface FinishedStroke` — interface, line 36
- `export type DownOutcome = /** Not ours: the event goes on as it would without pen mode (touch scrolls, the mouse selects). */ |` — type, line 41
- `export class PenInput` — class, line 58

## Internal implementation anchors

- `const MOUSE_PRESSURE = 0.5` — const, line 50
- `const BARREL_BUTTONS = new Set([2, 5])` — const, line 51
- `const ERASER_BITS = 32` — const, line 52
- `function clamp(value: number, low: number, high: number): number` — function, line 54
- `const pen = event.pointerType === "pen"` — const, line 74
- `const mouse = event.pointerType === "mouse" && this.simulate()` — const, line 75
- `const turnOn = pen && !penOn` — const, line 78
- `const erase = BARREL_BUTTONS.has(event.button) || (event.buttons & ERASER_BITS) !== 0` — const, line 79
- `const events = event.getCoalescedEvents?.() ?? []` — const, line 89
- `const samples = (events.length ? events : [event]).map((each)` — const, line 90
- `const done = this.active` — const, line 98
- `const start = this.active?.start ?? event.timeStamp` — const, line 110
- `const reported = Number.isFinite(event.pressure) ? event.pressure : 0` — const, line 111
- `const pressure = event.pointerType === "mouse" && reported === 0 ? MOUSE_PRESSURE : clamp(reported, 0, 1)` — const, line 112

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/pen/InkLine|src/screens/desks/pen/InkLine.tsx]] — import-or-re-export: `PenInput`, `PointerLike`, `Sample`; references `PenInput`, `PointerLike`, `Sample`
- [[Reference/Desktop/TypeScript/screens/desks/pen/PenLayer|src/screens/desks/pen/PenLayer.tsx]] — import-or-re-export: `PenInput`, `PointerLike`, `Sample`; references `PenInput`, `PointerLike`, `Sample`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/pen/input.test.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pen/input.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/pen/input.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/pen/input.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
