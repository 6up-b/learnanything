---
title: "Desktop module · src/screens/desks/keys/listeners.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.keys.listeners"
language: "TypeScript"
area: "TypeScript/screens/desks/keys"
source_path: "apps/learnloop-tauri/src/screens/desks/keys/listeners.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/keys/listeners.ts"
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

# `src/screens/desks/keys/listeners.ts`

Area: [[Reference/Desktop/TypeScript/screens/desks/keys/_area|TypeScript/screens/desks/keys]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `RouterHooks`, `WINDOW_ATTRIBUTE`, `windowOfTarget`, `DeskListenerRouter` within the desktop's TypeScript/screens/desks/keys ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/keys/listeners.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/keys/listeners.ts) |
| Source lines | 134 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/keys/_area|TypeScript/screens/desks/keys]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/keys/listeners|src/screens/desks/keys/listeners.ts]]

## Public API

- `export interface RouterHooks` — interface, line 32
- `export const WINDOW_ATTRIBUTE = "data-desk-window"` — const, line 43
- `export function windowOfTarget(target: EventTarget | null): string | null` — function, line 46
- `export class DeskListenerRouter` — class, line 51

## Internal implementation anchors

- `const INPUT_TYPES = new Set([ "keydown", "keyup", "keypress", "mousedown", "mouseup", "mousemove", "click", "dblclick", "contextmenu", "pointerdown", "pointerup", "pointermove", "pointercancel", "touchstart", "touchmove", "touchend", "copy", "cut", "paste", "…` — const, line 14
- `const POINTER_PRESS = new Set(["mousedown", "pointerdown", "touchstart"])` — const, line 22
- `interface Subscription` — interface, line 24
- `const capture = typeof options === "boolean" ? options : Boolean(options?.capture)` — const, line 62
- `const subscription: Subscription =` — const, line 63
- `const key = `$` — const, line 95
- `const node: EventTarget = target === "window" ? window : document` — const, line 97
- `const listener = (event: Event)` — const, line 98
- `const input = INPUT_TYPES.has(type)` — const, line 104
- `const pressed = windowOfTarget(event.target)` — const, line 106
- `const active = this.pressedWindow && POINTER_PRESS.has(type) ? this.pressedWindow : this.hooks.activeWindowId()` — const, line 111
- `let stopped = false` — let, line 112
- `const original = event.stopImmediatePropagation.bind(event)` — const, line 113

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `DeskListenerRouter`, `WINDOW_ATTRIBUTE`, `windowOfTarget`; references `DeskListenerRouter`, `WINDOW_ATTRIBUTE`, `windowOfTarget`
- [[Reference/Desktop/TypeScript/screens/desks/goal/GoalLayer|src/screens/desks/goal/GoalLayer.tsx]] — import-or-re-export: `WINDOW_ATTRIBUTE`; references `WINDOW_ATTRIBUTE`
- [[Reference/Desktop/TypeScript/screens/desks/menu/model|src/screens/desks/menu/model.ts]] — import-or-re-export: `WINDOW_ATTRIBUTE`; references `WINDOW_ATTRIBUTE`
- [[Reference/Desktop/TypeScript/screens/desks/pads/PassageMarks|src/screens/desks/pads/PassageMarks.tsx]] — import-or-re-export: `WINDOW_ATTRIBUTE`; references `WINDOW_ATTRIBUTE`
- [[Reference/Desktop/TypeScript/screens/desks/selection|src/screens/desks/selection.ts]] — import-or-re-export: `WINDOW_ATTRIBUTE`; references `WINDOW_ATTRIBUTE`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/screens/desks/lifecycle|src/screens/desks/lifecycle.tsx]] — import-or-re-export; imports `ListenTarget`, `ListenerHub`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/keys/listeners.test.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/keys/listeners.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/keys/listeners.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/keys/listeners.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
