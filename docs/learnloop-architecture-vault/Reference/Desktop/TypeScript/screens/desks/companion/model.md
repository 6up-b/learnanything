---
title: "Desktop module · src/screens/desks/companion/model.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.companion.model"
language: "TypeScript"
area: "TypeScript/screens/desks/companion"
source_path: "apps/learnloop-tauri/src/screens/desks/companion/model.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/companion/model.ts"
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

# `src/screens/desks/companion/model.ts`

Area: [[Reference/Desktop/TypeScript/screens/desks/companion/_area|TypeScript/screens/desks/companion]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `COMPANION_SIZES`, `DOCKS`, `dockRect`, `anchoredRect` and related exports within the desktop's TypeScript/screens/desks/companion ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/companion/model.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/companion/model.ts) |
| Source lines | 150 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/companion/_area|TypeScript/screens/desks/companion]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/companion/model|src/screens/desks/companion/model.ts]]

## Public API

- `export const COMPANION_SIZES =` — const, line 8
- `export const DOCKS: readonly CompanionDock[] = ["br", "bl", "right", "cb"]` — const, line 33
- `export function dockRect(dock: CompanionDock, stage: Stage): Rect` — function, line 35
- `export function anchoredRect(anchor: Rect, stage: Stage): Rect` — function, line 50
- `export function nearestDock(point:` — function, line 61
- `export function pillRect(stage: Stage): Rect` — function, line 75
- `export function intersects(a: Rect, b: Rect): boolean` — function, line 84
- `export function avoidOffset(panel: Rect, obstacles: Rect[], stage: Stage): number` — function, line 91
- `export type CompanionMode = "docked" | "hidden" | "anchored"` — type, line 105
- `export interface CompanionState` — interface, line 107
- `export const HIDDEN: CompanionState =` — const, line 119
- `export type CompanionEvent = /** `c` (or `alt+c` while typing), with where it would anchor. */ |` — type, line 121
- `export function companionStep(state: CompanionState, event: CompanionEvent): CompanionState` — function, line 130

## Internal implementation anchors

- `const w = Math.min(COMPANION_SIZES.rightWidth, stage.width * COMPANION_SIZES.rightShare)` — const, line 38
- `const w = Math.min(COMPANION_SIZES.width, Math.max(0, stage.width - 2 * inset))` — const, line 41
- `const h = Math.round(stage.height * COMPANION_SIZES.dockShare)` — const, line 42
- `const y = stage.height - h - inset` — const, line 43
- `const w = Math.min(stage.width < COMPANION_SIZES.narrowBelow ? COMPANION_SIZES.narrowWidth : COMPANION_SIZES.width, stage.width - 16)` — const, line 51
- `const h = Math.min(COMPANION_SIZES.anchoredHeight, Math.round(stage.height * COMPANION_SIZES.anchoredShare))` — const, line 52
- `const below = anchor.y + anchor.h + COMPANION_SIZES.anchorGap` — const, line 53
- `const above = anchor.y - COMPANION_SIZES.anchorGap - h` — const, line 54
- `const y = below + h <= stage.height - 8 ? below : above >= 8 ? above : stage.height - h - 8` — const, line 55
- `const x = Math.max(8, Math.min(anchor.x, stage.width - w - 8))` — const, line 56
- `let best: CompanionDock = "br"` — let, line 62
- `let distance = Infinity` — let, line 63
- `const r = dockRect(dock, stage)` — const, line 65
- `const d = Math.hypot(r.x + r.w / 2 - point.x, r.y + r.h / 2 - point.y)` — const, line 66
- `const covered = obstacles.filter((rect)` — const, line 92
- `const left = Math.min(...covered.map((rect)` — const, line 94
- `const right = Math.max(...covered.map((rect)` — const, line 95
- `const toLeft = left - COMPANION_SIZES.avoidMargin - (panel.x + panel.w)` — const, line 96
- `const toRight = right + COMPANION_SIZES.avoidMargin - panel.x` — const, line 97
- `const fits = (dx: number)` — const, line 98
- `const options = [toLeft, toRight].filter(fits).sort((a, b)` — const, line 99

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `CompanionEvent`, `CompanionState`, `HIDDEN`, `avoidOffset`, `companionStep`; references `CompanionEvent`, `CompanionState`, `HIDDEN`, `avoidOffset`, `companionStep`
- [[Reference/Desktop/TypeScript/screens/desks/companion/Companion|src/screens/desks/companion/Companion.tsx]] — import-or-re-export: `CompanionState`, `dockRect`, `nearestDock`, `pillRect`; references `CompanionState`, `dockRect`, `nearestDock`, `pillRect`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CompanionDock`
- [[Reference/Desktop/TypeScript/screens/desks/geometry|src/screens/desks/geometry.ts]] — import-or-re-export; imports `Rect`, `Stage`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/companion/model.test.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/companion/model.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/companion/model.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/companion/model.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
